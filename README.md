# 本项目为了方便的从网页提取小说构建
## 主要功能
- 从网页提取小说
- 去除所有不必要的标签
- 去除所有标点符号
- 控制每行的字数
- 生成txt小说文件
- 增加gpt洗文功能，支持第三方gpt
- 增加Gemini洗文功能

## 使用方法
1. 安装Python3
    请移步[这里](https://www.runoob.com/python3/python3-install.html)查看详细步骤
    我这里就不赘述了，能找到这个项目的人应该都会安装Python3
2. 下载本项目文件
    请点击右上角的绿色按钮，选择Download ZIP，或者使用git clone下载
3. 安装依赖
    在项目文件夹下打开终端(cmd或者shell)，输入以下命令
    ```shell
    pip install -r requirements.txt
    ```
4. 配置
    - 在config.ini中配置你的GPT/Gemini参数，格式如下
        > ; 第三方GPT-3 API地址和API Key
        > ai_addr=https://api.xxxx.xxx/v1
        > ai_api_key=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        > ; Google API Key
        > google_ai_addr=null
        > google_ai_api_key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    - 创建contents文件夹，将需要提取的小说网页(html扩展名)保存在contents文件夹下
5. 运行
    - 在项目文件夹下打开终端，输入以下命令
        ```shell
        python get_words.py
        ```
    - 程序会提示当前最新的文件是什么，如果确认，就直接回车；如果不是，输入需要提取的文件名，再回车
        > Enter the content name (default: xxxx):
    - 程序会提示选择功能：
        > 1: pre process html file: （预处理html文件）
        > 2: process txt file with gpt: （ai 洗文）

        __请务必先预处理html文件，再进行洗文操作；预处理html会自动切断每行的字数，并去除没有必要的标点符号。__
    - 如果选择ai洗文，下面系统会提示当前默认的ai是Gemini，如果需要切换使用GPT，请输入y，再回车
        > Current AI is: GenMini
        > Do you want to switch AI? (y/n):
    - 洗文完成后，会生成相应的txt文件，保存在contents文件夹下, gen为Gemini洗文，gpt为GPT洗文
        > Extraction completed, saved to: ./contents/xxxx_gen.txt