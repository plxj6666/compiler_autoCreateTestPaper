import tkinter as tk
from tkinter import scrolledtext
import re
import json

def read_tokens_from_file(filename):
    tokens = []
    line_number = 1
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            match = re.match(r'<(\d+),\s*"([^"]*)">', line)
            if match:
                token_type = int(match.group(1))
                value = match.group(2)
                tokens.append((token_type, value, line_number))
            line_number += 1
    return tokens

# 词法分析函数
def lexical_analysis(filename):
    section_header_pattern = r'第\w部分\s+(.*?)(\(\d+题，共\d+分\))'
    difficulty_pattern = re.compile(r'（(?P<difficulty>[^）]*)）')
    content_score_pattern = re.compile(r'^\d+、(?:（[^）]*）)?(?P<content>.*?)(?:（(?P<score>\d+)分）|$)')
    option_pattern = r'\s*([A-D])、\s*(.*)'

    valid_difficulties = {"简单", "中等", "困难"}
    valid_types = {"单选题", "多选题", "判断题", "简答题"}
    errors = []

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
                current_section = {
                    "type": section_type,
                    "count": count,
                    "total_score": total_score,
                    "questions": []
                }
                questions.append(current_section)
                continue

            content_score_match = content_score_pattern.search(line)
            if content_score_match:
                content = content_score_match.group('content').strip() if content_score_match.group('content') else None
                score = content_score_match.group('score') if content_score_match.group('score') else None

                # 检查是否有难度部分，确保不会误识别
                difficulty_match = difficulty_pattern.search(line)
                difficulty = None
                if difficulty_match:
                    potential_difficulty = difficulty_match.group('difficulty')
                    if potential_difficulty in valid_difficulties:
                        difficulty = potential_difficulty
                    if potential_difficulty and potential_difficulty not in valid_difficulties:
                        errors.append(f"词法分析错误：无效的难度 '{potential_difficulty}' 在第 {line_number} 行")
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

    return questions, generate_tokens(questions), errors

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

# 语法分析函数
def syntactical_analysis(tokens, word_category_filename):
    with open(word_category_filename, 'r', encoding='utf-8') as file:
        word_category = json.load(file)

    class Parser:
        def __init__(self, tokens, word_category):
            self.tokens = tokens
            self.word_category = word_category
            self.position = 0
            self.errors = []

        def current_token(self):
            if self.position < len(self.tokens):
                return self.tokens[self.position]
            return None

        def advance(self):
            self.position += 1

        def match(self, expected_type):
            current = self.current_token()
            if current and current[0] == expected_type:
                self.advance()
                return True
            return False

        def parse_option(self):
            expected_option = "A"
            while self.current_token() and self.current_token()[0] == self.word_category["OPTION"]:
                current_token = self.current_token()
                option_value = current_token[1]
                if not option_value.startswith(expected_option + "、"):
                    self.errors.append(f"Error at token {self.position}: Expected option {expected_option}, got {current_token}")
                    # Skip to the end of the current question
                    self.skip_to_next_question_or_type()
                    return False
                if option_value == expected_option + "、":
                    self.errors.append(f"Error at token {self.position}: Option {expected_option} content is empty")
                    # Skip to the end of the current question
                    self.skip_to_next_question_or_type()
                    return False
                expected_option = chr(ord(expected_option) + 1)
                self.advance()
            return True

        def parse_question(self):
            if not self.match(word_category["DIFFICULTY"]):
                self.errors.append(f"Error at token {self.position}: Expected DIFFICULTY, Unexpected token {self.current_token()}")
                # Skip to the end of the current question
                self.skip_to_next_question_or_type()
                return False
            if not self.match(word_category["SCORE"]):
                self.errors.append(f"Error at token {self.position}: Expected SCORE, Unexpected token {self.current_token()}")
                # Skip to the end of the current question
                self.skip_to_next_question_or_type()
                return False
            if not self.match(word_category["CONTENT"]):
                self.errors.append(f"Error at token {self.position}: Expected CONTENT, Unexpected token {self.current_token()}")
                # Skip to the end of the current question
                self.skip_to_next_question_or_type()
                return False
            self.parse_option()
            return True

        def parse_question_block(self):
            while self.position < len(self.tokens):
                if not self.parse_question():
                    # If error, skip to the next question or question type
                    continue
                # If next token is a new question type or end of tokens, break the loop
                if self.current_token() and self.current_token()[0] in [word_category["TYPE"], "$"]:
                    break

        def parse_question_type_block(self):
            if not self.match(word_category["TYPE"]):
                self.errors.append(f"Error at token {self.position}: Expected TYPE, Unexpected token {self.current_token()}")
                return False
            if not self.match(word_category["COUNT"]):
                self.errors.append(f"Error at token {self.position}: Expected COUNT, Unexpected token {self.current_token()}")
                return False
            if not self.match(word_category["TOTAL SCORE"]):
                self.errors.append(f"Error at token {self.position}: Expected TOTAL SCORE, Unexpected token {self.current_token()}")
                return False
            self.parse_question_block()
            return True

        def skip_to_next_question_or_type(self):
            # Skip tokens until we find the next question type or the end of the tokens
            while self.current_token() and self.current_token()[0] not in [word_category["DIFFICULTY"], "$"]:
                self.advance()

        def parse(self):
            while self.position < len(self.tokens):
                if self.current_token() and self.current_token()[0] == "$":
                    break
                if not self.parse_question_type_block():
                    # Skip to the next question type or end of tokens
                    self.skip_to_next_question_or_type()
            # Ensure we end parsing correctly if we reach the end
            if self.current_token() and self.current_token()[0] == "$":
                self.advance()
            return not self.errors

    def get_word_category_name(word_category, token_type):
        for name, type_id in word_category.items():
            if type_id == token_type:
                return name
        return str(token_type)

    parser = Parser(tokens, word_category)
    if parser.parse():
        return "语法分析完成，无错误", parser.errors
    else:
        return "语法分析完成，但存在错误", parser.errors

