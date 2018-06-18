import subprocess # 在python 中背景地跑shell 指令
import re # regular expression 的library
from Utilities import parallelly_process
# DataBase
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # create database "Summary" if not exist
db['biographies'] # create collection "biographies" if not exist

def main():
    indexes = extract_indexes() # 將目錄的項目和對應頁數擷取出來
    initialize_biographies(indexes) # 新增所有人的傳記到資料庫
    parallelly_process(extract_and_output, divide_param=list(db.biographies.find())) # 切割並輸出結果
    output_biographee_names()

def extract_catalog():
    # 如同在shell, 命令pdfbox 將 社會與文化篇.pdf 的3~9頁轉成純文字檔儲存
    # subprocess.run 的參數是 list of strings without space
    subprocess.run('java -jar ./Tools/pdfbox-app-1.8.13.jar ExtractText -startPage 3 -endPage 9 -encoding UTF-8 ./DataBase/社會與文化篇.pdf ./DataBase/tmp/index.txt'.split())
    
def extract_indexes():
    with open('./DataBase/tmp/index.txt', 'r') as f:
        index_text = f.read()

    match_pairs = re.findall(r'^(\w+　?\w+) ? ?\.+ (\d\d\d)$', index_text, re.MULTILINE)
    # return [("項目"，"起始頁數"), ("項目"，"起始頁數"),... .  ]
    match_pairs = list(filter(lambda pair: 5 <= int(pair[1]) <= 361, match_pairs)) # 抓的index限制在其起始頁數在5~361之間
    match_pairs.append(("第假章　最後墊底用", "363"))

    return match_pairs

def initialize_biographies(indexPair_s):
    category = "" # 目前所在的類別 e.g.教育學術
    for (i, indexPair) in enumerate(indexPair_s):
        item, startPage = indexPair

        if re.fullmatch(r'^第\w章　\w+$', item): # 若此index的項目是類別
            category = item[4:]
        else: # 否則此index的項目就是人物
            name = item.replace("　","") # 二字人名在目錄中會有全形空格在中間

            # 找符合query條件的document來update, 如果沒有則建立一個
            db.biographies.find_and_modify(
                query={'Name':name, 'StartPage':int(startPage),},
                
                update={'$set':
                        {'Name' : name,
                         'Alias_s' : [],
                         'Birth' : "",
                         'Death' : "",
                         'BirthPlace' : "",
                         'Hometown' : "",
                         # PDF、傳記相關
                         'Category' : category,
                         'StartPage' : int(startPage),
                         'EndPage' : int(indexPair_s[i+1][1]) - 1,
                         'Authors' : [],
                         'Notes' : [],
                         'Footnotes' : [],
                         # Summary
                         'Experience' : [], # 經歷
                         'ChronologicalTable' : [], # 年代表
                        }
                }, 

                upsert=True, # update + insert : 如果找不到則建立一個
            )

def extract_and_output(biograpies):
    for biograpy in biograpies:
        name = biograpy['Name']
        # 從目錄掃出來的是字串，要轉成數字. # +20 是因為市誌一開始從羅馬數字開始，市誌第1頁其實是pdf的第21頁
        startPage = int(biograpy['StartPage']) + 20
        endPage = int(biograpy['EndPage']) + 20
        
        command = 'java -jar ./Tools/pdfbox-app-1.8.13.jar ExtractText -startPage {} -endPage {} -encoding UTF-8 ./DataBase/社會與文化篇.pdf ./DataBase/raw_txt/{}-{}.txt'.format(str(startPage), str(endPage), str(startPage-20), name)
        subprocess.run(command.split() )

def output_biographee_names():
    with open('./Tools/Biographee-Names.dict.txt', 'w', encoding='utf-8') as f:
        for biography in db.biographies.find():
            print(biography['Name'], "nr", file=f)
    
if __name__ == "__main__":
    main()
        
