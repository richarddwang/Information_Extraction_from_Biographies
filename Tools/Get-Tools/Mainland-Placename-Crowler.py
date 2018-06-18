import re
import json
import requests
from requests_html import HTML
from hanziconv import HanziConv
toTraditional = HanziConv.toTraditional

def main():
    response = requests.get('http://www.360doc.com/content/11/1014/13/552292_156114051.shtml')
    text = HTML(html=response.text).find('#blogDetailDiv', first=True).text
    text = re.sub(r'\·\s*', "", text)
    text = re.sub(r'【.*】|\[.*\]', "", text)
    text = text.replace("　", "")
    text = re.sub(r'\s+', " ", text)
    text = toTraditional(text)
    place_names = text.split(" ")[1:] # no
    for (i, name) in enumerate(place_names):
        if name[-1] == "區":
            place_names[i] = name[:-1]
    with open('../Taiwanese-Place-Names.json', 'r') as f:
        taiwan_place_names = json.load(f)
    mainland_place_names = set(place_names) - set(taiwan_place_names)
    with open('../Mainland-Place-Names.json', 'w', encoding='utf-8') as f:
        json.dump(list(mainland_place_names), f)

if __name__ == '__main__':
    main()
