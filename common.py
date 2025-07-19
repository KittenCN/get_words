from bs4 import BeautifulSoup
from openai import OpenAI
from ollama import Client
from tqdm import tqdm
from config import write_config
# from transformers import LlamaTokenizer
import google.generativeai as genai
import httpx
import glob
import os
import sqlite3
import csv
import sys
import re
import requests, json
import tiktoken
import chardet

ai_max_length = 5000
batch_size = 50
num_ctx = 8000
overlap = 10
temperature = 0.5
contents_path = "./contents/"
log_file_path = "./error.log"
drafts_path = "./drafts/"
analysis_path = "./analysis/"
ver_num = 13
enc = tiktoken.get_encoding('cl100k_base')
# chinese_llama_tokenizer = LlamaTokenizer.from_pretrained("./tokenizer-human")

parameter_list = ['ai_addr', 'ai_api_key', 'google_ai_addr', 'google_ai_api_key', 'ollama_api_addr', \
                  'ollama_api_model', 'pre_prompts', 'ai_gpt_ver', 'sutui_db_addr', 'zx_index', \
                  'cj_index', 'zx_prompts', 'cj_prompts', 'proxy_addr', 'proxy_port', '1st_prompts']
sutui_flag = 1
parameters = {
        "ai_gpt_ver" : 4,
        "ai_addr" : "",
        "ai_api_key" : "",
        "google_ai_addr":"",
        "google_ai_api_key" : "",
        "ollama_api_addr" : "",
        "ollama_api_model" : "",
        "sutui_db_addr" : "",
        "cj_prompts" : f"You are a Stable Diffusion prompt generator.\n\
目标：针对用户一次性给出的 {batch_size} 行中文句子（行号格式 1.–{batch_size}.），结合上下文逐行提取关键信息，生成英文关键词行，以便 Stable Diffusion 还原场景。\n\
输入规则: \n\
每行前缀 1.~{batch_size}. 是行号，不可作为提取内容。\n\
{batch_size} 行内容在情节上可能连续或相互呼应，可跨行推断。\n\
输出格式: \n\
按行号对应输出：1. 主体, 表情, 动作, 背景/场景, 综合修饰,\n\
只输出关键词行，不得出现解释、空行、附加文本。\n\
只输出这 {batch_size} 行关键词，不得添加任何解释、标题或空行。\n\
如果上下行重复，或者其他情况导致该行没有数据输出，依旧要严格输出行号。\n\
行号是表示该行在原文中的位置，所以不一定是从1开始，因此必须严格按照输入的行号输出，不可自行修改，重置等行为。\n\
输入的行号必须与输出的行号一一对应， 不允许有增加，减少，修改。\n\
5 个槽位一律半角逗号分隔，行尾保留逗号。\n\
关键词按画面重要度由高到低排序；缺失信息按下列规则处理。\n\
每行关键词：\n\
主体（首位，必留槽位，可留空）：1man | 1woman | 1boy | 1girl | 1old man | 1old woman | 1animal（如未注明主体，根据外貌/行为推断）。\n\
    若当前行缺乏线索，可向前后句寻找提示。 \n\
    若上下文仍无法判断，可留空：直接写 , 保持占位。\n\
    如果明确知道人物主体的名字，一定要直接输出名字的拼音， 此时针对这个主体，就不需要输出“1man | 1woman”等概述词了\n\
    允许有多个主体。\n\
表情：情绪形容词（例：smiling, angry）。无法推断可留空。\n\
动作：动词短语（例：running, reading a book）。无法推断可留空。\n\
背景/场景：地点、环境、道具。无法推断可留空。\n\
综合修饰：画风、氛围、季节天气、光照、镜头角度等。无法推断可留空。\n\
关键词按画面重要度高→低排序，半角逗号分隔，行尾保留逗号。\n\
推断规则:\n\
可跨行引用信息：如第 2 行出现人物，第 3 行延续同一人物，可复用。\n\
若某槽位缺失且上下文无解，可合理猜测或直接留空。\n\
如任何规则导致无限递归/循环推断，立即停止该槽位推断并留空。\n\
对话、心理独白、成语、谚语：先推断情境再产出关键词。\n\
不可输出任何与关键词无关的内容。\n\
思考的过程，完全不需要输出给我！\n\
每行输出完，一定要换行，就是说每行包含一个行号及其内容。 \n\
示例: \n\
用户输入：\n\
1. 暴风雨中的老船长紧握方向舵  \n\
2. 雪夜里女孩抬头望月  \n\
3. 雪夜里女孩抬头望月  \n\
…（共{batch_size}行）\n\
系统输出：\n\
1. 1old man, determined, gripping ship wheel, stormy sea deck, dramatic lighting, cinematic,  \n\
2. 1girl, hopeful, looking up, snowy night town square, soft glow, anime style,  \n\
3. \n\
…（共{batch_size}行）",
        "zx_prompts" : "",
        "pre_prompts" : "# 角色设定 \n\
你是一位杰出的中文小说家，精于语言润色与情节重组。 \n\
# 任务 \n\
仅根据我随后提供的【原文】片段： \n\
1. 理解情节与主题，不改变核心意义。   \n\
2. 以小说叙事方式重写，允许补充合理的环境、心理或动作描写，必要时可调整段落顺序，使文意连贯。   \n\
3. 文字应比原文更充实优美，且字数≥原文字数。   \n\
4. 尽量使用不同的词语与句式表达同一含义。   \n\
5. 尽量在同一行中输出适合同一个场景的内容，避免过多换行；且不同场景的内容一定不输出到同一行。   \n\
6. 禁止出现无意义符号、空行填充、字母、数字或任何与小说无关的内容。   \n\
# 输出格式 \n\
仅输出【重写后文本】本身。   \n\
**不要**包含任何解释、思考、提示、问句、系统指令或标记。   \n\
除非原文为英文，否则一律使用中文。   \n\
# 开始 \n\
请等待我提供【原文】片段，收到后立即给出【重写后文本】，不做其他回应。 \n\
",
        "zx_index" : "【系统提词】解读正向词助手（升级版）",
        "cj_index" : "【系统场景】解读场景词助手（升级版）",
        "proxy_addr" : "",
        "proxy_port" : "",
        "1st_prompts" : "你是一个小说家，擅长将原文进行润色和重写。\n\
下面我将提供原文全文，请仔细阅读并理解原文，并分析人物关系、情节发展和主题思想。\n\
然后请你暂时记住这些内容，并之后的对话中，按照我提出要求和你理解和分析的内容，做出正确的操作。\n\
以下是原文全文：",
        }
