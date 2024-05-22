"""
词法分析程序
对于输入的试卷进行词法分析
报错内容：难度等级，题目类型
"""
import re

# 正则表达式预定义
section_header_pattern = r'第\w部分\s+(.*?)(\(\d+题，共\d+分\))'
question_pattern = r'\d+、\（(.*?)\）(.*?)\（(\d+)分\）'
option_pattern = r'\s*([A-D])、\s*(.*)'

# 有效的难度和题型
valid_difficulties = {"简单", "中等", "困难"}
valid_types = {"单选题", "多选题", "判断题", "简答题"}

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

            section_match = re.match(r'第\w+部分\s+(.*?)\((\d+)题，共(\d+)分\)', line)
            if section_match:
                section_type = section_match.group(1).strip()
                count = section_match.group(2).strip()
                total_score = section_match.group(3).strip()
                if section_type not in valid_types:
                    raise ValueError(f"词法分析错误：无效的题型 '{section_type}' 在第 {line_number} 行")
                current_section = {
                    "type": section_type,
                    "count": count,
                    "total_score": total_score,
                    "questions": []
                }
                questions.append(current_section)
                continue

            question_match = re.match(question_pattern, line)
            if question_match:
                difficulty = question_match.group(1).strip()
                if difficulty not in valid_difficulties:
                    raise ValueError(f"词法分析错误：无效的难度 '{difficulty}' 在第 {line_number} 行")
                current_question = {
                    "difficulty": difficulty,
                    "content": question_match.group(2).strip(),
                    "score": question_match.group(3).strip(),
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
            tokens.append((4, question["difficulty"]))
            tokens.append((5, question["score"]))
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

print("词法分析完成并保存到文件。")
