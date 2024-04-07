from bs4 import BeautifulSoup
from openai import OpenAI
from tqdm import tqdm
import google.generativeai as genai
import httpx
import re
import os
import glob

ai_switch = 1 # (0:gpt, 1:genmini)

contents_path = "./contents/"
ai_addr = ""
ai_api_key = ""
google_ai_addr=""
google_ai_api_key=""
pre_prompts = "你是一个文学大师，小说家。我将提供一段文本给你，请你理解这段文本，\
                并结合上下文以及合理的想象，保持文本原有主题意思的情况下, \
                以小说的风格，并加入适当的润色和合理的环境，心理或动作描写，改写这段话，\
                如果上下文不连贯或有缺失，可以适当添加一些语句，甚至可以调整上下文的顺序， \
                使得整个文段更加合理，更加流畅充实，\
                最终达到词句，语言表达等与原文尽量不同，但是意思与原文大致相同的目的，\
                但是内容更加充实优美的文字语句，修改后的字数不能少于原文字数，\
                尽量使用与原文同一个意思，但是不同的词句用语来表述，\
                不要额外添加没有意义的符号, \
                除非原文是英文，否则必须使用中文回答:"
# ai_max_length =4096 - len(pre_prompts) - 100
ai_max_length = 1000
temperature = 0.5