SutuiDB = {
        "text_content" : "",
        "fenjin_text" : "",
        "prompt" : "",
        "image_width" : "1024",
        "image_height" : "576",
        "sampler_name" : "DPM++ 2M Karras",
        "steps" : "30",
        "cfg_scale" : "9",
        "unknown1" : "",
        "unknown2" : "0",
        "tag" : "",
        }

def exec_sql(sql):
    if sutui_flag == 0:
        return []
    conn = sqlite3.connect(parameters['sutui_db_addr'])
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

# check the folder address, if not exist, create it
for item in [contents_path, drafts_path, analysis_path]:
    if not os.path.exists(item):
        os.makedirs(item)
if not os.path.exists('config.ini'):
    write_config()
# read config.ini file
last_ver = 0
with open('config.ini', 'rb') as file:
    raw = file.read()
    result = chardet.detect(raw)
    encoding = result['encoding'] if result['encoding'] else 'utf-8'
    lines = raw.decode(encoding).splitlines()
    for line in lines:
        for parameter in parameter_list:
            if line.startswith(parameter):
                if len(line.split('=')[1].strip()) > 0:
                    parameters[parameter] = line.split('=')[1].strip()
                last_ver += 1
                break
    if last_ver < ver_num:
        print("软件非最新版本，部分功能可能无法使用，建议重新下载最新版本！")
        print("并按照__config.ini文件的格式补充填写config.ini文件！")

# check file sutui_db_addr
if not os.path.exists(parameters['sutui_db_addr']):
    sutui_flag = 0
    print("没有找到数据库文件: " + parameters['sutui_db_addr'])
    print("部分功能可能无法使用")
else:
    if len(parameters['zx_prompts']) == 0:
        sql = "SELECT * FROM gpt_roles where name = " + parameters['zx_index']
        result = exec_sql(sql)
        if len(result) == 0:
            print("没有找到系统提词的配置信息")
        else:
            parameters['zx_prompts'] = result[0][3]  
    if len(parameters['cj_prompts']) == 0:
        sql = "SELECT * FROM gpt_roles where name = " + parameters['cj_index']
        result = exec_sql(sql)
        if len(result) == 0:
            print("没有找到系统场景的配置信息")
        else:
            parameters['cj_prompts'] = result[0][3]

