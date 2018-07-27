import json
from time import sleep # sleep 可以指定程式暫停一段時間
import requests 
from requests_html import HTML # parse html內容，使方便查找裏面各種內容
# 繁簡轉換 (不要用hanziconv， 有的會轉換錯誤)
from opencc import OpenCC
toTrad = OpenCC("s2t") 

"""
從日本網站爬下來的日本姓，有些使用平假名和跟中文漢字不同的日本漢字
例如：佐々木、斎藤
"""
def main():
    # 讀取爬下來的前7000名日本姓
    with open('../../tmp/Japanese-Surnames.json', 'r', encoding='utf-8') as f:
        surnames = json.load(f)

    # 皆轉換成台灣繁體
    surnames_in_zhTW = []
    for surname in surnames:
        translated_surname = translate_word_jp2zhTW(surname)
        translated_surname = toTrad.convert(translated_surname) # 字典網站的中文有的可能是用簡體，轉成繁體
        surnames_in_zhTW.append(translated_surname)
        """
        ！！重要！！ 
        用爬蟲過度頻繁使用他們的服務，會被鎖住避免其server被過度佔用，
        所以要隔一段時間送一個request，頻率大概跟人工使用其服務差不多快，展現我們誠意，當個善良的爬蟲
        """
        sleep(5)
        """
        小技巧：
        因為會執行很久，所以持續輸出翻譯後日本姓，證明還在正常執行中
        同時可以看到處理過的，知道處理得如何，
        另外也可以在錯誤的時候推敲得知在處理哪個時錯誤。
        """
        print(translated_surname) 

    # 輸出成json
    with open('../Japanese-Surnames-in-zhTW.json', 'w', encoding='utf-8') as f:
        json.dump(surnames_in_zhTW, f)
    
def translate_word_jp2zhTW(word):
    """
    利用爬蟲自動使用weblio的「中国語辞書」服務，來將日文的日本姓翻譯成中文的日本姓
    檢索結果可能會是：沒有結果，某一個字典的結果，複數個辭典的結果
    例：佐々木, 山崎, 中村, 斎藤, 伊藤。 從這些的檢索結果可以看到不同的情況
    """
    # 利用python 內建的requests來取得html
    response = requests.get('https://cjjc.weblio.jp/content/' + word) # 網址後面就是欲檢索的字詞
    # 將request 獲取的html字串，parse 成request_html 的class
    html = HTML(html=response.text)
    # 從整個html 限縮到顯示檢索結果的範圍
    main = html.find('#main', first=True)
    """
    我們只相信『Weblio中日対訳辞書』、『Wiktionary中国語版』這兩個字典的結果，
    其中又優先相信『Weblio中日対訳辞書』的結果
    """
    if main.search("Weblio中日対訳辞書") is True:
        wchnt_translation_result = html.find('div.Wchnt', first=True) # Wchnt代表Weblio中日対訳辞書，是其結果的html element特有的class
        # 如果判斷是檢索日文就會出現中文翻譯，如果判斷是中文就會出現日文翻譯，此時就不用另外處理
        if wchnt_translation_result.search("中国語訳"):
            translated_word = wchnt_translation_result.find('a', first=True).text # text 這個method，會取此element下面(recursively) 的所有text內容(text不是tag裏面的，而是tag夾的文字)
        else:
            translated_word = word
    elif main.search("Wiktionary中国語版"):
        kiji = list(filter(lambda kiji: kiji.find('div.Zhwik') is not None, main.find('div.kiji')))[0] # ZHwik 代表Wiktionary中国語版，是其結果的html element特有的class
        translated_word = kiji.find('h2.midashigo', first=True).text # midashigo = 見出し語，Wiktionary中国語版檢索結果的放中文的html element
    else:
        translated_word = word
                
    return translated_word

if __name__ == '__main__':
    main()
