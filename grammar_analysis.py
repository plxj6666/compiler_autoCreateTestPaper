import json
import re

# 读取 token 文件
def read_tokens_from_file(filename):
    tokens = []
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            match = re.match(r'<(\d+),\s*"([^"]*)">', line)
            if match:
                token_type = int(match.group(1))
                value = match.group(2)
                tokens.append((token_type, value))
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

# 解析器类
class Parser:
    def __init__(self, tokens, word_category):
        self.tokens = tokens
        self.word_category = word_category
        self.index = 0
        self.line_number = 1

    def current_token(self):
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None

    def match(self, expected_type):
        token = self.current_token()
        if token and token[0] == expected_type:
            self.index += 1
            self.line_number += 1
            return token
        expected_name = get_word_category_name(self.word_category, expected_type)
        raise ValueError(f"语法错误: Unexpected token {token}, expected '{expected_name}' at line {self.line_number}")

    def parse_exam(self):
        self.match(self.word_category["TYPE"])
        self.match(self.word_category["COUNT"])
        self.match(self.word_category["TOTAL SCORE"])
        self.parse_question_list()

    def parse_question_list(self):
        while self.current_token() and self.current_token()[0] == self.word_category["DIFFICULTY"]:
            self.parse_question()

    def parse_question(self):
        self.match(self.word_category["DIFFICULTY"])
        self.match(self.word_category["SCORE"])
        self.match(self.word_category["CONTENT"])
        self.parse_options_or_empty()

    def parse_options_or_empty(self):
        while self.current_token() and self.current_token()[0] == self.word_category["OPTION"]:
            self.match(self.word_category["OPTION"])

# 示例用法
tokens_filename = "./output/tokens.txt"
word_category_filename = "word_category.json"

tokens = read_tokens_from_file(tokens_filename)
word_category = read_word_category(word_category_filename)

parser = Parser(tokens, word_category)
try:
    parser.parse_exam()
    print("语法分析完成，无错误")
except ValueError as e:
    print(f"语法错误: {e}")
