import subprocess # 在python 中跑shell 指令
import re # regular expression 的library
import sys
import json # 資料格式json 的library
import threading
from functools import reduce

def main():
    extract_catalog() # 將目錄部份轉成純文字檔儲存在./tmp下
    indexes = extract_indexes()
    biographies = set_biographies_schema(indexes)
    biographies_s = divide_n_parts(biographies, 4)
    
    # Output
    output(biographies_s)
    
def extract_catalog():
    # 如同在shell, 命令pdfbox 將 社會與文化篇.pdf 的3~9頁轉成純文字檔儲存在./tmp 下
    subprocess.run('java -jar pdfbox-app-1.8.13.jar ExtractText -startPage 3 -endPage 9 社會與文化篇.pdf ./DataBase/tmp/index.txt'.split()) # 

def extract_indexes():
    with open('./DataBase/tmp/index.txt', 'r') as f:
        index_text = f.read()

    match_pairs = re.findall(r'^(\w+　?\w+) ? ?\.+ (\d\d\d)$', index_text, re.MULTILINE)
    match_pairs = list(filter(lambda pair: 5 <= int(pair[1]) <= 361, match_pairs))
    match_pairs.append(("第假章　最後墊底用", "363"))

    return match_pairs

def set_biographies_schema(indexPair_s):
    biographies = []
    category = ""
    for (i, indexPair) in enumerate(indexPair_s):
        item, startPage = indexPair

        if re.fullmatch(r'^第\w章　\w+$', item):
            category = item[4:]
        else:
            name = item.replace("　","") # 二字人名在目錄中會有全形空格在中間
    
            biography = {
                "Name" : name,
                "Alias_s" : [],
                #
                "Category" : category,
                "StartPage" : int(startPage),
                "EndPage" : int(indexPair_s[i+1][1]) - 1, # 這個傳記的結尾頁數是下一個傳記的開頭頁數再減1
                "Authors" : [],
                "Notes" : "",
                "footnotes" : [],
                #
                "Locations" : [],
                "Identities" : [],
                "ChronologicalTable" : [],
                #
                "Birth" : "",
                "Death" : "",
                "BirthPlace" : "",
                "Hometown" : ""
            }
            biographies.append(biography)

    return biographies

def divide_n_parts(lst, n):
    return [lst[i::n] for i in range(n)]

# [startIndex : endIndex : skip]

# Example:
# Divide [0, 1, 2, 3, 4, 5, 6, 7, 8 ,9, 10, 11, 12] into 3 parts
# -> [[0, 3, 6, 9, 12], [1, 4, 7, 10], [2, 5, 8, 11]]

def output(biographies_s):
    all_biographies = reduce(lambda x,y: x + y, biographies_s)

    #
    threads = []
    #
    for part_biographies in biographies_s:
        thread = threading.Thread(target=output_txts, args=[part_biographies])
        threads.append(thread)
    #
    thread = threading.Thread(target=output_metaDatas, args=[all_biographies])
    threads.append(thread)

    #
    for thread in threads:
        thread.start()

    #
    for thread in threads:
        thread.join()


def output_txts(biographies):
    for biography in biographies:
        name = biography["Name"]
        # 從目錄掃出來的是字串，要轉成數字 # +20 是因為市誌一開始從羅馬數字開始，市誌第1頁其實是pdf的第21頁
        startPage = biography["StartPage"] + 20 
        endPage = biography["EndPage"] + 20

        command = 'java -jar pdfbox-app-1.8.13.jar ExtractText -startPage {} -endPage {} 社會與文化篇.pdf ./DataBase/raw_txt/{}.txt'.format(str(startPage), str(endPage), name)
        subprocess.run(command.split() )

def output_metaDatas(biographies):
    for biography in biographies:
        with open('./DataBase/metaData/{}_metaData.json'.format(biography["Name"]), 'w') as f:
            json.dump(biography, f) # 把biography(dict type) 變成json 檔案儲存
    
if __name__ == "__main__":
    main()
        
