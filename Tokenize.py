import argparse
import os # 處理path 用
import json # 通用的資料格式
import sys
import re
import jieba # 斷詞的工具
jieba.set_dictionary('dict.txt.big') # 輔助的jieba 的辭典
from CKIP_client import ckip_client # 中研院斷詞

# 開啟所有txt files, 各自斷詞輸出
def tokenize(tokenizeTool, people=None):
    txts = get_txtFiles(people) # 回傳指定人物們的txt檔路徑，若沒有指定則是全部的txt檔的路徑
    
    for txt in txts:
        with open(txt, 'r') as f:
            text = f.read()
            
        if tokenizeTool == "jieba":
            tokens = jieba_tokenize(text)
        elif tokenizeTool == "ckip":
            tokens = ckip_tokenize(text)
        else:
            raise InputError("Unkown tokenize tool.")        
        
        # 輸出成檔案儲存
        with open(txt[:-4] + "_" + tokenizeTool + "_tokens", 'w') as f:
            f.write("\n".join(tokens))

def get_txtFiles(people_names):
    if people_names is None:
        txt_files = list(filter(lambda f: f[-4:]=='.txt', # 取後面4個字是.txt 的
                                  os.listdir('./Texts'))) # 從./Texts 底下所有檔案或目錄取
        return ['./Texts/' + txtFile for txtFile in txt_files] # 將所有txt檔名轉成路徑的list
    else:
        return ['./Texts/{}.txt'.format(person_name) for person_name in people_names]
    
# 切出純文字的tokens
def jieba_tokenize(text):
    enhance_jieba_dict() # 因為是暫時性的，沒辦法做一次後就不做(加入到辭典)
    
    text = text.replace("\n", "") # 如果有詞剛好橫跨行尾，會被切成兩個詞，所以要把行尾去掉
    text = text.replace(" ", "")
    tokens = list(jieba.cut(text)) # 此時的仍包含標點符號、數字...的token
    word_tokens = list(filter(lambda token: token.isalpha(), tokens)) # 只留純文字的token
    return word_tokens

# 暫時性的把一些資訊加到辭典裡
def enhance_jieba_dict():
    with open('./tmp/names.json', 'r') as f:
        names = json.load(f)
    
    for name in names:
        jieba.add_word(name, tag='nr') # tag 是其詞性

def ckip_tokenize(text):
    text = text.replace("\n", "") # 如果有詞剛好橫跨行尾，會被切成兩個詞，所以要把行尾去掉
    text = text.replace(" ", "")
    
    word_tokens = []
    sentences = re.split("，|。", text) # 利用逗號和句號切成數段句子，避免一次對ckip server的request 太大
    for sent in sentences:
        result, length = ckip_client(sent + "。") # 將每句後面加上句點，避免ckip server 的internal error
        result = result.split("　") # (token, POS tag) 間會以全形空白來隔開
        for item in result:
            cut_index = item.find('(') # 每個斷詞後面會括號其詞性
            token = item[:cut_index] # 我們只取該token，不取詞性
            if token.isalpha(): # 只取純文字的token
                word_tokens.append(token)
                
    return word_tokens

class InputError(Exception):
    def _init_(self, string):
        self.message = string

    def _str_(self):
        return repr(self.message)

if __name__ == "__main__":
    # 這邊的說明請看Statistic.py 的下方
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-p', '--people',
                           nargs='+', 
                           help="specify some people to analyze, otherwise analyze all")
    argParser.add_argument('-t', '--tool', 
                           nargs='+',
                           choices=['ckip', 'jieba'], 
                           required=True, 
                           metavar="TOOLS", 
                           dest='tools', 
                           help="specify one or two tools to tokenize.")
    args = argParser.parse_args()
    
    for tool in args.tools:
        tokenize(tool, args.people)

#========================================================
#                      Test
#========================================================
# python Tokenize.py --tools ckip 
# python Tokenize.py -t jieba --people 何凡 何基明

