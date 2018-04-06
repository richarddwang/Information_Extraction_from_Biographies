import jieba # 斷詞的工具
from CKIP_client import ckip_client # 中研院斷詞
import os # 處理path 用
import json # 通用的資料格式
import sys
import re
jieba.set_dictionary('dict.txt.big') # 輔助的jieba 的辭典

# 開啟所有txt files, 各自斷詞, 輸出
def main(input_path, output_format, tool):
    directory_path, txt_names = process_input(input_path)
    for txt_name in txt_names:
        with open(directory_path + txt_name, 'rU') as f:
            text = f.read()
            
        if tool == "jieba":
            tokens = jieba_tokenize(text)
        elif tool == "ckip":
            tokens = ckip_tokenize(text)
        else:
            raise InputError("Unkown tokenize tool.")
        
        process_output(tokens, output_format, directory_path, txt_name, tool)

# 判斷INPUT_PATH 是一個txt檔案的路徑還是一個資料夾路徑
# 回傳所有txt 檔案的名子(包括副檔名)
def process_input(input_path):
    base_path, extension = os.path.splitext(input_path) # 切出副檔名
    directory_path = os.path.dirname(input_path) + "/" # 切出路徑裡的目錄部份
    
    txt_names = []
    # 如果INPUT_PATH 是一個txt檔案的路徑
    # 切出奇檔案名子
    if extension == '.txt': 
        assert os.path.dirname(input_path) != "", "You should specify full path to the txt file."
        txt_names.append(os.path.basename(input_path))
    # 如果INPUT_PATH 是一個資料夾的路徑
    # 網羅其下面的所有txt 檔案的名子
    elif extension == '': 
        assert input_path[-1] == "/", "You should put / at the end of the directory path."
        txt_names = list(filter(lambda name: '.txt' in name, os.listdir(input_path)))
    # 都不是就報錯
    else:
        raise InputError("Only accept a path to a txt file or a directory path")
    
    return directory_path, txt_names

# 切出純文字的tokens
def jieba_tokenize(text):
    text = text.replace("\n", "") # 如果有詞剛好橫跨行尾，會被切成兩個詞，所以要把行尾去掉
    text = text.replace(" ", "")
    tokens = list(jieba.cut(text)) # 此時的結果仍包含標點符號、數字...
    word_tokens = list(filter(lambda token: token.isalpha(), tokens)) # 只留純文字的token
    return word_tokens

def ckip_tokenize(text):
    text = text.replace("\n", "") # 如果有詞剛好橫跨行尾，會被切成兩個詞，所以要把行尾去掉
    text = text.replace(" ", "")
    
    word_tokens = []
    sentences = re.split("，|。", text) # 利用逗號和句號切成數段句子，避免一次對ckip server的request 太大
    for sent in sentences:
        result, length = ckip_client(sent + "。") # 將每句後面加上句點，避免ckip server 的internal error
        result = result.split("\u3000") # 結果會以一個unicode的字符來隔開
        for item in result:
            cut_index = item.find('(') # 每個斷詞後面會括號其詞性
            token = item[:cut_index] # 我們只取該token，不取詞性
            if token.isalpha(): # 只取純文字的token
                word_tokens.append(token)
                
    return word_tokens

# 根據ouput format 做不同方式的輸出
def process_output(tokens, output_format, directory_path, txt_name, tool):
    # 直接印在shell上
    if output_format == "shell": 
        print(tokens)
    # 在原處產生txt檔
    elif output_format == "txt":
        with open(directory_path + txt_name[:-4] + tool + "_tokens.txt", 'w') as f:
            f.write("\n".join(tokens))
    # 在原處產生json格式的檔案
    elif output_format == "json":
        with open(directory_path + txt_name[:-4] + tool + "_tokens.json", 'w') as f:
            json.dump(tokens, f)
    # 都不是就報錯
    else:
        raise InputError("Wrong ouput format, choose \"shell\", \"txt\",or \"json\"")
        
class InputError(Exception):
    def _init_(self, string):
        self.message = string

    def _str_(self):
        return repr(self.message)

if __name__ == "__main__":
    assert len(sys.argv) == 4, "Tokenize.py <Tokenize tool > <ouput format> <path_to_txt_file / directory>"
    main(sys.argv[3], sys.argv[2], sys.argv[1])