# check and set system proxy
if len(parameters["proxy_addr"]) > 0 and len(parameters["proxy_port"]) > 0:
    os.environ['HTTP_PROXY'] = "http://" + parameters["proxy_addr"] + ":" + parameters["proxy_port"]
    os.environ['HTTPS_PROXY'] = "http://" + parameters["proxy_addr"] + ":" + parameters["proxy_port"]
    print("系统代理设置为: " + "http://" + parameters["proxy_addr"] + ":" + parameters["proxy_port"])

def check_ai(ai_switch):
    if ai_switch == 0:
        if len(parameters['ai_addr']) == 0 or len(parameters['ai_api_key']) == 0:
            print("AI配置信息不完整，请检查config.ini文件")
            return False
    elif ai_switch == 1:
        if len(parameters['google_ai_api_key']) == 0:
            print("AI配置信息不完整，请检查config.ini文件")
            return False
    elif ai_switch == 2:
        if len(parameters['ai_addr']) == 0 or len(parameters['ollama_api_addr']) == 0:
            print("AI配置信息不完整，请检查config.ini文件")
            return False
    return True

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
    with open(file_path, 'a', encoding='utf-8') as output_file:
        # now = datetime.now()
        # output_file.write(now.strftime('%Y%m%d%H%M%S') + "    " + text)
        for line in text.split('\n'):
            if len(line.strip()) > 0:
                output_file.write(line.strip() + '\n')
    print(f"Extraction completed, saved to: {file_path}")

def split_article(text):
    words = enc.encode(text)
    i, n = 0, len(words)
    chunks = []
    while i < n:
        chunks = words[i:i + num_ctx]
        yield enc.decode(chunks)
        i += num_ctx - 200
    return chunks

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
            # current_chunk = chinese_llama_tokenizer.tokenize(current_chunk)
            chunks.append(current_chunk)
            current_chunk = line
    # current_chunk = chinese_llama_tokenizer.tokenize(current_chunk)
    chunks.append(current_chunk)
    return chunks

def rewrite_text_with_genai(text, google_ai_api_key, prompt="Please rewrite this text:", pbar_flag=True):
    chunks = split_text_into_chunks(text)
    rewritten_text = ''
    current_model = 'gemini-pro'
    if pbar_flag:
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
        try:
            for _chunk in response:
                if _chunk.text is not None:
                    rewritten_text += _chunk.text.strip()
            if pbar_flag:
                pbar.update(1)
        except Exception as e:
            return "error"
    if pbar_flag:
        pbar.close()
    if len(error_text) > 0:
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            try:
                for _chunk in error_text:
                    log_file.write(_chunk)
            except Exception as e:
                log_file.write(str(e))
    return rewritten_text

def rewrite_text_with_gpt3(text, ai_addr, ai_api_key, ai_gpt_ver, prompt="Please rewrite this text:", pbar_flag=True):
    chunks = split_text_into_chunks(text)
    rewritten_text = ''
    error_text = []
    client = OpenAI(
        base_url=ai_addr, 
        api_key=ai_api_key,
        http_client=httpx.Client(
            base_url=ai_addr,
            follow_redirects=True,
            # proxy=parameters["proxy_addr"] + ":" + parameters["proxy_port"] if len(parameters["proxy_addr"]) and len(parameters["proxy_port"]) > 0 else None,
        ),
    )
    if pbar_flag:
        pbar = tqdm(total=len(chunks), ncols=150)
    for chunk in chunks:
        response = client.chat.completions.create(
            model="gpt-4" if ai_gpt_ver == 4 else "gpt-3.5-turbo",
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
            stream=True,
        )
        # rewritten_text += response.choices[0].message.content.strip()
        try:
            for _chunk in response:
                if len(_chunk.choices) > 0 and _chunk.choices[0].delta.content is not None:
                    rewritten_text += _chunk.choices[0].delta.content.strip()
            if pbar_flag:        
                pbar.update(1)
        except Exception as e:
            return "error"
    if pbar_flag:
        pbar.close()
    if len(error_text) > 0:
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            try:
                for _chunk in error_text:
                    log_file.write(_chunk)
            except Exception as e:
                log_file.write(str(e))
    return rewritten_text