# 语义分析函数
def semantic_analysis(tokens, word_category_filename):
    with open(word_category_filename, 'r', encoding='utf-8') as file:
        word_category = json.load(file)

    class SemanticAnalyzer:
        def __init__(self, tokens, word_category):
            self.tokens = tokens
            self.word_category = word_category
            self.index = 0
            self.current_type = None
            self.expected_count = 0
            self.expected_total_score = 0
            self.actual_count = 0
            self.actual_total_score = 0
            self.questions = []
            self.difficulty_score_map = {
                "简单": None,
                "中等": None,
                "困难": None
            }
            self.errors = []

        def current_token(self):
            if self.index < len(self.tokens):
                return self.tokens[self.index]
            return None

        def match(self, expected_type):
            token = self.current_token()
            if token and token[0] == expected_type:
                self.index += 1
                return token
            expected_name = get_word_category_name(self.word_category, expected_type)
            self.errors.append(f"语法错误: Unexpected token {token}, expected '{expected_name}' at line {token[2]}")
            self.index += 1  # Skip this token and continue
            return None

        def analyze(self):
            while self.current_token():
                self.current_type = self.match(self.word_category["TYPE"])[1]
                self.expected_count = int(self.match(self.word_category["COUNT"])[1])
                self.expected_total_score = int(self.match(self.word_category["TOTAL SCORE"])[1])
                self.actual_count = 0
                self.actual_total_score = 0
                self.difficulty_score_map = {
                    "简单": None,
                    "中等": None,
                    "困难": None
                }
                self.analyze_question_list()

                # 验证题目数量和总分数
                if self.actual_count != self.expected_count:
                    current_token = self.current_token()
                    self.errors.append(f"语义错误: 预期题目数量 {self.expected_count}, 但实际数量为 {self.actual_count} at line {current_token[2] if current_token else 'EOF'}")
                if self.actual_total_score != self.expected_total_score:
                    current_token = self.current_token()
                    self.errors.append(f"语义错误: 预期总分数 {self.expected_total_score}, 但实际分数为 {self.actual_total_score} at line {current_token[2] if current_token else 'EOF'}")

        def analyze_question_list(self):
            while self.current_token() and self.current_token()[0] == self.word_category["DIFFICULTY"]:
                self.analyze_question()

        def analyze_question(self):
            difficulty_token = self.match(self.word_category["DIFFICULTY"])
            score_token = self.match(self.word_category["SCORE"])
            content_token = self.match(self.word_category["CONTENT"])
            if not difficulty_token or not score_token or not content_token:
                return
            score = int(score_token[1])
            difficulty = difficulty_token[1]

            # 设置难度和分数的映射
            if self.difficulty_score_map[difficulty] is None:
                self.difficulty_score_map[difficulty] = score
            elif self.difficulty_score_map[difficulty] != score:
                self.errors.append(f"语义错误: 难度 '{difficulty}' 的题目分数应为 {self.difficulty_score_map[difficulty]}，但实际分数为 {score} at line {score_token[2]}")

            # 检查分数是否满足简单 < 中等 < 困难
            if (self.difficulty_score_map["简单"] is not None and
                self.difficulty_score_map["中等"] is not None and
                self.difficulty_score_map["困难"] is not None):
                if not (self.difficulty_score_map["简单"] < self.difficulty_score_map["中等"] < self.difficulty_score_map["困难"]):
                    self.errors.append(f"语义错误: 题目分数不满足 简单 < 中等 < 困难 的要求 at line {score_token[2]}")

            self.actual_total_score += score
            self.actual_count += 1
            options = self.analyze_options_or_empty()

            question = (self.current_type, difficulty, f"{score}分", content_token[1]) + tuple(options)
            self.questions.append(question)

        def analyze_options_or_empty(self):
            options = []
            has_options = False
            while self.current_token() and self.current_token()[0] == self.word_category["OPTION"]:
                option_token = self.match(self.word_category["OPTION"])
                if option_token:
                    options.append(option_token[1])
                    has_options = True

            # 验证题目类型是否正确包含或不包含选项
            token = self.current_token()
            if self.current_type in ["单选题", "多选题"] and not has_options:
                self.errors.append(f"语义错误: 题目类型 '{self.current_type}' 应该包含选项，但没有找到选项 at line {token[2] if token else 'EOF'}")
            if self.current_type in ["判断题", "简答题"] and has_options:
                self.errors.append(f"语义错误: 题目类型 '{self.current_type}' 不应该包含选项，但找到了选项 at line {token[2] if token else 'EOF'}")
            return options

        def save_to_question_bank(self, filename):
            with open(filename, 'w', encoding='utf-8') as file:
                for question in self.questions:
                    file.write(str(question) + '\n')

    def get_word_category_name(word_category, token_type):
        for name, type_id in word_category.items():
            if type_id == token_type:
                return name
        return str(token_type)

    analyzer = SemanticAnalyzer(tokens, word_category)
    analyzer.analyze()

    if analyzer.errors:
        return "语义分析完成，但存在错误", analyzer.errors

    analyzer.save_to_question_bank("./output/QuestionBank.txt")
    return "语义分析完成，无错误", analyzer.errors

