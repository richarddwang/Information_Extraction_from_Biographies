import re
import json
import os
import subprocess

def main():
    #
    biographies = get_biographies()
    for (i, biography) in enumerate(biographies):
        text = process_text(biographies, i)
        name = biographies[i]["Name"]
        with open("./DataBase/mature_txt/{}.txt".format(name), 'w') as f:
            f.write(text)

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

def process_text(biographies, i):
    name = biographies[i]["Name"]

    with open('./DataBase/raw_txt/{}.txt'.format(name), 'r') as f:
        text = f.read()

    #
    match = re.search(r'^(第\w章)　(\w+)$', text, flags=re.MULTILINE)
    if match: #
        chapter_th = match[1]
        category   = match[2]
        text = text.replace("{}　{}\n".format(chapter_th, category), "")
        text = text.replace("{}\n{}\n".format(category, chapter_th), "")

    #
    page_s = re.split(r'\d \d \d', text)[1:]
    all_comment_indices = []
    page_content_s = []
    for page in page_s:
        comment_indices = re.findall(r'\n(\d+) ', page)
        all_comment_indices += comment_indices
        if comment_indices: #
            splits = re.split(r'\n\d+ ', page)
            content = splits[0]
            footnotes = splits[1:]
            biographies[i]["footnotes"] = zip(comment_indices, footnotes)
            page_content_s.append(content)
        else:
            page_content_s.append(page)
    text = ''.join(page_content_s)
    
    #
    for index in all_comment_indices:
        # test if behind people name
        text = text.replace("{} {}（".format(name, index), "{}（".format(name))
        text = re.sub("([。，）])" + index, r'\g<1>', text)

    # deal with newline
    text = re.sub(r'。\n', "。。。", text, re.MULTILINE)
    text = re.sub(r'\n', "", text)
    text = re.sub(r'。。。', "。\n\n", text, re.MULTILINE)

    # remove space before number
    text = re.sub(r' +(\d)', r'\g<1>', text)

    # remove author
    match = re.search(r"（([\w+、]+)撰寫?）", text, flags=re.MULTILINE) # $
    author_line = match[0]
    authorGroup = match[1]
    text = text.replace(author_line, "")
    biographies[i]["Authors"] = authorGroup.split("、")

    # remove title of biography, and get birth and death
    reg = name + "（(.+，)?([\d?.]*)-([\d?.]*)）"
    title = re.search(reg, text, flags=re.MULTILINE)
    if len(title.groups()) == 2:
        biographies[i]["Birth"] = title[1]
        biographies[i]["Death"] = title[2]
    else:
        biographies[i]["Alias_s"].append(title[1])
        biographies[i]["Birth"] = title[2]
        biographies[i]["Death"] = title[3]
    
    text = text.replace(title[0], "")

    return text

def output_names(biographies):
    names = []
    for biography in biographies:
        names.append(biography["Name"])
        
    with open(os.getcwd() + '/DataBase/tmp/names.json', 'w') as f:
        json.dump(names, f) # 把names 變成json 檔案儲存

if __name__ == "__main__":
    main()
