import os
import csv
from time import sleep
from common import *

ai_switch = 1 # (0:gpt, 1:genmini)
# ai_max_length =4096 - len(pre_prompts) - 100
dict_to_csv_limit = 10

# Main program
content_name = get_latest_file_name(contents_path)
if content_name is None:
    print("在文件夹中没有html文件")
    exit()
input_name = input("输入小说的名字(默认为: " + content_name + "): ")
if len(input_name) > 0:
    content_name = input_name
print("当前选择的小说是: " + content_name)

choice = input("1: 预处理小说的网页文件: \n2: 使用AI洗文: \n3: 测试AI: \n4: 创建导入脚本: \n0: 退出\n请选择:")
while(True):
    if choice == '0':
        break
    elif choice == '1':
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
            output_text = rewrite_text_with_gpt3(output_text, ai_addr, ai_api_key, ai_gpt_ver, pre_prompts)
        elif ai_switch == 1:
            output_text = rewrite_text_with_genai(output_text, google_ai_api_key, pre_prompts)
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
            output_text = rewrite_text_with_gpt3(test_text, ai_addr, ai_api_key, ai_gpt_ver, "测试AI:")
        elif ai_switch == 1:
            output_text = rewrite_text_with_genai(test_text, google_ai_api_key, "测试AI:")
        print(output_text)
    elif choice == '4':
        if sutui_flag == 1:
            current_tenants = ""
            base_name = contents_path + content_name
            ori__file_path = base_name + '.txt'
            if(not os.path.exists(ori__file_path)):
                print("文件没有找到: " + ori__file_path)
                exit()
            rows = []
            if(os.path.exists(drafts_path + content_name + '.csv')):
                with open(drafts_path + content_name + '.csv', 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    rows = list(reader)
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
            sutui = []
            current_times = 0
            with open(mod_file_path, 'r', encoding='utf-8') as file:
                output_text = file.read().split('\n')
            pbar = tqdm(total=len(output_text))
            for _i, item in enumerate(output_text):
                if len(rows) > 0 and (_i + 1) <= len(rows):
                    pbar.update(1)
                    continue
                SutuiDB["text_content"] = item.strip()
                if ai_switch == 0:
                    SutuiDB["fenjin_text"] = rewrite_text_with_gpt3(item, ai_addr, ai_api_key, ai_gpt_ver, cj_prompts, pbar_flag=False).strip()
                    SutuiDB["prompt"] = rewrite_text_with_gpt3(item, ai_addr, ai_api_key, ai_gpt_ver, zx_prompts, pbar_flag=False).strip()
                elif ai_switch == 1:
                    SutuiDB["fenjin_text"] = rewrite_text_with_genai(item, google_ai_api_key, cj_prompts, pbar_flag=False).strip()
                    SutuiDB["prompt"] = rewrite_text_with_genai(item, google_ai_api_key, zx_prompts, pbar_flag=False).strip()
                if SutuiDB["fenjin_text"] == "error" or SutuiDB["prompt"] == "error":
                    print("\n第{}行发生AI错误，有可能是文字描述没有通过AI审查，请修改后再试.".format(_i + 1))
                    SutuiDB["fenjin_text"] = "\n "
                    SutuiDB["prompt"] = " "
                sutui.append(SutuiDB.copy())
                current_times += 1
                if current_times >= dict_to_csv_limit:
                    if len(sutui) > 0:
                        dict_to_csv(sutui, drafts_path + content_name + '.csv')
                    current_times = 0
                    sutui = []
                    sleep(10)
                pbar.update(1)
            pbar.close()
            if len(sutui) > 0:
                dict_to_csv(sutui, drafts_path + content_name + '.csv')
        else:
            print("没有正确配置速推数据库")
    else:
        print("选择错误")
    choice = input("1: 预处理小说的网页文件: \n2: 使用AI洗文: \n3: 测试AI: \n4: 创建导入脚本: \n0: 退出\n请选择:")