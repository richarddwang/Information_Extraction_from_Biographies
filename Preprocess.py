import re
import json
import os
import subprocess
import math
import argparse

# DataBase
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"

def main():
    # normalize傳記文本，並同時存一些傳記資訊
    for biography in db.biographies.find():
        process_biograpy(biography)

# Global variables
OUTPUT_MATURE_TXT_PER_BIOGRAPHY = True
        
        
def process_biograpy(biography):
    name = biography["Name"]
    startPage = biography["StartPage"]

    with open('./DataBase/raw_txt/{}-{}.txt'.format(startPage, name), 'r', encoding='utf-8') as f:
        text = f.read()

    # 文本整體的處理，並找出附註的小數字們
    text = remove_chapter(text)

    # 找出每條附註前面會有的小數字們
    footnote_indices = re.findall(r'\n(\d+) [^\d][^\d]', text)
    
    # 將內文和附註切開
    content, footnote = distinguish_footnote(text)

    # 去除內文中的附註小數字
    content = remove_footnoteNumber(content, name, footnote_indices)

    # 清掉所有不需要的空格
    content = remove_unneedSpace(content)
    footnote = remove_unneedSpace(footnote)
    
    # 處理newline，內文分出段落
    content = paragraph_clarify(content)
    footnote = paragraph_clarify(footnote)

    # 將footnote 處理後加進傳記的資訊裡
    process_footnote(footnote, biography)

    # 針對內容作處理
    content = process_content(content, biography, footnote_indices)

    # Output
    if OUTPUT_MATURE_TXT_PER_BIOGRAPHY is True:
        output_mature_txt(startPage, name, content)
        
    db.biographies.save(biography) # save into collection and replace the document with the same "_id" (original document)

def remove_chapter(text):
    # 清掉章節標題
    match = re.search(r'^(第\w章)　(\w+)$', text, flags=re.MULTILINE)
    if match: # 有可能沒有章節標題， 所以要先看有沒有找到
        chapter_th = match[1]
        category   = match[2]
        text = text.replace("{}　{}\n".format(chapter_th, category), "")
        text = text.replace("{}\n{}\n".format(category, chapter_th), "")    

    return text

def distinguish_footnote(text):
    # 先依頁碼分成多個頁
    page_s = re.split(r'^\d \d \d$', text, flags=re.MULTILINE)
    content_part_s = [] # 各頁的內文部分
    footnote_part_s = [] # 各頁的附註部分
    for page in page_s:
        cut_at = math.inf # 內文和附註的切割點

        # 利用附註小數字的格式找出本頁第一條附註位置
        match = re.search(r'^\d+ ', page , flags=re.MULTILINE)
        if match:
            mStart, mEnd = match.span()
            cut_at = mStart

        # 一條附註可能被斷到兩頁，則下一頁的附註一開始就是上一頁的附註的接續，沒有附註小數字
        # 看附註結尾來辨識出在下一頁開頭的接續的附註(不是完全可靠)
        match = re.search(r'^.+，(頁[\d\- ]+|第[\d\- ]+版)。$',page ,flags=re.MULTILINE)
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
            
    content_text = "".join(content_part_s) # 把各頁的內文部分結合成內文
    footnote_text = "".join(footnote_part_s) # 把各頁的附註部分結合成附註
    
    return content_text, footnote_text

def remove_footnoteNumber(content, name, footnote_indices):
    # 第一種附註小數字出現的場合
    content = re.sub(name+' ?'+str(footnote_indices[0])+' ?（', "{}（".format(name),content , 1)
    # 第二種附註小數字出現的場合
    for index in footnote_indices[1:]:  
        content = re.sub("([。，])" + index, r'\g<1>', content, count=1)

    return content

def remove_unneedSpace(text):
    # 先把需要的空格轉成另一個字符記錄起來，清完空格再回復原狀
    text = re.sub(r'([a-zA-Z,）（]) ([a-zA-Z,）（])', '\g<1>Ä\g<2>', text)
    text = re.sub(r'^(\d+) ', '\g<1>Ä', text, flags=re.MULTILINE)
    text = text.replace(" ","")
    text = text.replace("Ä", " ")

    return text

def paragraph_clarify(text):
    # 因為句號後面換行的通常是一段落的結尾(但也可能不是)
    text = text.replace("。\n", "Å")
    text = text.replace("\n", "")
    text = text.replace("Å", "。\n\n")

    return text

def process_footnote(footnote, biography):
    footnote = footnote[:-2] # 去掉最後的兩個newline
    f_lines = footnote.split('\n\n') # 這樣最後就不會多一個空的split，各條附註分開
    # There may be footnot line without numbering, see pdf 194,195
    insert_pos = 0
    for f_line in f_lines:
        pair = f_line.split(" ")
        if len(pair)!=1:
            biography['Footnotes'].append({'Numbering': pair[0], 'FootnoteText': pair[1],})
            insert_pos += 1
        else:
            biography['Footnotes'][insert_pos-1]['FootnoteText'] += ("\n" + f_line)
            
def process_content(content, biography, footnote_indices):
    name = biography["Name"]    

    # 從內文去掉傳記撰者，並保存在傳記資訊
    match = re.search(r'（([\w、]+)撰寫?）', content, flags=re.MULTILINE) # $
    author_line = match[0]
    biography["Authors"] = match[1].split("、")
    content = content.replace(author_line, "")

    # 從內文去掉傳記標題，保存別名， 生日日期，死亡日期
    reg = name + "（(.+，)?([\d?.]*)-([\d?.]*)）"
    title = re.search(reg, content, flags=re.MULTILINE)
    if len(title.groups()) == 2:
        biography["Birth"] = title[1] # group1
        biography["Death"] = title[2] # group2
    else:
        biography["Alias_s"].append(title[1])
        biography["Birth"] = title[2] 
        biography["Death"] = title[3]
    content = content.replace(title[0], "") # replace Whole match with empty string
    
    return content

def output_mature_txt(startPage, name, content):
    try:
        os.makedirs('./DataBase/mature_txt')
    except FileExistsError: # directory is exist
        pass
    
    with open('./DataBase/mature_txt/{}-{}.txt'.format(startPage, name), 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    # 用ArgumentParser 來定義無論optional 和 position arguments(這裡只定義了optional)
    # 然後用這些定義去parse command line 的arguments, 得到每個option arguments 後的arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-n', '--no-output',
                           action='store_false', # 
                           dest='whether_output', # 用什麼名稱access 此option後arguments, 預設是option名
                           help="Output the result for the sake of getting insights.", # -h 裡的敘述
    )
    args = argParser.parse_args()

    OUTPUT_MATURE_TXT_PER_BIOGRAPHY = args.whether_output
    
    main()
