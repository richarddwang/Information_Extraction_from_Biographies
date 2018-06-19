import re
import json
import requests
from requests_html import HTML
from functools import reduce

def main():
    url_prefix = 'https://myoji-yurai.net/prefectureRanking.htm?prefecture=%E5%85%A8%E5%9B%BD&page='
    surnames = []
    for p in range(14):
        surnames += crowl_ja_surname(url_prefix + str(p))
        
    with open('../../DataBase/tmp/Japanese-Surnames.json', 'w') as f:
        json.dump(surnames, f)
        
def crowl_ja_surname(url):
    response = requests.get(url)
    html = HTML(html=response.text)
    tables = html.find('table')
    ranking_tables = list(filter(lambda table: table.search("名字") and table.search("人数"), tables))
    surname_links = reduce(lambda table1, table2: table1.find('a') + table2.find('a'), ranking_tables)
    surnames = list(map(lambda link: link.text, surname_links))
    return surnames
    
if __name__ == '__main__':
    main()