def ollama_with_requests(ai_addr, ollama_api_model, ollama_api_addr, prompt, stream=False, options=None, output=True):
    """
    Use requests to call the Ollama API.
    """
    rewritten_text = ''
    if stream == False:
        headers = {
            'Content-Type': 'application/json',
            'x-some-header': 'some-value',
        }
        data = {
            'model': ollama_api_model,
            'prompt': prompt + " /nothing /no_thinking /no thinking",
            "stream": stream,
            'options': options if options else {
                "num_ctx": num_ctx,
                'num_gpu': -1,
            }
        }
        response = requests.post(
            f"{ai_addr}{ollama_api_addr}",
            headers=headers,
            json=data
        )
        if response.status_code == 200:
            return response.json()
    else:
        url = ai_addr + ollama_api_addr
        data = {
            'model': ollama_api_model,
            'prompt': prompt + " /nothing /no_thinking /no thinking",
            "stream": stream,
            'options': {
                "num_ctx": num_ctx,
                'num_gpu': -1,
            }
        }
        response = requests.post(url, json=data, stream=True)
        for line in response.iter_lines():
            if not line:
                continue
            request = json.loads(line.decode())
            if ollama_api_addr == '/api/chat':
                content = request['message']['content'].strip()
                content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL).strip()
                rewritten_text += content
            elif ollama_api_addr == '/api/generate':
                if 'response' in request:               
                    if request.get('done'):
                        break
                    content = request['response']
                    if content is not None:
                        rewritten_text += content
                        if output == True:
                            sys.stdout.write(content)
                            sys.stdout.flush()
        return rewritten_text

def rewrite_text_with_Ollama(text, ai_addr, ollama_api_addr, ollama_api_model, prompt="Please rewrite this text:", pbar_flag=True, split_flag=True):
    rewritten_text = ''
    error_text = []
    clients = Client(
        host = ai_addr,
        headers={'x-some-header': 'some-value'},
    )
    client = clients.chat
    if ollama_api_addr == '/api/chat':
        client = clients.chat
    elif ollama_api_addr == '/api/generate':
        client = clients.generate
    if split_flag:
        chunks = split_text_into_chunks(text)
        if pbar_flag:
            pbar = tqdm(total=len(chunks), ncols=100)
        for chunk in chunks:
            # if ollama_api_addr == '/api/chat':
            #     messages=[
            #             {
            #                 "role": "system",
            #                 "content": prompt
            #             },
            #             {
            #                 "role": "user",
            #                 "content": chunk
            #             }
            #         ]
            # elif ollama_api_addr == '/api/generate':
            #     messages = prompt + "\n" + chunk
            # response = ollama_with_requests(
            #     ai_addr=ai_addr,
            #     ollama_api_model=ollama_api_model,
            #     ollama_api_addr=ollama_api_addr,
            #     stream=True,
            #     prompt=messages,
            #     options={
            #         "num_ctx": num_ctx,
            #         'num_gpu': -1,
            #     }
            # )
            # response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL).strip()
            # response = re.sub(r'Thinking\.\.\..*?\.\.\.done thinking\.', '', response, flags=re.DOTALL).strip()
            # rewritten_text += response
            response = client(
                model =ollama_api_model,
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": prompt + " /nothing /no_thinking /no thinking"
                    },
                    {
                        "role": "user",
                        "content": chunk + " /nothing /no_thinking /no thinking"
                    }
                ],
                options={
                    "num_ctx": num_ctx,
                    'num_gpu': -1,
                }
            )
            try:
                for line in response:
                    if not line:
                        continue
                    # request = json.loads(line.decode())
                    request = line
                    if line.get('error'):
                        error_text.append(f"Error: {line['error']}\n")
                        continue
                    if ollama_api_addr == '/api/chat':
                        content = request.message.content.strip()
                        rewritten_text += content
                    elif ollama_api_addr == '/api/generate':
                        if 'response' in request:
                            content = request['response']
                            if content is not None:
                                rewritten_text += content
                    sys.stdout.write(content)
                    sys.stdout.flush()
                    if request.get('done'):
                        break
                sys.stdout.write('\n')
                sys.stdout.flush()
                rewritten_text = re.sub(r'<think>.*?</think>\s*', '', rewritten_text, flags=re.DOTALL).strip()
                rewritten_text = re.sub(r'Thinking\.\.\..*?\.\.\.done thinking\.', '', rewritten_text, flags=re.DOTALL).strip()
                rewritten_text += '\n'
                # if ollama_api_addr == '/api/chat':
                #     content = response.message.content.strip()
                #     content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL).strip()
                # elif ollama_api_addr == '/api/generate':
                #     content = response['response']
                #     if content is not None:
                #         rewritten_text += content
                if pbar_flag:        
                    pbar.update(1)
            except Exception as e:
                return "error"
        if pbar_flag:
            pbar.close()
    else:
        chunks = text
        # if ollama_api_addr == '/api/chat':
        #     messages=[
        #             {
        #                 "role": "system",
        #                 "content": prompt
        #             },
        #             {
        #                 "role": "user",
        #                 "content": chunks
        #             }
        #         ]
        # elif ollama_api_addr == '/api/generate':
        #     messages = prompt + "\n" + chunks
        # response = ollama_with_requests(
        #     ai_addr=ai_addr,
        #     ollama_api_model=ollama_api_model,
        #     ollama_api_addr=ollama_api_addr,
        #     stream=True,
        #     prompt=messages,
        #     options={
        #         "num_ctx": num_ctx,
        #         'num_gpu': -1,
        #     }
        # )
        # response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL).strip()
        # response = re.sub(r'Thinking\.\.\..*?\.\.\.done thinking\.', '', response, flags=re.DOTALL).strip()
        # rewritten_text += response
        response = client(
            model =ollama_api_model,
            messages=[
                {
                    "role": "system",
                    "content": prompt + " /nothing /no_thinking /no thinking"
                },
                {
                    "role": "user",
                    "content": chunks + " /nothing /no_thinking /no thinking"
                }
            ],
            options={
                "num_ctx": num_ctx,
                'num_gpu': -1 ,
            }
        )
        try:
            if ollama_api_addr == '/api/chat':
                content = response.message.content.strip()
                content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL).strip()
            elif ollama_api_addr == '/api/generate':
                content = response['response']
                if content is not None:
                    rewritten_text += content
        except Exception as e:
            return "error"
    
    if len(error_text) > 0:
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            try:
                for _chunk in error_text:
                    log_file.write(_chunk)
            except Exception as e:
                log_file.write(str(e))
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
    chinese_punctuation = r"[。，、；：？！“”‘’《》（）【】]"
    english_punctuation = r"[.,;:?!\"\"''<>()[\]{}]"
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
        line = line.rstrip() + ' '
        if chinese_chars_and_punctuation.search(line) and not line.endswith(tuple('。，、；：？！“”‘’《》（）【】')):
            if len(current_line) > 12:
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
                extracted_texts.append(' \n'.join(matches) + ' \n')

    output_text = ""
    for text in extracted_texts:
        output_text += text + '\n'
    process_contents(output_text, ori__file_path)
    # output_text = remove_chapter_markers(output_text)
    # output_text = merge_lines_without_punctuation(output_text)
    # output_text = insert_new_lines_with_condition(output_text)
    # output_text = split_long_lines(output_text)
    # output_text = merge_short_lines(output_text)
    # output_text = replace_punctuation_with_space(output_text)
    # output_text = remove_lines_with_only_numbers_or_symbols(output_text)
    # write_text_to_file(output_text, ori__file_path)
    # with open(output_file_path, 'w', encoding='utf-8') as output_file:
    #     output_file.write(output_text)

    # print(f"Extraction completed, saved to: {output_file_path}")

