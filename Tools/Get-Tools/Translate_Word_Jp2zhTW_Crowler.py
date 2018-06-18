import json
from time import sleep
import requests
from requests_html import HTML
from hanziconv import HanziConv
toTraditional = HanziConv.toTraditional


def main():
    with open('../../tmp/Japanese-Surnames.json', 'r', encoding='utf-8') as f:
        surnames = json.load(f)
        
    surnames_in_zhTW = []
    for surname in surnames:
        print(surname)
        translated_surname = translate_word_jp2zhTW(surname)
        translated_surname = toTraditional(translated_surname)
        surnames_in_zhTW.append(translated_surname)
        sleep(3)
    
    with open('../Japanese-Surnames-in-zhTW.json', 'w', encoding='utf-8') as f:
        json.dump(surnames_in_zhTW, f)
    
def translate_word_jp2zhTW(word):
    # e.g. 佐々木, 山崎, 中村, 斎藤, 伊藤
    response = requests.get('https://cjjc.weblio.jp/content/' + word)
    html = HTML(html=response.text)
    main = html.find('#main', first=True)
    if main.search("Weblio中日対訳辞書") is True:
        wchnt_translation_result = html.find('div.Wchnt', first=True)
        if wchnt_translation_result.search("中国語訳"):
            translated_word = wchnt_translation_result.find('a', first=True).text
        else:
            translated_word = word
    elif main.search("Wiktionary中国語版"):
        kiji = list(filter(lambda kiji: kiji.find('div.Zhwik') is not None, main.find('div.kiji')))[0]
        translated_word = kiji.find('h2.midashigo', first=True).text
    else:
        translated_word = word
                
    return translated_word

if __name__ == '__main__':
    main()
