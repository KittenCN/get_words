import os
import sys

config_text = '; GPT版本 \n\
ai_gpt_ver=4 \n\
; 第三方GPT-3 API地址和API Key \n\
ai_addr=https://api.xxxx.xxx/v1 \n\
ai_api_key=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \n\
; Google API Key \n\
google_ai_addr=null \n\
google_ai_api_key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \n\
; Ollama \n\
ollama_api_addr=xxxx \n\
ollama_api_model=XXXX \n\
; 提示词 \n\
pre_prompts= \n\
; 速推数据库地址, 一般windows系统下地址为C:/Users/XXXX/AppData/Roaming/text2video/book2video/database_v2.sqlite，其中XXXX为用户名；其他系统请自行找寻 \n\
sutui_db_addr=C:/Users/XXXX/AppData/Roaming/text2video/book2video/database_v2.sqlite \n\
zx_index="【系统提词】解读正向词助手（升级版）" \n\
cj_index="【系统场景】解读场景词助手（升级版）" \n\
zx_prompts= \n\
cj_prompts= \n\
proxy_addr= \n\
proxy_port= \n\
1st_prompts= \n'


def write_config():
    if not os.path.exists('config.ini'):
        with open('config.ini', 'w') as configfile:
            configfile.write(config_text)
        print("已经创建了配置文件config.ini，请打开配置文件填写相应的信息后，再次运行本程序！")
        os.system("pause")
        sys.exit()
    else:
        print("配置文件已存在，无需重复创建")