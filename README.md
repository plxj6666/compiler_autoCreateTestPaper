# compiler_autoCreateTestPaper
武汉大学2024年春季编译原理课程设计（试题匹配及自动构建试题库)

- Author:Xiang_pl

文件列表：
1. main.py: 主程序，将三个分析程序综合并可视化。
2. lexical_analysis.py: 词法分析程序，将输入的试卷转化为token序列。
3. grammar_analysis.py: 语法分析程序，对tokens进行语法分析。
4. semantic_analysis.py: 语义分析程序，进行语义分析。
5. create_test_paper.py: 从题库抽取试题生成试卷。
6. word_category.json: 词法分析的词性表。
7. output/QuestionBank.txt: 题库。
8. output/tokens.txt: 词法分析结果。
9. /src/example.txt: 输入的试卷。