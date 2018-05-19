import re
import json
import os
import subprocess
import math

def main():
    #
    biographies = get_biographies()
    for biography in biographies:
        process_biograpy(biography)
        
    #
    output_names(biographies)
    
def get_biographies():
    json_file_s = list(filter(lambda fle: fle[-5:]=='.json', # 取後面4個字是.json 的
                                  os.listdir('./DataBase/metaData'))) # 從./Texts 底下所有檔案或目錄取
    json_filePath_s = [os.getcwd() + '/DataBase/metaData/' + jsonFile for jsonFile in json_file_s] # 將所有json檔名轉成路徑

    biographies = []
    for json_filePath in json_filePath_s:
        with open(json_filePath, 'r') as f:
            biography = json.load(f)
            biographies.append(biography)
            
    return biographies

def process_biograpy(biography):
    name = biography["Name"]
    startPage = biography["StartPage"]

    with open('./DataBase/raw_txt/{}-{}.txt'.format(startPage, name), 'r') as f:
        text = f.read()

    #
    text, footnote_indices = process_text(text)

    #
    content, footnote = distinguish_footnote(text)

    #
    content = paragraph_clarify(content)
    footnote = paragraph_clarify(footnote)

    #
    process_footnote(footnote, biography)

    #
    content = process_content(content, biography, footnote_indices)

    # Output
    with open('./DataBase/mature_txt/{}-{}.txt'.format(startPage, name), 'w') as f:
        f.write(content)
    with open('./DataBase/metaData/{}-{}.json'.format(startPage, name), 'w') as f:
        json.dump(biography, f)

def process_text(text):
    #
    match = re.search(r'^(第\w章)　(\w+)$', text, flags=re.MULTILINE)
    if match: #
        chapter_th = match[1]
        category   = match[2]
        text = text.replace("{}　{}\n".format(chapter_th, category), "")
        text = text.replace("{}\n{}\n".format(category, chapter_th), "")

    #
    text = re.sub(r'^(\d) (\d) (\d)$', '\g<1>Ä\g<2>Ä\g<3>', text ,flags=re.MULTILINE)
    text = re.sub(r'([a-zA-Z,]) ([a-zA-Z,])', '\g<1>Ä\g<2>', text)
    text = re.sub(r'(\n\d+) ', '\g<1>Ä', text)
    text = text.replace(" ","")
    text = text.replace("Ä", " ")

    #
    footnote_indices = re.findall(r'\n(\d+) \w\w', text)

    return text, footnote_indices

def distinguish_footnote(text):
    page_s = re.split(r'\d \d \d', text)
    content_part_s = []
    footnote_part_s = []
    for page in page_s:
        cut_at = math.inf

        match = re.search(r'^\d+ ', page , flags=re.MULTILINE)
        if match:
            mStart, mEnd = match.span()
            cut_at = mStart

        match = re.search(r'^.+，(頁[\d-]+|第[\d-]+版)。$',page ,flags=re.MULTILINE)
        if match:
            mStart, mEnd = match.span()
            cut_at = min(mStart, cut_at)

        if cut_at is not math.inf:
            content_part = page[:cut_at]
            footnote_part = page[cut_at:]
            content_part_s.append(content_part)
            footnote_part_s.append(footnote_part)
        else:
            content_part_s.append(page)
            
    content_text = "".join(content_part_s)
    footnote_text = "".join(footnote_part_s)

    return content_text, footnote_text

def paragraph_clarify(text):
    text = text.replace("。\n", "Å")
    text = text.replace("\n", "")
    text = text.replace("Å", "。\n\n")

    return text

def process_footnote(footnote, biography):
    footnote = footnote[:-2]
    f_lines = footnote.split('\n\n')
    biography["Footnotes"] = list(map(lambda line: line.split(" "), f_lines))

def process_content(content, biography, footnote_indices):
    name = biography["Name"]
    
    #
    for index in footnote_indices:
        # test if behind people name
        content = content.replace("{}{}（".format(name, index), "{}（".format(name))
        content = re.sub("([。，])" + index, r'\g<1>', content)

    #
    match = re.search(r'（([\w、]+)撰寫?）', content, flags=re.MULTILINE) # $
    author_line = match[0]
    biography["Authors"] = match[1].split("、")
    content = content.replace(author_line, "")

    #
    reg = name + "（(.+，)?([\d?.]*)-([\d?.]*)）"
    title = re.search(reg, content, flags=re.MULTILINE)
    if len(title.groups()) == 2:
        biography["Birth"] = title[1]
        biography["Death"] = title[2]
    else:
        biography["Alias_s"].append(title[1])
        biography["Birth"] = title[2]
        biography["Death"] = title[3]
    
    content = content.replace(title[0], "")
    return content

def output_names(biographies):
    names = []
    for biography in biographies:
        names.append(biography["Name"])
        
    with open(os.getcwd() + '/DataBase/tmp/names.json', 'w') as f:
        json.dump(names, f) # 把names 變成json 檔案儲存

if __name__ == "__main__":
    main()
