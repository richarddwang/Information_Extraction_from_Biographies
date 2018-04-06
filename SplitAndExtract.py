import subprocess # 可以在python 中跑shell 指令
import re # python 的regular expression 的library

def split_and_extract():
    # 將社會與文化篇的目錄的部份抽出成一個txt檔
    subprocess.run(['java', '-jar', 'pdfbox-app-1.8.13.jar', 'ExtractText', '-startPage', '3', '-endPage', '9', '社會與文化篇.pdf', './tmp/index.txt'])
    # 開啟包含目錄的txt檔，讀取內容成字串
    with open("./tmp/index.txt", 'rU') as f:
        text = f.read()

    # 利用regular expression 來搜尋目錄裡，人物名子和其對應的開頭頁數
    # 回傳值是list of tuple : (名子, 開頭頁數)， 裡面的開頭頁數是三位數數字的字串
    # 詳細在 README 裏面說明
    people = re.findall(r'^(\w+) ?\.+ (\d\d\d)$', text, re.MULTILINE)

    # 抽取出每個人物的部份並轉成txt檔儲存
    for (i, person) in enumerate(people):
        name = person[0]
        start_page = int(person[1]) +20 # +20 是因為市誌一開始從羅馬數字開始，市誌第1頁其實是pdf的第21頁
        end_page = int(people[i+1][1]) - 1 + 20 # 這個人物的結尾頁數是下一個人物的開頭頁數再減1
        if start_page > 262 + 20: # 262 是我們負責的部份的最後一頁
            break
        subprocess.run(['java', '-jar', 'pdfbox-app-1.8.13.jar', 'ExtractText', '-startPage', str(start_page), '-endPage', str(end_page), '社會與文化篇.pdf', './Texts/'+ name + '.txt'])

if __name__ == "__main__":
    split_and_extract()
