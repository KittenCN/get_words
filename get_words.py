from common import *
import shutil

if len(ai_addr) == 0 or len(ai_api_key) == 0:
    # check config.ini file, if it is not exict, then check the __config.ini file , if it is not exist, then warning and exit; else create the config.ini file from __config.ini file
    if not os.path.exists('config.ini'):
        if not os.path.exists('__config.ini'):
            print("没有找到配置文件config.ini或者__config.ini")
            exit()
        else:
            shutil.copy('__config.ini', 'config.ini')
            print("已经创建了配置文件config.ini，请打开配置文件填写相应的信息后，再次运行本程序！")
            exit()
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
            elif line.startswith('pre_prompts'):
                pre_prompts = line.split('=')[1].strip()
            elif line.startswith('ai_gpt_ver'):
                ai_gpt_ver = int(line.split('=')[1].strip())

# Main program
# check the folder address, if not exist, create it
if not os.path.exists(contents_path):
    os.makedirs(contents_path)
content_name = get_latest_file_name(contents_path)
if content_name is None:
    print("在文件夹中没有html文件")
    exit()
input_name = input("输入小说的名字(默认为: " + content_name + "): ")
if len(input_name) > 0:
    content_name = input_name
print("当前选择的小说是: " + content_name)

choice = input("1: 预处理小说的网页文件: \n2: 使用AI洗文: \n3: 测试AI: \n请选择:")
if choice == '1':
    html_file_path = contents_path + content_name + '.html'
    if(not os.path.exists(html_file_path)):
        print("文件没有找到: " + html_file_path)
        exit()
    extract_chinese_and_punctuation_from_html(html_file_path)
elif choice == '2':
    base_name = contents_path + content_name
    ori__file_path = base_name + '.txt'
    if(not os.path.exists(ori__file_path)):
        print("文件没有找到: " + ori__file_path)
        exit()
    ai_choice = input("当前的AI是: " + ("GPT" if ai_switch == 0 else "GenMini") + "\n你要不要切换(默认不要)? (y/n): ")
    if ai_choice == 'y':
        ai_switch = 1 - ai_switch
        print("AI切换为: " + ("GPT" if ai_switch == 0 else "GenMini"))
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
    output_text = merge_short_lines(output_text)
    output_text = replace_punctuation_with_space(output_text)
    output_text = remove_lines_with_only_numbers_or_symbols(output_text)
    write_text_to_file(output_text, mod_file_path)
elif choice == '3':
    # check ai
    ai_choice = input("当前准备测试的AI是: " + ("GPT" if ai_switch == 0 else "GenMini") + "\n你要不要切换(默认不要)? (y/n): ")
    if ai_choice == 'y':
        ai_switch = 1 - ai_switch
        print("AI切换为: " + ("GPT" if ai_switch == 0 else "GenMini"))
    test_text = "你是哪家公司的什么AI模型？"
    if ai_switch == 0:
        output_text = rewrite_text_with_gpt3(test_text, "测试AI:")
    elif ai_switch == 1:
        output_text = rewrite_text_with_genai(test_text, "测试AI:")
    print(output_text)
else:
    print("选择错误")
    exit()