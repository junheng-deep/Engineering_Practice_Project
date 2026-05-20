import re
from bs4 import BeautifulSoup

def parse_grade_table(html):
    """解析成绩HTML"""
    soup = BeautifulSoup(html, 'html.parser')

    # 1. 解析成绩列表
    table = soup.find('table', id=re.compile(r'grid\d+'))
    courses = []

    if table and table.find('tbody'):
        for row in table.find('tbody').find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 11:
                # 提取课程名称（去除sup标签，如体育5的篮球标注）
                name_cell = cols[3]
                for sup in name_cell.find_all('sup'):
                    sup.decompose()
                course_name = name_cell.get_text(strip=True)

                courses.append({
                    'semester': cols[0].get_text(strip=True),
                    'course_code': cols[1].get_text(strip=True),
                    'course_seq': cols[2].get_text(strip=True),
                    'course_name': course_name,
                    'category': cols[4].get_text(strip=True),
                    'credit': cols[5].get_text(strip=True),
                    'regular_score': cols[6].get_text(strip=True),
                    'final_score': cols[7].get_text(strip=True),
                    'total_score': cols[8].get_text(strip=True),
                    'final_grade': cols[9].get_text(strip=True),
                    'gpa': cols[10].get_text(strip=True)
                })

    # 2. 计算统计数据
    stats = calculate_stats(courses)

    return {
        'courses': courses,
        'stats': stats
    }

def calculate_stats(courses):
    """计算成绩统计数据"""
    if not courses:
        return {}

    total_credits = 0
    weighted_gpa = 0
    total_score_sum = 0
    score_count = 0

    category_stats = {}

    for course in courses:
        try:
            credit = float(course['credit'])
            gpa = float(course['gpa'])
            total_score = float(course['total_score'])

            total_credits += credit
            weighted_gpa += credit * gpa
            total_score_sum += total_score
            score_count += 1

            # 按课程类别统计
            category = course['category']
            if category not in category_stats:
                category_stats[category] = {
                    'courses': 0,
                    'total_credits': 0,
                    'total_gpa': 0,
                    'total_score': 0
                }
            category_stats[category]['courses'] += 1
            category_stats[category]['total_credits'] += credit
            category_stats[category]['total_gpa'] += credit * gpa
            category_stats[category]['total_score'] += total_score

        except (ValueError, TypeError):
            continue

    # 计算平均绩点和平均分
    avg_gpa = round(weighted_gpa / total_credits, 2) if total_credits > 0 else 0
    avg_score = round(total_score_sum / score_count, 1) if score_count > 0 else 0

    # 计算各类别平均绩点
    for category in category_stats:
        cat = category_stats[category]
        cat['avg_gpa'] = round(cat['total_gpa'] / cat['total_credits'], 2) if cat['total_credits'] > 0 else 0
        cat['avg_score'] = round(cat['total_score'] / cat['courses'], 1) if cat['courses'] > 0 else 0

    return {
        'total_courses': len(courses),
        'total_credits': total_credits,
        'avg_gpa': avg_gpa,
        'avg_score': avg_score,
        'category_stats': category_stats
    }


# 测试
if __name__ == "__main__":
    with open('grade_table.html', 'r', encoding='utf-8') as f:
        html = f.read()

    result = parse_grade_table(html)

    print(f"课程数量: {len(result['courses'])}")
    print(f"总学分: {result['stats']['total_credits']}")
    print(f"平均绩点: {result['stats']['avg_gpa']}")
    print(f"平均分: {result['stats']['avg_score']}")

    print("\n成绩明细:")
    print("-" * 95)
    for c in result['courses']:
        print(f"{c['course_name']:<24} | 学分: {c['credit']:>4} | 平时: {c['regular_score']:>3} | 期末: {c['final_score']:>3} | 总评: {c['total_score']:>3} | 绩点: {c['gpa']}")

    print("\n按类别统计:")
    print("-" * 55)
    for cat, data in result['stats']['category_stats'].items():
        print(f"{cat:<12} | 课程数: {data['courses']:>2} | 学分: {data['total_credits']:>5} | 平均绩点: {data['avg_gpa']}")