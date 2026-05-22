import os
from typing import Optional, List, Dict
from datetime import datetime, date
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

# 导入已有的解析模块
from campus_crawler.crawler.parse_course_table import parse_course_table
from campus_crawler.crawler.parse_grade_table import parse_grade_table

load_dotenv()

# ==================== 学期配置 ====================
# 从环境变量读取学期开始日期，格式 YYYY-MM-DD，默认 2025-09-01
SEMESTER_START_STR = os.getenv("SEMESTER_START_DATE", "2026-03-04")
SEMESTER_START = datetime.strptime(SEMESTER_START_STR, "%Y-%m-%d").date()

def get_current_week(reference_date: Optional[date] = None) -> int:
    """
    计算当前日期是学期第几周。
    规则：周一为一周的开始，学期开始日期所在周为第1周。
    如果 reference_date 为 None，则使用今天的日期。
    """
    if reference_date is None:
        reference_date = date.today()
    # 计算天数差，然后除以7取整，加1得到周数
    days_diff = (reference_date - SEMESTER_START).days
    if days_diff < 0:
        return 0   # 学期尚未开始
    week_num = days_diff // 7 + 1
    return week_num

# ==================== 加载并预处理数据 ====================
with open('course_table.html', 'r', encoding='utf-8') as f:
    html = f.read()
course_result = parse_course_table(html)

grade_result = parse_grade_table('grade_table.html')

course_list = course_result['courses']
schedule_raw = course_result['schedule']

weekday_map = {'周一':0, '周二':1, '周三':2, '周四':3, '周五':4, '周六':5, '周日':6}
period_names = [f'第{i+1}节' for i in range(12)]
schedule_matrix = [[None for _ in range(12)] for _ in range(7)]
for item in schedule_raw:
    day = weekday_map[item['day']]
    period = item['section'] - 1
    if 0 <= period < 12:
        schedule_matrix[day][period] = {
            'course_name': item['course_name'],
            'course_code': item['course_code_full'].split('(')[0] if '(' in item['course_code_full'] else item['course_code_full'],
            'teacher': '',
            'classroom': item['room'],
            'weeks_binary': item['weeks_binary'],
            'weeks_text': item['weeks_text']
        }

teacher_map = {c['name']: c['teacher'] for c in course_list}
for day in range(7):
    for period in range(12):
        if schedule_matrix[day][period]:
            course_name = schedule_matrix[day][period]['course_name']
            schedule_matrix[day][period]['teacher'] = teacher_map.get(course_name, '未知教师')

grade_stats = grade_result['stats']
grade_courses = grade_result['courses']


# ==================== 加载上课时间表 ====================
CAMPUS = os.getenv("CAMPUS", "航空港校区")  # 可通过环境变量指定校区，默认航空港校区

def parse_time_table(file_path: str) -> Dict[str, List[tuple]]:
    """
    解析 time.txt，返回校区到时间段的映射。
    结构：{校区: [(start_time, end_time), ...], 索引0对应第1节}
    """
    import re
    campus_times = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 第一行：节次航空港校区龙泉校区 -> 提取校区名称
    header = lines[0].strip()
    # 简单分割：去掉“节次”，剩下的按空格拆分
    parts = header.split()
    # parts[0] 是 "节次"，后面依次是校区名（可能含空格？这里假设单空格分隔）
    campus_names = [p for p in parts[1:] if p]  # 如 ['航空港校区', '龙泉校区']
    if not campus_names:
        # 备用硬编码
        campus_names = ['航空港校区', '龙泉校区']
    
    # 初始化每个校区的时间列表，索引0-11对应第1-12节
    for name in campus_names:
        campus_times[name] = [None] * 12
    
    # 正则匹配：第X节... 例如 "第1节08:20-09:05 08:30-09:15"
    pattern = re.compile(r'第(\d+)节(\d{2}:\d{2}-\d{2}:\d{2})\s+(\d{2}:\d{2}-\d{2}:\d{2})')
    
    for line in lines:
        m = pattern.search(line)
        if m:
            period_idx = int(m.group(1)) - 1  # 转为0索引
            if 0 <= period_idx < 12:
                # 第一个时间段对应第一个校区，第二个时间段对应第二个校区
                time1 = m.group(2)
                time2 = m.group(3)
                for i, name in enumerate(campus_names):
                    time_str = time1 if i == 0 else time2
                    start_str, end_str = time_str.split('-')
                    start_time = datetime.strptime(start_str, '%H:%M').time()
                    end_time = datetime.strptime(end_str, '%H:%M').time()
                    campus_times[name][period_idx] = (start_time, end_time)
    return campus_times

