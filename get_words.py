from time import sleep
from common import *

ai_switch = 2 # (0:gpt, 1:genmini, 2:Ollama)
# ai_max_length =4096 - len(pre_prompts) - 100
dict_to_csv_limit = 10
up_scale = 8
down_scale = 3

# Main program
content_name = get_latest_file_name(contents_path)
if content_name is None:
    print("在文件夹中没有小说html文件")
    os.system("pause")
    sys.exit()
input_name = input("输入小说的名字(默认为: " + content_name + "): ")
if len(input_name) > 0:
    content_name = input_name
print("当前选择的小说是: " + content_name)

choice = input("1: 预处理小说的网页文件: \n2: 使用AI洗文: \n3: 测试AI: \n4: 创建导入脚本: \n5: 分析文档\n0: 退出\n请选择:")
while(True):
    if choice == '0':
        # check and unset system proxy
        if len(parameters["proxy_addr"]) > 0 and len(parameters["proxy_port"]) > 0:
            os.environ.pop('http_proxy')
            os.environ.pop('https_proxy')
            print("已经取消代理设置")
        break
    elif choice == '1':
        html_file_path = contents_path + content_name + '.html'
        if(not os.path.exists(html_file_path)):
            print("文件没有找到: " + html_file_path)
        else:
         extract_chinese_and_punctuation_from_html(html_file_path)
    elif choice == '2':
        base_name = contents_path + content_name
        ori__file_path = base_name + '.txt'
        if(not os.path.exists(ori__file_path)):
            print("文件没有找到: " + ori__file_path)
        else:
            ai_choice = input("当前的AI是: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama") + "\n你要不要切换(默认不要)? (y/n): ")
            if ai_choice == 'y':
                ai_switch = input("请输入AI的选择(0: GPT, 1: GenMini, 2: Ollama): ")
                print("AI切换为: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama"))
            if check_ai(ai_switch) == False:
                continue
            # base_name = os.path.splitext(html_file_path)[0]   
            if ai_switch == 0:
                mod_file_path = base_name + '_gpt.txt'
            elif ai_switch == 1:
                mod_file_path = base_name + '_gen.txt'
            elif ai_switch == 2:
                mod_file_path = base_name + '_ollama.txt'
            # read mod file to get the text
            output_text = ""
            with open(ori__file_path, 'r', encoding='utf-8') as file:
                output_text = file.read()
            # output_text = output_text.replace('\n', '')
            output_text = remove_chapter_markers(output_text)
            if ai_switch == 0:
                output_text = rewrite_text_with_gpt3(output_text, parameters['ai_addr'], parameters['ai_api_key'], parameters['ai_gpt_ver'], parameters['pre_prompts'])
            elif ai_switch == 1:
                output_text = rewrite_text_with_genai(output_text, parameters['google_ai_api_key'], parameters['pre_prompts'])
            elif ai_switch == 2:
                output_text = rewrite_text_with_Ollama(output_text, parameters['ai_addr'], parameters['ollama_api_addr'], parameters['ollama_api_model'], parameters['pre_prompts'])
            process_contents(output_text, mod_file_path)
            # output_text = merge_lines_without_punctuation(output_text)
            # output_text = insert_new_lines_with_condition(output_text)
            # output_text = split_long_lines(output_text)
            # output_text = merge_short_lines(output_text)
            # output_text = replace_punctuation_with_space(output_text)
            # output_text = remove_lines_with_only_numbers_or_symbols(output_text)
            # write_text_to_file(output_text, mod_file_path)
            print("处理完成")
    elif choice == '3':
        # check ai
        ai_choice = input("当前准备测试的AI是: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama") + "\n你要不要切换(默认不要)? (y/n): ")
        if ai_choice == 'y':
            ai_switch = input("请输入AI的选择(0: GPT, 1: GenMini, 2: Ollama): ")
            print("AI切换为: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama"))
        if check_ai(ai_switch) == False:
            continue
        test_text = "你是哪家公司的什么AI模型？"
        if ai_switch == 0:
            output_text = rewrite_text_with_gpt3(test_text, parameters['ai_addr'], parameters['ai_api_key'], parameters['ai_gpt_ver'], "测试AI:")
        elif ai_switch == 1:
            output_text = rewrite_text_with_genai(test_text, parameters['google_ai_api_key'], "测试AI:")
        elif ai_switch == 2:
            output_text = rewrite_text_with_Ollama(test_text, parameters['ai_addr'], parameters['ollama_api_addr'], parameters['ollama_api_model'], "测试AI:")
        print(output_text)
    elif choice == '4':
        if sutui_flag == 1:
            current_tenants = ""
            base_name = contents_path + content_name
            ori__file_path = base_name + '.txt'
            if(not os.path.exists(ori__file_path)):
                print("文件没有找到: " + ori__file_path)
            else:
                rows = []
                ai_choice = input("当前的AI是: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama") + "\n你要不要切换(默认不要)? (y/n): ")
                if ai_choice == 'y':
                    ai_switch = input("请输入AI的选择(0: GPT, 1: GenMini, 2: Ollama): ")
                    print("AI切换为: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama"))
                # base_name = os.path.splitext(html_file_path)[0]   
                if check_ai(ai_switch) == False:
                    continue
                extent = ""
                if ai_switch == 0:
                    mod_file_path = base_name + '_gpt.txt'
                    extent = "_gpt"
                elif ai_switch == 1:
                    mod_file_path = base_name + '_gen.txt'
                    extent = "_gen"
                elif ai_switch == 2:
                    mod_file_path = base_name + '_ollama.txt'
                    extent = "_ollama"
                if(os.path.exists(drafts_path + content_name + extent + '.csv')):
                    with open(drafts_path + content_name + extent + '.csv', 'r', encoding='utf-8') as file:
                        reader = csv.reader(file)
                        rows = list(reader)
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
                    up_string = ""
                    down_string = ""
                    for index in range(up_scale, 0, -1):
                        if (_i - index) >= 0:
                            up_string = output_text[_i - index] + ' ' + up_string
                    for index in range(1, down_scale + 1):
                        if (_i + index) < len(output_text):
                            down_string = down_string + ' ' + output_text[_i + index]
                    _other = " 以下是提供给你分析用的,上下文关联的段落,上文: " + up_string + " 下文: " + down_string + " 下面是正文，请分析后按上述要求输出："
                    if ai_switch == 0:
                        SutuiDB["fenjin_text"] = rewrite_text_with_gpt3(item, parameters['ai_addr'], parameters['ai_api_key'], parameters['ai_gpt_ver'], parameters['cj_prompts'] +_other, pbar_flag=False).strip()
                        SutuiDB["prompt"] = rewrite_text_with_gpt3(item, parameters['ai_addr'], parameters['ai_api_key'], parameters['ai_gpt_ver'], parameters['zx_prompts'] +_other, pbar_flag=False).strip()
                    elif ai_switch == 1:
                        SutuiDB["fenjin_text"] = rewrite_text_with_genai(item, parameters['google_ai_api_key'], parameters['cj_prompts'] +_other, pbar_flag=False).strip()
                        SutuiDB["prompt"] = rewrite_text_with_genai(item, parameters['google_ai_api_key'], parameters['zx_prompts'] +_other, pbar_flag=False).strip()
                    elif ai_switch == 2:
                        SutuiDB["fenjin_text"] = rewrite_text_with_Ollama(item, parameters['ai_addr'], parameters['ollama_api_addr'],  parameters['ollama_api_model'],parameters['cj_prompts'] +_other, pbar_flag=False).strip()
                        SutuiDB["prompt"] = rewrite_text_with_Ollama(item, parameters['ai_addr'], parameters['ollama_api_addr'],  parameters['ollama_api_model'], parameters['zx_prompts'] +_other, pbar_flag=False).strip()
                    if SutuiDB["fenjin_text"] == "error" or SutuiDB["prompt"] == "error":
                        print("\n第{}行发生AI错误，有可能是文字描述没有通过AI审查，请修改后再试.".format(_i + 1))
                        SutuiDB["fenjin_text"] = " "
                        SutuiDB["prompt"] = " "
                    sutui.append(SutuiDB.copy())
                    current_times += 1
                    if current_times >= dict_to_csv_limit:
                        if len(sutui) > 0:
                            dict_to_csv(sutui, drafts_path + content_name + extent + '.csv')
                        current_times = 0
                        sutui = []
                        sleep(10)
                    pbar.update(1)
                pbar.close()
                if len(sutui) > 0:
                    dict_to_csv(sutui, drafts_path + content_name + extent + '.csv')
                print("处理完成")
        else:
            print("没有正确配置速推数据库")
    elif choice == '5':
        _prompts = "你现在是一个文档分析器，我需要你分析下面的文字段落，把其中所有人物名字提取出来；并尝试分析上下文，找出其中可能存在的逻辑错误。下面就是这段文字：\n"
        base_name = contents_path + content_name
        _ee_text = "_gen"
        ex_choice = input("你要分析哪种文件(默认为: gen文件),要不要切换(默认不要)? (y/n): ")
        if ex_choice == 'y':
            _ee_text = "_gpt"
        ori__file_path = base_name + _ee_text + '.txt'
        if(not os.path.exists(ori__file_path)):
            print("文件没有找到: " + ori__file_path)
        else:
            ai_choice = input("当前的AI是: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama") + "\n你要不要切换(默认不要)? (y/n): ")
            if ai_choice == 'y':
                ai_switch = input("请输入AI的选择(0: GPT, 1: GenMini, 2: Ollama): ")
                print("AI切换为: " + ("GPT" if ai_switch == 0 else "GenMini" if ai_switch == 1 else "Ollama"))
            if check_ai(ai_switch) == False:
                continue
            output_text = ""
            with open(ori__file_path, 'r', encoding='utf-8') as file:
                output_text = file.read()
            if ai_switch == 0:
                output_text = rewrite_text_with_gpt3(output_text, parameters['ai_addr'], parameters['ai_api_key'], parameters['ai_gpt_ver'], _prompts)
            elif ai_switch == 1:
                output_text = rewrite_text_with_genai(output_text, parameters['google_ai_api_key'], _prompts)
            with open(analysis_path + content_name + '_analysis.txt', 'w', encoding='utf-8') as file:
                file.write(output_text)
            print("处理完成")
    else:
        print("选择错误")
    choice = input("1: 预处理小说的网页文件: \n2: 使用AI洗文: \n3: 测试AI: \n4: 创建导入脚本: \n5: 分析文档\n0: 退出\n请选择:")
os.system("pause")