import subprocess # 在python 中跑shell 指令
import re # regular expression 的library
import json # 資料格式json 的library
import sys

def split_and_extract():
    extract_index() # 將目錄部份轉成純文字檔儲存在./tmp下
    names, startPages = get_people() # 擷取出目錄上的人名和開始頁數
    output_names(names) # 把人名用json檔儲存 (之後jieba 可以拿來加進其辭典)
    output_people_txts(names, startPages) # 分別轉並儲存各人物的文字檔
    
def extract_index():
    # 如同在shell, 命令pdfbox 將 社會與文化篇.pdf 的3~9頁轉成純文字檔儲存在./tmp 下
    subprocess.run(['java', '-jar', 'pdfbox-app-1.8.13.jar', 'ExtractText', '-startPage', '3', '-endPage', '9', '社會與文化篇.pdf', './tmp/index.txt'])

def get_people():
    with open('./tmp/index.txt', 'r') as f:
        index_text = f.read()
    # 利用regular expression 來搜尋目錄，回傳(人物名子,開頭頁數)s
    person_tuples = re.findall(r'^(\w　?\w+) ?\.+ (\d\d\d)$', index_text, re.MULTILINE)
    names = []
    startPages = []
    for person in person_tuples:
        names.append(person[0])
        startPages.append(person[1])
        
    return names, startPages
    
def output_names(names):
    with open('./tmp/names.json', 'w') as f:
        json.dump(names, f) # 把names 變成json 檔案儲存

def output_people_txts(names, startPages):
    for (i, (name, startPage_str)) in enumerate(zip(names, startPages)):
        name = name.replace("　","") # 二字人名在目錄中會有全形空格在中間
        startPage = int(startPage_str) + 20 # 從目錄掃出來的是字串，要轉成數字 # +20 是因為市誌一開始從羅馬數字開始，市誌第1頁其實是pdf的第21頁
        endPage = int(startPages[i+1]) - 1 + 20 # 這個人物的結尾頁數是下一個人物的開頭頁數再減1
        
        if startPage > 262 + 20: # 262 是我們負責的部份的最後一頁, 超過262就停止
            break
        else:
            subprocess.run(['java', '-jar', 'pdfbox-app-1.8.13.jar', 'ExtractText', '-startPage', str(startPage), '-endPage', str(endPage), '社會與文化篇.pdf', './Texts/{}.txt'.format(name)])
    
if __name__ == "__main__":
    split_and_extract()
        