# GUI 部分
def run_lexical_analysis():
    txt_display.delete(1.0, tk.END)
    filename = "./src/examples.txt"
    try:
        txt_display.delete(1.0, tk.END)
        questions, tokens, lex_errors = lexical_analysis(filename)
        txt_display.insert(tk.END, "词法分析结果：\n")
        for token in tokens:
            txt_display.insert(tk.END, f"<{token[0]}, \"{token[1]}\">\n")
        with open('./output/tokens.txt', 'w', encoding='utf-8') as f:
            for token in tokens:
                f.write(f"<{token[0]}, \"{token[1]}\">\n")
        if lex_errors:
            txt_display.insert(tk.END, "\n词法分析错误：\n" + "\n".join(lex_errors) + "\n")
    except Exception as e:
        txt_display.insert(tk.END, f"词法分析异常：{str(e)}\n")
    btn_syntax.config(state="normal")

def run_syntactical_analysis():
    tokens_filename = "./output/tokens.txt"
    word_category_filename = "word_category.json"
    try:
        txt_display.delete(1.0, tk.END)
        tokens = read_tokens_from_file(tokens_filename)
        result, syn_errors = syntactical_analysis(tokens, word_category_filename)
        txt_display.insert(tk.END, "\n语法分析结果：\n" + result + "\n")
        if syn_errors:
            txt_display.insert(tk.END, "\n语法分析错误：\n" + "\n".join(syn_errors) + "\n")
    except Exception as e:
        txt_display.insert(tk.END, f"语法分析异常：{str(e)}\n")
    btn_semantic.config(state="normal")

def run_semantic_analysis():
    tokens_filename = "./output/tokens.txt"
    word_category_filename = "word_category.json"
    try:
        txt_display.delete(1.0, tk.END)
        tokens = read_tokens_from_file(tokens_filename)
        result, sem_errors = semantic_analysis(tokens, word_category_filename)
        txt_display.insert(tk.END, "\n语义分析结果：\n" + result + "\n")
        if sem_errors:
            txt_display.insert(tk.END, "\n语义分析错误：\n" + "\n".join(sem_errors) + "\n")
    except Exception as e:
        txt_display.insert(tk.END, f"语义分析异常：{str(e)}\n")

# 设置主窗口
window = tk.Tk()
window.title("分析工具")

# 文本区域用于显示输出和错误
txt_display = scrolledtext.ScrolledText(window, width=80, height=20)
txt_display.grid(row=0, column=0, columnspan=3, pady=10, padx=10)

# 控制工作流的按钮
btn_lexical = tk.Button(window, text="运行词法分析", command=run_lexical_analysis)
btn_lexical.grid(row=1, column=0, padx=10, pady=10)

btn_syntax = tk.Button(window, text="运行语法分析", state="disabled", command=run_syntactical_analysis)
btn_syntax.grid(row=1, column=1, padx=10, pady=10)

btn_semantic = tk.Button(window, text="运行语义分析", state="disabled", command=run_semantic_analysis)
btn_semantic.grid(row=1, column=2, padx=10, pady=10)

window.mainloop()
