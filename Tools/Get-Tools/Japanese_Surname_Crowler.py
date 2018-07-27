import re
import json
import requests
from requests_html import HTML # parse html內容，使方便查找裏面各種內容
from functools import reduce

"""
根據『日本の苗字七千傑』這個網站(雖然這邊使用的是『名字由来net』這個網站)，
前7000名的日本姓大約涵蓋全日本人口的96%
"""
def main():
    # page=0 是前0~500 頻繁日本姓，page=1 是前501~1000，依此類推，取前7000名的日本姓
    url_prefix = 'https://myoji-yurai.net/prefectureRanking.htm?prefecture=%E5%85%A8%E5%9B%BD&page='
    surnames = []
    for p in range(14):
        surnames += crowl_ja_surname(url_prefix + str(p))

    # 輸出成json
    with open('../../DataBase/tmp/Japanese-Surnames.json', 'w') as f:
        json.dump(surnames, f)
        
def crowl_ja_surname(url):
    # 利用python 內建的requests來取得html
    Response = requests.get(url) # 不要用request_html 來get 網頁資料，有的會有bug
    # 將request 獲取的html字串，parse 成request_html 的class
    html = HTML(html=response.text)
    # 找到html裏面的日本姓們
    tables = html.find('table') # 找所有html裡的tables，回傳list
    ranking_tables = list(filter(lambda table: table.search("名字") and table.search("人数"), tables)) # 只取其下的文字內容(非指tag內，夾在tag之間的text)有名字、人数的tables，因為那才是姓氏排名的table
    surname_links = reduce(lambda table1, table2: table1.find('a') + table2.find('a'), ranking_tables) # 串成一個包含所有表格內所有連結的list(因為在網站上，每個顯示的姓氏都是個連結)
    surnames = list(map(lambda link: link.text, surname_links)) # 把所有連結中的文字提出來，就是所有的姓氏 # text 這個method，會取此element下面(recursively) 的所有text內容(text不是tag裏面的，而是tag夾的文字)
    return surnames
    
if __name__ == '__main__':
    main()
