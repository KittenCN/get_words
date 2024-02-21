from bs4 import BeautifulSoup
import re
import os

# Enhanced functionality to split long lines and remove lines with only numbers or symbols
def split_long_lines(text):
    """
    Split lines exceeding 25 characters at the next punctuation mark.
    """
    punctuation_marks = ('，', '。', '？', '！', '……', '：')
    new_text = []
    for line in text.split('\n'):
        while len(line) > 25:
            split_point = -1
            for mark in punctuation_marks:
                split_at = line.find(mark, 25)
                if split_at != -1:
                    split_point = split_at + 1
                    break
            if split_point == -1:  # No punctuation mark found within the limit
                new_text.append(line[:25])
                line = line[25:]
            else:
                new_text.append(line[:split_point])
                line = line[split_point:]
        if line:  # Add the remainder of the line if any
            new_text.append(line)
    return '\n'.join(new_text)

def remove_lines_with_only_numbers_or_symbols(text):
    """
    Remove lines that contain only numbers or symbols.
    """
    lines = text.split('\n')
    filtered_lines = [line for line in lines if not re.fullmatch(r'[\d\W_]+', line)]
    return '\n'.join(filtered_lines)

# 重新定义函数以包含所需的re模块导入
def merge_lines_without_punctuation(text):
    """
    处理文本，合并没有标点符号的行。
    保留有标点符号的正常换行。
    """
    lines = text.split('\n')  # 按换行符分割文本为行
    merged_lines = []  # 存储处理后的行
    current_line = ""  # 当前正在处理的行

    # 定义一个正则表达式，用于匹配中文字符及标点
    chinese_chars_and_punctuation = re.compile(r'[\u4e00-\u9fa5。，、；：？！“”‘’《》（）【】]')

    for line in lines:
        # 移除行尾空格
        line = line.rstrip()
        # 检查当前行是否以中文标点结束
        if chinese_chars_and_punctuation.search(line) and not line.endswith(tuple('。，、；：？！“”‘’《》（）【】')):
            # 如果当前行不以中文标点结束，尝试与下一行合并
            current_line += line
        else:
            # 如果当前行以中文标点结束，将其（和之前可能合并的行）添加到结果中
            if current_line:
                # 添加之前合并的行和当前行
                merged_lines.append(current_line + line)
                current_line = ""  # 重置当前行
            else:
                # 直接添加当前行
                merged_lines.append(line)

    # 确保最后的行也被添加
    if current_line:
        merged_lines.append(current_line)

    return '\n'.join(merged_lines)

def extract_chinese_and_punctuation_from_html(html_file_path):
    # 确定输出的txt文件路径
    base_name = os.path.splitext(html_file_path)[0]
    output_file_path = base_name + '.txt'
    
    # 从.html文件中读取内容
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 定义正则表达式匹配中文字符及常见的中文标点
    chinese_punctuation_regex = re.compile(r'[\u4e00-\u9fff，。？！；：、“”《》（）\u0030-\u0039\uFF10-\uFF19]+')

    # 提取中文及标点的文本
    extracted_texts = []
    for element in soup.find_all(text=True):
        if element.parent.name not in ['script', 'style']:  # 忽略JavaScript和CSS内容
            matches = chinese_punctuation_regex.findall(element)
            if matches:
                extracted_texts.append(''.join(matches))

    output_text = ""
    for text in extracted_texts:
        output_text += text + '\n'
    output_text = merge_lines_without_punctuation(output_text)

    # Apply new functionalities to process the text further
    output_text = split_long_lines(output_text)
    output_text = remove_lines_with_only_numbers_or_symbols(output_text)

    # 将提取的文本保存到同名的txt文件中
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(output_text)

    print(f"提取完成，已保存至：{output_file_path}")

# 指定你的HTML文件路径
html_file_path = '离婚后，前妻她后悔了.html'

# 调用函数
extract_chinese_and_punctuation_from_html(html_file_path)