# 加载时间表
time_table = parse_time_table('time.txt')
if CAMPUS not in time_table:
    print(f"警告：环境变量 CAMPUS={CAMPUS} 不在时间表中，将使用航空港校区时间。")
    CAMPUS = '航空港校区'
period_times = time_table[CAMPUS]  # 当前校区的时间段列表

# ==================== 工具函数 ====================
@tool
def query_schedule(weekday: str, period: Optional[str] = None, week: Optional[int] = None, campus: Optional[str] = None) -> str:
    """
    查询课表。自动根据当前日期判断教学周，只显示本周有课的课程。
    参数:
        weekday: 星期几，例如 '周一' 或 '星期一'。
        period: 可选，节次如 '第一节'，或 '全天'。默认 '全天'。
        week: 可选，指定查询第几周（整数）。若不提供则自动使用当前周次。
        campus: 可选，校区名称（'航空港校区' 或 '龙泉校区'），不传则使用环境变量配置的校区。
    """
    # 星期标准化
    wk_map = {
        '周一': '周一', '周二': '周二', '周三': '周三', '周四': '周四', '周五': '周五', '周六': '周六', '周日': '周日',
        '星期一': '周一', '星期二': '周二', '星期三': '周三', '星期四': '周四', '星期五': '周五', '星期六': '周六', '星期日': '周日'
    }
    weekday_std = wk_map.get(weekday, weekday)
    if weekday_std not in weekday_map:
        return f"无法识别星期：{weekday}，请使用'周一'至'周日'或'星期一'至'星期日'。"
    day_idx = weekday_map[weekday_std]

    # 确定周次
    target_week = week if week is not None else get_current_week()
    if target_week <= 0:
        return f"当前日期 {date.today()} 早于学期开始日期 {SEMESTER_START}，无法查询课表。"

    # 确定校区和时间表
    use_campus = campus if campus and campus in time_table else CAMPUS
    times = time_table.get(use_campus, time_table.get('航空港校区'))
    if not times:
        times = [None] * 12

    # 辅助函数：根据 weeks_text 判断本周是否有课
    def is_week_in_course(weeks_text: str, week_num: int) -> bool:
        if not weeks_text:
            return False
        parts = weeks_text.strip().split('-')
        if len(parts) == 1:
            try:
                return int(parts[0]) == week_num
            except:
                return False
        elif len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return start <= week_num <= end
            except:
                return False
        else:
            # 降级：尝试使用二进制（如果存在），但优先用文本
            return False

    if period is None or period == '全天':
        lines = [f"{weekday_std}全天课程（第{target_week}周，{use_campus}时间）："]
        has_any = False
        for p_idx, p_name in enumerate(period_names):
            act = schedule_matrix[day_idx][p_idx]
            time_str = ""
            if times and p_idx < len(times) and times[p_idx]:
                start, end = times[p_idx]
                time_str = f"（{start.strftime('%H:%M')}-{end.strftime('%H:%M')}）"
            if act:
                # 使用文本周次判断
                if is_week_in_course(act['weeks_text'], target_week):
                    has_any = True
                    lines.append(f"{p_name}{time_str}：{act['course_name']}（{act['teacher']}）@{act['classroom']}，周次：{act['weeks_text']}（本周有课）")
                else:
                    lines.append(f"{p_name}{time_str}：{act['course_name']}（{act['teacher']}）@{act['classroom']}，但本周无课（课程周次：{act['weeks_text']}）")
            else:
                lines.append(f"{p_name}{time_str}：无课")
        if not has_any:
            lines.append("（本周该日无任何课程安排）")
        return "\n".join(lines)
    else:
        if period not in period_names:
            return f"无法识别节次：{period}，请使用'第一节'至'第十二节'。"
        p_idx = period_names.index(period)
        act = schedule_matrix[day_idx][p_idx]
        time_str = ""
        if times and p_idx < len(times) and times[p_idx]:
            start, end = times[p_idx]
            time_str = f"（{start.strftime('%H:%M')}-{end.strftime('%H:%M')}）"
        if act:
            if is_week_in_course(act['weeks_text'], target_week):
                return f"{weekday_std}{period}{time_str}（第{target_week}周）：{act['course_name']}（{act['teacher']}）@{act['classroom']}，周次：{act['weeks_text']}（本周有课）"
            else:
                return f"{weekday_std}{period}{time_str} 原计划有 {act['course_name']}，但本周无课（课程周次：{act['weeks_text']}）"
        else:
            return f"{weekday_std}{period}{time_str}没有课程安排。"