if len(ai_addr) == 0 or len(ai_api_key) == 0:
    # read config.ini file
    with open('config.ini', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith('ai_addr'):
                ai_addr = line.split('=')[1].strip()
            elif line.startswith('ai_api_key'):
                ai_api_key = line.split('=')[1].strip()
            elif line.startswith('google_ai_addr'):
                google_ai_addr = line.split('=')[1].strip()
            elif line.startswith('google_ai_api_key'):
                google_ai_api_key = line.split('=')[1].strip()

def get_latest_file_name(directory):
    """
    Get the name of the latest HTML file in a directory.
    """
    list_of_files = glob.glob(directory + '/*.html')  # get list of all HTML files
    if not list_of_files:  # No HTML files found
        return None
    latest_file = max(list_of_files, key=os.path.getctime)  # get the latest file
    base_name = os.path.basename(latest_file)  # get the file name
    file_name, _ = os.path.splitext(base_name)  # remove the extension
    return file_name

def write_text_to_file(text, file_path):
    with open(file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(text)
    print(f"Extraction completed, saved to: {file_path}")

def split_text_into_chunks(text, max_length=ai_max_length):
    """
    Split text into chunks with a maximum length, ensuring that splits only occur at line breaks.
    """
    lines = text.splitlines()
    chunks = []
    current_chunk = ''
    for line in lines:
        if len(current_chunk + ' ' + line) <= max_length:
            current_chunk += ' ' + line
        else:
            chunks.append(current_chunk)
            current_chunk = line
    chunks.append(current_chunk)
    return chunks

def rewrite_text_with_genai(text, prompt="Please rewrite this text:"):
    chunks = split_text_into_chunks(text)
    rewritten_text = ''
    current_model = 'gemini-pro'
    pbar = tqdm(total=len(chunks), ncols=150)
    genai.configure(api_key = google_ai_api_key)
    model = genai.GenerativeModel(current_model)
    error_text = []
    for chunk in chunks:
        _prompt=f"{prompt}\n{chunk}",
        response = model.generate_content(
            contents=_prompt, 
            generation_config=genai.GenerationConfig(
                temperature=temperature,
            ),
            stream=True,
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_DANGEROUS",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]
        )
        for _chunk in response:
            if _chunk.text is not None:
                rewritten_text += _chunk.text.strip()
            else:
                error_text.append(_chunk)
        pbar.update(1)
    pbar.close()
    for _chunk in error_text:
        print(_chunk)
    return rewritten_text

def rewrite_text_with_gpt3(text, prompt="Please rewrite this text:"):
    chunks = split_text_into_chunks(text)
    rewritten_text = ''
    error_text = []
    client = OpenAI(
        base_url=ai_addr, 
        api_key=ai_api_key,
        http_client=httpx.Client(
            base_url=ai_addr,
            follow_redirects=True,
        ),
    )
    pbar = tqdm(total=len(chunks), ncols=150)
    for chunk in chunks:
        response = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4",
            messages=[
                {
                "role": "system",
                "content": prompt
                },
                {
                "role": "user",
                "content": chunk
                }
            ],
            temperature=temperature,
            max_tokens=4096,
            stream=True,
        )
        # rewritten_text += response.choices[0].message.content.strip()
        for _chunk in response:
            if _chunk.choices[0].delta.content is not None:
                rewritten_text += _chunk.choices[0].delta.content.strip()
            else:
                error_text.append(_chunk)
        pbar.update(1)
    pbar.close()
    for _chunk in error_text:
        print(_chunk)
    return rewritten_text

def remove_chapter_markers(text):
    """
    Remove all chapter markers from a string.
    """
    chinese_numbers = r'零一二三四五六七八九十百千万亿'
    arabic_numbers = r'0123456789'
    chapter_marker_regex = re.compile(f'第[{chinese_numbers}{arabic_numbers}]+章')
    return chapter_marker_regex.sub('', text)

def replace_punctuation_with_space(text):
    """
    Replace all punctuation marks (except newline characters) with a space.
    """
    chinese_punctuation = r'[。，、；：？！“”‘’《》（）【】]'
    english_punctuation = r'[.,;:?!""''<>()[\]{}]'
    text = re.sub(chinese_punctuation, ' ', text)
    text = re.sub(english_punctuation, ' ', text)
    return text

def merge_short_lines(text):
    """
    Merge lines with less than 5 characters to the previous or next line based on their length.
    """
    lines = text.split('\n')
    merged_lines = []
    i = 0
    while i < len(lines):
        if len(lines[i]) < 10:
            if i > 0 and i < len(lines) - 1:
                if len(lines[i-1]) < len(lines[i+1]):
                    merged_lines[-1] += lines[i]
                else:
                    lines[i+1] = lines[i] + lines[i+1]
            elif i > 0:  # This is the last line
                merged_lines[-1] += lines[i]
            elif i < len(lines) - 1:  # This is the first line
                lines[i+1] = lines[i] + lines[i+1]
        else:
            merged_lines.append(lines[i])
        i += 1
    return '\n'.join(merged_lines)

# Enhanced functionality to split long lines and remove lines with only numbers or symbols
def split_long_lines(text):
    """
    Split lines exceeding 30 characters at the next punctuation mark.
    Only split if both parts have more than 12 characters.
    """
    punctuation_marks = ('，', '。', '？', '！', '……', '：')
    new_text = []
    for line in text.split('\n'):
        while len(line) > 30:
            split_point = -1
            for mark in punctuation_marks:
                split_at = line.find(mark, 30)
                if split_at != -1 and split_at > 12 and len(line) - split_at - 1 > 12:
                    split_point = split_at + 1
                    break
            if split_point == -1:  # No punctuation mark found within the limit
                new_text.append(line)
                line = ""
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

def merge_lines_without_punctuation(text):
    """
    Process text by merging lines without punctuation while keeping normal line breaks for those with punctuation.
    Only split if both parts have more than 12 characters.
    """
    lines = text.split('\n')
    merged_lines = []
    current_line = ""

    chinese_chars_and_punctuation = re.compile(r'[\u4e00-\u9fa5。，、；：？！“”‘’《》（）【】]')

    for line in lines:
        line = line.rstrip()
        if chinese_chars_and_punctuation.search(line) and not line.endswith(tuple('。，、；：？！“”‘’《》（）【】')):
            if len(current_line) > 12 and len(line) > 12:
                merged_lines.append(current_line)
                current_line = line
            else:
                current_line += line
        else:
            if current_line:
                merged_lines.append(current_line + line)
                current_line = ""
            else:
                merged_lines.append(line)

    if current_line:
        merged_lines.append(current_line)

    return '\n'.join(merged_lines)



def insert_new_lines_with_condition(text):
    """
    Insert new lines after specified punctuation marks only if they are not
    already at the end of a line.
    """
    def replace_func(match):
        punctuation, quote = match.groups()
        # If punctuation is at the end of the text or followed by a newline, don't add another newline
        if match.end() == len(text) or text[match.end()] == '\n':
            return punctuation + (quote if quote else '')
        else:
            return punctuation + (quote if quote else '') + '\n'

    pattern = re.compile(r'([。！？])(”?)')
    new_text = pattern.sub(replace_func, text)
    return new_text

def extract_chinese_and_punctuation_from_html(html_file_path):
    base_name = os.path.splitext(html_file_path)[0]
    ori__file_path = base_name + '.txt'
    
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    chinese_punctuation_regex = re.compile(r'[\u4e00-\u9fff，。？！；：、“”《》（）\u0030-\u0039\uFF10-\uFF19]+')

    extracted_texts = []
    for element in soup.find_all(string=True):
        if element.parent.name not in ['script', 'style']:
            matches = chinese_punctuation_regex.findall(element)
            if matches:
                extracted_texts.append(''.join(matches))

    output_text = ""
    for text in extracted_texts:
        output_text += text + '\n'
    output_text = remove_chapter_markers(output_text)
    output_text = merge_lines_without_punctuation(output_text)
    output_text = insert_new_lines_with_condition(output_text)
    output_text = split_long_lines(output_text)
    output_text = remove_lines_with_only_numbers_or_symbols(output_text)
    output_text = merge_short_lines(output_text)
    output_text = replace_punctuation_with_space(output_text)
    write_text_to_file(output_text, ori__file_path)
    # with open(output_file_path, 'w', encoding='utf-8') as output_file:
    #     output_file.write(output_text)

    # print(f"Extraction completed, saved to: {output_file_path}")

# Main program

content_name = get_latest_file_name(contents_path)
input_name = input("Enter the content name (default: " + content_name + "): ")
if len(input_name) > 0:
    content_name = input_name
print("Current content is: " + content_name)

choice = input("1: pre process html file: \n2: process txt file with gpt: \n")
if choice == '1':
    html_file_path = contents_path + content_name + '.html'
    if(not os.path.exists(html_file_path)):
        print("File not found: " + html_file_path)
        exit()
    extract_chinese_and_punctuation_from_html(html_file_path)
elif choice == '2':
    base_name = contents_path + content_name
    ori__file_path = base_name + '.txt'
    if(not os.path.exists(ori__file_path)):
        print("File not found: " + ori__file_path)
        exit()
    ai_choice = input("Current AI is: " + ("GPT" if ai_switch == 0 else "GenMini") + "\nDo you want to switch AI? (y/n): ")
    if ai_choice == 'y':
        ai_switch = 1 - ai_switch
        print("AI switched to: " + ("GPT" if ai_switch == 0 else "GenMini"))
    # base_name = os.path.splitext(html_file_path)[0]   
    if ai_switch == 0:
        mod_file_path = base_name + '_gpt.txt'
    elif ai_switch == 1:
        mod_file_path = base_name + '_gen.txt'
    # read mod file to get the text
    output_text = ""
    with open(ori__file_path, 'r', encoding='utf-8') as file:
        output_text = file.read()
    # output_text = output_text.replace('\n', '')
    output_text = remove_chapter_markers(output_text)
    if ai_switch == 0:
        output_text = rewrite_text_with_gpt3(output_text, pre_prompts)
    elif ai_switch == 1:
        output_text = rewrite_text_with_genai(output_text, pre_prompts)
    output_text = merge_lines_without_punctuation(output_text)
    output_text = insert_new_lines_with_condition(output_text)
    output_text = split_long_lines(output_text)
    output_text = remove_lines_with_only_numbers_or_symbols(output_text)
    output_text = merge_short_lines(output_text)
    output_text = replace_punctuation_with_space(output_text)
    write_text_to_file(output_text, mod_file_path)

