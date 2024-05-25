import re

# 定义正则表达式
difficulty_pattern = r'（(?P<difficulty>[^）]*)）'
content_pattern = r'1、(?:（[^）]*）)?(?P<content>.*?)（(?:\d+分）?|$)'
score_pattern = r'（(?P<score>\d+)分）'

# 测试样例
texts = [
    "1、（中等）ICT项目台账应包含项目基本情况、预立项项目效益评估内容、（）、合同、入账情况。（2分）",
    "1、ICT项目台账应包含项目基本情况、预立项项目效益评估内容、（）、合同、入账情况。（2分）",
    "1、（中等）（2分）",
    "1、（中等）ICT项目台账应包含项目基本情况、预立项项目效益评估内容、（）、合同、入账情况。"
]

for text in texts:
    # 匹配难度
    difficulty_match = re.search(difficulty_pattern, text)
    if difficulty_match and difficulty_match.group('difficulty').strip():
        print(f"<4, \"{difficulty_match.group('difficulty').strip()}\">")

    # 匹配分数
    score_match = re.search(score_pattern, text)
    if score_match and score_match.group('score').strip():
        print(f"<5, \"{score_match.group('score').strip()}\">")

    # 匹配内容
    content_match = re.search(content_pattern, text)
    if content_match and content_match.group('content').strip():
        print(f"<6, \"{content_match.group('content').strip()}\">")
