import re
from bs4 import BeautifulSoup

def parse_course_table(html):
    """解析课表HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. 解析课程列表
    table = soup.find('table', id=re.compile(r'grid\d+'))
    courses = []
    
    if table and table.find('tbody'):
        for row in table.find('tbody').find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 7:
                courses.append({
                    'seq': cols[0].text.strip(),
                    'code': cols[1].text.strip(),
                    'name': cols[2].text.strip(),
                    'credit': cols[3].text.strip(),
                    'class_id': cols[4].text.strip(),
                    'class_name': cols[5].text.strip(),
                    'teacher': cols[6].text.strip()
                })
    
    # 2. 解析JS中的时间地点
    js_data = extract_js_schedule(soup)
    
    return {
        'courses': courses,
        'schedule': js_data
    }

def extract_js_schedule(soup):
    """从JavaScript提取详细安排（含时间、教室、周次）"""
    scripts = soup.find_all('script')
    schedule = []
    
    for script in scripts:
        text = script.string or ''
        
        # 找所有 activity 定义
        activities = []
        for match in re.finditer(r'activity = new TaskActivity\((.*?)\);', text, re.DOTALL):
            params = re.findall(r'"([^"]*)"', match.group(1))
            if len(params) >= 5:
                activities.append({
                    'course_code_full': params[0],
                    'course_name': params[1],
                    'hours': params[2],
                    'room': params[3],
                    'weeks_binary': params[4]
                })
        
        # 找所有 index 赋值的位置
        act_positions = [(m.start(), i) for i, m in enumerate(re.finditer(r'activity = new TaskActivity\((.*?)\);', text, re.DOTALL))]
        idx_positions = [(m.start(), int(m.group(1)), int(m.group(2))) for m in re.finditer(r'index\s*=\s*(\d+)\s*\*\s*unitCount\s*\+\s*(\d+)\s*;', text)]
        
        # 配对：每个 index 找最近的 activity
        for idx_pos, day, section in idx_positions:
            closest_act = None
            closest_dist = float('inf')
            
            for act_pos, act_idx in act_positions:
                dist = idx_pos - act_pos
                if 0 <= dist < closest_dist:
                    closest_dist = dist
                    closest_act = act_idx
            
            if closest_act is not None and closest_act < len(activities):
                act = activities[closest_act]
                day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                
                schedule.append({
                    'course_code_full': act['course_code_full'],
                    'course_name': act['course_name'],
                    'hours': act['hours'],
                    'room': act['room'],
                    'weeks_binary': act['weeks_binary'],
                    'day': day_names[day % 7],
                    'section': section + 1,
                    'weeks_text': parse_weeks(act['weeks_binary'])
                })
    
    return schedule

def parse_weeks(weeks_binary):
    """将周次二进制转为具体周数范围（从0开始）"""
    weeks = []
    for i, bit in enumerate(weeks_binary):
        if bit == '1':
            weeks.append(i)
    
    if not weeks:
        return "无"
    
    ranges = []
    start = weeks[0]
    prev = weeks[0]
    
    for w in weeks[1:]:
        if w == prev + 1:
            prev = w
        else:
            ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = w
            prev = w
    
    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(ranges)


# 测试
if __name__ == "__main__":
    with open('course_table.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    result = parse_course_table(html)
    print(f"课程数量: {len(result['courses'])}")
    for c in result['courses']:
        print(f"{c['name']} - {c['teacher']}")
    
    print(f"\n详细安排: {len(result['schedule'])} 条")
    for s in result['schedule']:
        print(f"  {s['course_name']} | {s['day']} 第{s['section']}节 | 教室: {s['room']} | 周次: {s['weeks_text']}")