@tool
def query_grades(course_name: Optional[str] = None, show_stats: bool = False) -> str:
    """查询成绩（保持原有实现不变）"""
    if not grade_courses:
        return "成绩数据未加载，请检查 grade_table.html 文件。"
    if course_name:
        matches = [g for g in grade_courses if course_name in g['course_name']]
        if not matches:
            return f"未找到包含'{course_name}'的课程。"
        return "\n".join(
            f"{g['course_name']}（{g['course_code']}）：总评 {g['total_score']}，绩点 {g['gpa']}"
            for g in matches
        )
    else:
        if show_stats:
            stats = grade_stats
            return (f"成绩统计：\n"
                    f"总课程数：{stats.get('total_courses', 0)}\n"
                    f"总学分：{stats.get('total_credits', 0)}\n"
                    f"平均绩点：{stats.get('avg_gpa', 0)}\n"
                    f"平均分：{stats.get('avg_score', 0)}\n"
                    f"分类详情：\n" +
                    "\n".join(f"  {cat}：{data['courses']}门课，学分 {data['total_credits']}，平均绩点 {data['avg_gpa']}"
                              for cat, data in stats.get('category_stats', {}).items()))
        else:
            lines = ["所有课程成绩："]
            for g in grade_courses:
                lines.append(f"{g['course_name']}：{g['total_score']} 分，绩点 {g['gpa']}")
            return "\n".join(lines)

@tool
def query_course_list() -> str:
    """列出本学期所有课程（含学分、教师）"""
    if not course_list:
        return "课程列表未加载，请检查 course_table.html 文件。"
    lines = ["本学期课程列表："]
    for c in course_list:
        lines.append(f"{c['name']}（{c['code']}），学分 {c['credit']}，教师 {c['teacher']}")
    return "\n".join(lines)
@tool
def query_current_week() -> str:
    """查询当前是学期第几周。"""
    week_num = get_current_week()
    if week_num <= 0:
        return f"当前日期 {date.today()} 早于学期开始日期 {SEMESTER_START}，学期尚未开始。"
    return f"当前是学期第 {week_num} 周（学期开始日期：{SEMESTER_START}）。"
@tool
def query_current_time() -> str:
    """返回当前日期、时间、星期和学期周次。"""
    now = datetime.now()
    weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()]
    week_num = get_current_week()
    return f"现在是 {now.strftime('%Y年%m月%d日 %H:%M:%S')}，{weekday_cn}，学期第 {week_num} 周。"


