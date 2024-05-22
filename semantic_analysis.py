import json
import re

# 读取 token 文件
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

# 读取单词类别表
def read_word_category(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

# 获取单词类别的名称
def get_word_category_name(word_category, token_type):
    for name, type_id in word_category.items():
        if type_id == token_type:
            return name
    return str(token_type)

# 语义分析器类
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


# 示例用法
tokens_filename = "./output/tokens.txt"
word_category_filename = "word_category.json"
question_bank_filename = "./output/QuestionBank.txt"

tokens = read_tokens_from_file(tokens_filename)
word_category = read_word_category(word_category_filename)

analyzer = SemanticAnalyzer(tokens, word_category)
analyzer.analyze()

if analyzer.errors:
    for error in analyzer.errors:
        print(error)
else:
    analyzer.save_to_question_bank(question_bank_filename)
    print("语义分析完成，无错误")
