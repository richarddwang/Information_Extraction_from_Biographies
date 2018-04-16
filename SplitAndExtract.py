import subprocess # 可以在python 中跑shell 指令
import re # python 的regular expression 的library
import sys

def split_and_extract():
    names_and_ranges = extract_names_ranges()
    for person in names_and_ranges:
        name = person[0]
        start_page = person[1]
        end_page = person[2]
        subprocess.run(['java', '-jar', 'pdfbox-app-1.8.13.jar', 'ExtractText', '-startPage', str(start_page), '-endPage', str(end_page), '社會與文化篇.pdf', './Texts/'+ name + '.txt'])

def extract_names_ranges():
    # 將社會與文化篇的目錄的部份抽出成一個txt檔
    #subprocess.run(['java', '-jar', 'pdfbox-app-1.8.13.jar', 'ExtractText', '-startPage', '3', '-endPage', '9', '社會與文化篇.pdf', './tmp/index.txt'])
    # 開啟包含目錄的txt檔，讀取內容成字串
    with open("./tmp/index.txt", 'rU') as f:
        index_text = f.read()

    # 利用regular expression 來搜尋目錄裡，人物名子和其對應的開頭頁數
    # 回傳值是list of tuple : (名子, 開頭頁數)， 裡面的開頭頁數是三位數數字的字串
    # 詳細在 github README 裏面說明
    people = re.findall(r'^(\w　?\w+) ?\.+ (\d\d\d)$', index_text, re.MULTILINE)

    # 抽取出每個人物的部份並轉成txt檔儲存
    names_and_ranges = [] # list of 3-tuple (name, startPage, endPage)
    for (i, person) in enumerate(people):
        name = person[0].replace("　","")
        start_page = int(person[1]) +20 # +20 是因為市誌一開始從羅馬數字開始，市誌第1頁其實是pdf的第21頁
        end_page = int(people[i+1][1]) - 1 + 20 # 這個人物的結尾頁數是下一個人物的開頭頁數再減1
        names_and_ranges.append( (name, start_page, end_page) )
        if start_page > 262 + 20: # 262 是我們負責的部份的最後一頁
            break # 掃到 葛小寶時，就不再做抽取了(只做到楊德昌)

    return names_and_ranges

if __name__ == "__main__":
    split_and_extract()
        
