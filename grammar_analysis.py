import json

# 读取单词类别表和tokens文件
def read_word_category(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def read_tokens(file_path):
    tokens = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip() == "$":
                tokens.append(("$", "$"))
                continue
            parts = line.strip('<>\n').split(', ', 1)
            token_type = int(parts[0])
            token_value = parts[1].strip('"')
            tokens.append((token_type, token_value))
    return tokens

# Token类型编码
word_category_file = 'word_category.json'
tokens_file = './output/tokens.txt'

word_category = read_word_category(word_category_file)
tokens = read_tokens(tokens_file)

# 解析器类定义
class Parser:
    def __init__(self, tokens, word_category, result_file):
        self.tokens = tokens
        self.word_category = word_category
        self.position = 0
        self.errors = []
        self.result_file = result_file
        with open(self.result_file, 'w', encoding='utf-8') as file:
            file.write("<试卷> ")

    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def advance(self):
        self.position += 1

    def match(self, expected_type):
        current = self.current_token()
        if current and current[0] == expected_type:
            self.write_to_result(current)
            self.advance()
            return True
        return False

    def write_to_result(self, token):
        with open(self.result_file, 'a', encoding='utf-8') as file:
            file.write(f"<{token[0]}, \"{token[1]}\"> ")

    def parse_option(self):
        expected_option = "A"
        while self.current_token() and self.current_token()[0] == self.word_category["OPTION"]:
            current_token = self.current_token()
            option_value = current_token[1]
            if not option_value.startswith(expected_option + "、"):
                self.errors.append(f"Error at token {self.position}: Expected option {expected_option}, got {current_token}")
                self.skip_to_next_question_or_type()
                return False
            if option_value == expected_option + "、":
                self.errors.append(f"Error at token {self.position}: Option {expected_option} content is empty")
                self.skip_to_next_question_or_type()
                return False
            expected_option = chr(ord(expected_option) + 1)
            self.write_to_result(current_token)
            self.advance()
        return True

    def parse_question(self):
        if not self.match(self.word_category["DIFFICULTY"]):
            self.errors.append(f"Error at token {self.position}: Expected DIFFICULTY, Unexpected token {self.current_token()}")
            self.skip_to_next_question_or_type()
            return False
        if not self.match(self.word_category["SCORE"]):
            self.errors.append(f"Error at token {self.position}: Expected SCORE, Unexpected token {self.current_token()}")
            self.skip_to_next_question_or_type()
            return False
        if not self.match(self.word_category["CONTENT"]):
            self.errors.append(f"Error at token {self.position}: Expected CONTENT, Unexpected token {self.current_token()}")
            self.skip_to_next_question_or_type()
            return False
        self.parse_option()
        return True

    def parse_question_block(self):
        while self.position < len(self.tokens):
            if not self.parse_question():
                continue
            if self.current_token() and self.current_token()[0] in [self.word_category["TYPE"], "$"]:
                break

    def parse_question_type_block(self):
        if not self.match(self.word_category["TYPE"]):
            self.errors.append(f"Error at token {self.position}: Expected TYPE, Unexpected token {self.current_token()}")
            return False
        if not self.match(self.word_category["COUNT"]):
            self.errors.append(f"Error at token {self.position}: Expected COUNT, Unexpected token {self.current_token()}")
            return False
        if not self.match(self.word_category["TOTAL SCORE"]):
            self.errors.append(f"Error at token {self.position}: Expected TOTAL SCORE, Unexpected token {self.current_token()}")
            return False
        self.parse_question_block()
        return True

    def skip_to_next_question_or_type(self):
        while self.current_token() and self.current_token()[0] not in [self.word_category["DIFFICULTY"], "$"]:
            self.advance()

    def parse(self):
        while self.position < len(self.tokens):
            if self.current_token() and self.current_token()[0] == "$":
                break
            if not self.parse_question_type_block():
                self.skip_to_next_question_or_type()
        if self.current_token() and self.current_token()[0] == "$":
            self.advance()
        return not self.errors

# 主解析器入口
def main():
    tokens = read_tokens("./output/tokens.txt")
    word_category = read_word_category("word_category.json")
    result_file = "./output/parsed_tokens.txt"
    parser = Parser(tokens, word_category, result_file)
    if parser.parse():
        print("grammar analysis success")
    else:
        print("grammar analysis failed")
        for error in parser.errors:
            print(error)

main()
