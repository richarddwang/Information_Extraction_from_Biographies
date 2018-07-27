import re
import json
import requests
from requests_html import HTML # parse html內容，使方便查找裏面各種內容
# 繁簡轉換(不要用hanziconv， 有的會轉換錯誤)
from opencc import OpenCC
toTrad = OpenCC("s2t")

def main():
    response = requests.get('http://www.360doc.com/content/11/1014/13/552292_156114051.shtml') # 不要用request_html 來get 網頁資料，有的會有bug
    text = HTML(html=response.text).find('#blogDetailDiv', first=True).text # 放大陸地名主要html element # text 這個method，會取此element下面(recursively) 的所有text內容(text不是tag裏面的，而是tag夾的文字)
    # 將文本整理乾淨
    text = re.sub(r'\·\s*', "", text)
    text = re.sub(r'【.*】|\[.*\]', "", text)
    text = text.replace("　", "")
    text = re.sub(r'\s+', " ", text)
    # 轉成繁體，來配合台北市誌
    text = toTrad.convert(text)
    place_names = text.split(" ")[1:]
    # 將有些地名最後的『區』字去掉，讓它們更符合通常在文章上出現的樣子
    for (i, name) in enumerate(place_names):
        if name[-1] == "區":
            place_names[i] = name[:-1]
    # 去掉裏面的提到的台灣地名，得到大陸的地名
    with open('../Taiwanese-Place-Names.json', 'r') as f:
        taiwan_place_names = json.load(f)
    mainland_place_names = set(place_names) - set(taiwan_place_names)
    # 輸出成json 檔
    with open('../Mainland-Place-Names.json', 'w', encoding='utf-8') as f:
        json.dump(list(mainland_place_names), f)

if __name__ == '__main__':
    main()