def process_contents(input_text, file_path):
    output_text = remove_chapter_markers(input_text)
    output_text = merge_lines_without_punctuation(output_text)
    output_text = insert_new_lines_with_condition(output_text)
    output_text = split_long_lines(output_text)
    output_text = merge_short_lines(output_text)
    output_text = replace_punctuation_with_space(output_text)
    output_text = remove_lines_with_only_numbers_or_symbols(output_text)
    write_text_to_file(output_text, file_path)

def remove_duplicates(csv_file, column):
    # 读取并去重数据
    words = set()
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            no_chinese = re.sub(r'[\u4e00-\u9fff]+', '', row[column])
            row[column] = ','.join(set(no_chinese.split(',')))
            rows.append(row)

    # 将去重后的数据写回文件
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def dict_to_csv(dict_array, csv_file):
    """
    Write a dictionary to a CSV file.
    """
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=dict_array[0].keys())
        # writer.writeheader()  # 写入表头
        writer.writerows(dict_array)  # 写入数据
    remove_duplicates(csv_file, 2)

def split_by_line_number(text):
    """
    将字符串中的行号及内容分到单独的行。
    行号格式为数字后跟点，例如：1. 2. 3. 等。
    """
    # 修改正则表达式，匹配行号及其后面的内容，直到下一个行号出现
    pattern = r'(\d+\..*?)(?=\d+\.|$)'
    matches = re.findall(pattern, text, flags=re.DOTALL)

    # 将匹配的内容分到单独的行
    result = "\n".join(matches)
    return result