@tool
def query_current_course(campus: Optional[str] = None) -> str:
    """
    根据当前时间，判断现在正在上什么课，或者下一节课是什么。
    参数 campus: 可选，校区名称（航空港校区/龙泉校区），不传则使用环境变量配置的校区。
    """
    # 确定校区
    use_campus = campus if campus and campus in time_table else CAMPUS
    times = time_table[use_campus]
    
    now = datetime.now()
    current_weekday = now.weekday()  # 周一=0，周日=6
    # 转换为我们的 weekday_map 索引（周一=0）
    # datetime 的 Monday=0 正好对应我们的周一=0，周日=6 也对应周日=6
    day_idx = current_weekday  # 0=周一, 6=周日
    current_time = now.time()
    current_week = get_current_week()
    
    if current_week <= 0:
        return f"当前日期 {now.date()} 早于学期开始日期 {SEMESTER_START}，学期尚未开始，无法查询实时课程。"
    
    # 辅助：判断某课程在当周是否有课
    def has_course_in_week(weeks_binary: str, week_num: int) -> bool:
        if week_num < 1 or week_num > len(weeks_binary):
            return False
        return weeks_binary[week_num - 1] == '1'
    
    # 寻找当前时间所属的节次（哪个时间段包含当前时间）
    current_period = None
    for i, (start, end) in enumerate(times):
        if start <= current_time <= end:
            current_period = i
            break
    
    # 如果没找到，寻找下一节（下一个开始时间大于当前时间的最小节次）
    next_period = None
    if current_period is None:
        for i, (start, end) in enumerate(times):
            if start > current_time:
                next_period = i
                break
    
    period_names = [f'第{i+1}节' for i in range(12)]
    
    # 当前正在上课
    if current_period is not None:
        act = schedule_matrix[day_idx][current_period] if day_idx < len(schedule_matrix) else None
        period_name = period_names[current_period]
        start_time, end_time = times[current_period]
        if act and has_course_in_week(act['weeks_binary'], current_week):
            return (f"当前时间 {current_time.strftime('%H:%M')}，{period_name}（{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}）\n"
                    f"正在上：{act['course_name']}（{act['teacher']}）@{act['classroom']}，第{current_week}周有课。")
        else:
            return (f"当前时间 {current_time.strftime('%H:%M')}，{period_name}（{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}）\n"
                    f"该时间段无课程安排（或本周无课）。")
    
    # 下一节课
    elif next_period is not None:
        act = schedule_matrix[day_idx][next_period] if day_idx < len(schedule_matrix) else None
        period_name = period_names[next_period]
        start_time, end_time = times[next_period]
        if act and has_course_in_week(act['weeks_binary'], current_week):
            time_diff = (datetime.combine(now.date(), start_time) - now).seconds // 60
            return (f"当前时间 {current_time.strftime('%H:%M')}，下一节课是 {period_name}（{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}），"
                    f"距离上课还有 {time_diff} 分钟。\n课程：{act['course_name']}（{act['teacher']}）@{act['classroom']}，第{current_week}周有课。")
        else:
            return (f"当前时间 {current_time.strftime('%H:%M')}，下一节 {period_name} 无课程安排。")
    else:
        return f"当前时间 {current_time.strftime('%H:%M')} 已超过当天所有节次时间，今天没有更多课程了。"



tools = [query_schedule, query_grades, query_course_list, query_current_week,query_current_course,query_current_time]
tools_by_name = {tool.name: tool for tool in tools}




# ==================== LangGraph Agent ====================
llm = ChatOpenAI(
    model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
    openai_api_base=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
    temperature=0
).bind_tools(tools)

SYSTEM_PROMPT = """你是一个校园信息查询助手，可以帮助学生查询课表、成绩和课程信息。
注意：系统已根据当前日期自动判断教学周（第几周）。查询课表时，只显示本周有课的课程，严格按照课表，课程只有第几周到第几周有课，其余时间无课。
工具：
- query_schedule(weekday, period=None, week=None): 查询指定天/节次的课表。
- query_grades(course_name, show_stats): 查询成绩。
- query_course_list(): 列出所有课程。
- query_current_week(): 查询当前是学期第几周。
- query_current_course(campus=None): 根据当前时间，判断现在正在上什么课或下一节是什么课。campus可选'航空港校区'或'龙泉校区'。
- query_current_week(): 查询当前时间。
请根据用户问题选择合适的工具。如果用户询问“现在上什么课”、“当前有什么课”、“下一节是什么”等，请调用 query_current_course()。
"""

def agent_node(state: MessagesState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: MessagesState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

def tools_node(state: MessagesState) -> dict:
    last = state["messages"][-1]
    tool_msgs = []
    for tc in last.tool_calls:
        tool = tools_by_name[tc["name"]]
        result = tool.invoke(tc["args"])
        tool_msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    return {"messages": tool_msgs}

builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tools_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")
graph = builder.compile()

# ==================== 交互循环 ====================
def chat():
    history = []
    print("校园信息查询助手已启动。输入问题（或'退出'结束）")
    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ["退出", "exit", "quit"]:
            print("再见！")
            break
        result = graph.invoke({"messages": history + [HumanMessage(content=user_input)]})
        history = result["messages"]
        for msg in reversed(history):
            if isinstance(msg, AIMessage) and msg.content:
                print(f"助手: {msg.content}")
                break

if __name__ == "__main__":
    chat()