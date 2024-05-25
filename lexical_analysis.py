import re

# 正则表达式预定义
section_header_pattern = r'第\w部分\s+(.*?)(\(\d+题，共\d+分\))'
# 更新后的题干内容匹配正则表达式
difficulty_pattern = re.compile(r'（(?P<difficulty>[^）]*)）')
content_pattern = re.compile(r'^\d+、(?:（[^）]*）)?(?P<content>.*?)(?:（\d+分）|$)')
score_pattern = re.compile(r'（(?P<score>\d+)分）')
option_pattern = r'\s*([A-D])、\s*(.*)'

# 有效的难度和题型
valid_difficulties = {"简单", "中等", "困难"}
valid_types = {"单选题", "多选题", "判断题", "简答题"}
errors = []


def parse_questions(filename):
    questions = []
    current_section = None
    current_question = None
    line_number = 0

    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line_number += 1
            line = line.strip()
            if not line:
                continue

            section_match = re.match(section_header_pattern, line)
            if section_match:
                section_type = section_match.group(1).strip()
                count_score_match = re.findall(r'\d+', section_match.group(2))
                count = count_score_match[0]
                total_score = count_score_match[1]
                if section_type not in valid_types:
                    errors.append(f"词法分析错误：无效的题型 '{section_type}' 在第 {line_number} 行")
                    # raise ValueError(f"词法分析错误：无效的题型 '{section_type}' 在第 {line_number} 行")
                current_section = {
                    "type": section_type,
                    "count": count,
                    "total_score": total_score,
                    "questions": []
                }
                questions.append(current_section)
                continue

            difficulty_match = difficulty_pattern.search(line)
            score_match = score_pattern.search(line)
            content_match = content_pattern.search(line)

            if content_match:
                difficulty = difficulty_match.group('difficulty') if difficulty_match else None
                score = score_match.group('score') if score_match else None
                content = content_match.group('content').strip() if content_match.group('content') else None

                # 检查是否难度值为有效值
                if difficulty and difficulty not in valid_difficulties:
                    errors.append(f"词法分析错误：无效的难度 '{difficulty}' 在第 {line_number} 行")
                    # difficulty = None

                current_question = {
                    "difficulty": difficulty,
                    "content": content,
                    "score": score,
                    "options": []
                }
                current_section["questions"].append(current_question)
                continue

            option_match = re.match(option_pattern, line)
            if option_match and current_question:
                current_question["options"].append(option_match.group(1) + '、' + option_match.group(2))

    return questions

def generate_tokens(questions):
    tokens = []
    for section in questions:
        tokens.append((1, section["type"]))
        tokens.append((2, section["count"]))
        tokens.append((3, section["total_score"]))
        for question in section["questions"]:
            if question["difficulty"]:
                tokens.append((4, question["difficulty"]))
            if question["score"]:
                tokens.append((5, question["score"]))
            if question["content"]:
                tokens.append((6, question["content"]))
            for option in question["options"]:
                tokens.append((7, option))
    return tokens

# Example usage
filename = r"./src/examples.txt"
questions = parse_questions(filename)
tokens = generate_tokens(questions)

with open('./output/tokens.txt', 'w', encoding='utf-8') as f:
    for token in tokens:
        f.write(f"<{token[0]}, \"{token[1]}\">\n")
    f.write("$")
print("词法分析完成并保存到文件。")
if errors:
    for error in errors:
        print(error)