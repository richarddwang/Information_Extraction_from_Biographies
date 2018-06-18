import json
import re
import subprocess

def extract_appendix():
    command = 'java -jar ./Tools/pdfbox-app-1.8.13.jar ExtractText -encoding utf-8 -startPage 383 -endPage 412 ../../DataBase/社會與文化篇.pdf ../../tmp/names_appendix.txt'
    subprocess.run(command.split() )


def split_text():
    title = []
    with open ('../../tmp/names_appendix.txt', 'r', encoding='utf-8') as f:
        text = f.read()
        text = re.sub(r"\d \d \d\n|附錄　人物表\n|臺北市醫院名 院（所）長\n","", text)
    pattern = re.compile("[一二三四五六七八九]、.+一覽")
    titles= re.findall(pattern,text)
    pattern_ref = re.compile(r"資料來源|參考資料")
    references = re.findall(pattern_ref, text)
    texts = re.split(pattern,text)
    for i in range(1,len(texts)):
        clean_text = re.split(pattern_ref,texts[i])
        texts[i] = clean_text[0]
    return texts

def p1(texts):
    pattern_hospital = re.compile(r".+[院所][ \n]")
    hospitals = re.findall(pattern_hospital, texts[1])
    text_hospital = re.split(pattern_hospital,texts[1])
    for i in range(0,len(text_hospital)):
        text_hospital[i] = text_hospital[i].replace("\n","")
    text_hospital.pop(0)
    hospital_dean = {}
    str = re.compile("\w{0,6}")
    for i in range(0, len(hospitals)):
        dean_names = re.split("、", text_hospital[i])
        for name in dean_names:
            hospital_dean[name] = hospitals[i].strip()
    return hospital_dean

def p2(texts):
    rlg_grp_mgr = {}
    lines = re.split("\n",texts[2])
    for line in lines:
        items = re.split(" ",line)
        if items != ['']:
            mgrnames = re.split("、", items[1])
            for mgr in mgrnames:
                rlg_grp_mgr[mgr] = items[0]
    return rlg_grp_mgr

def p3(texts):
    poet_club_mgr = {}
    str = re.compile("(?<=、)\n")
    texts[3] = re.sub(r"(?<=、)\n","",texts[3])
    lines = lines = re.split("\n",texts[3])
    for line in lines:
        items = re.split(" ",line)
        if items != ['']:
            mgrnames = re.split("、", items[3])
            for mgr in mgrnames:
                poet_club_mgr[mgr] = items[0]
    return poet_club_mgr


def p456(texts):
    artists = {}
    texts_add = re.sub(r"屆／年度 得獎者 作品名","",texts[4]+texts[5])
    text_art = re.split(r"第.屆（....）|\n",texts_add) 
    for t in text_art:
        ts = re.split(" ", t)
        if ts[0] != '':
            artists[ts[0]] = "藝術家"
    texts[6] = re.sub(r"屆／年度 得獎者 作品名","",texts[6])
    text_art = re.split(r"\n",texts[6]) 
    for t in text_art:
        ts = re.split(" ", t)
        if ts[0] != '':
            artists[ts[1]] = "藝術家"
    return artists


def p7(texts):
    teachers ={}
    text_teacher= re.sub(r"學校名 臺籍教員姓名|.+學校","",texts[7])
    t = re.split("[、\n]", text_teacher)
    for name in t:
        if name != '':
            teachers[re.sub("\n|　","",name)] = "教員"
    return teachers


def p8(texts):
    prize_owner = {}
    pattern_owner = re.compile("\w+（\w+）")
    text_owners = re.findall(pattern_owner,texts[8])
    for t in text_owners:
        t = re.split("\W",t)
        prize_owner[t[0]] = t[1]
    return prize_owner


def p9(texts):
    excl_teachers = {}
    et_texts = re.sub("年代（民國） 姓名 任教科目 任教學校|\d \d \d","",texts[9])
    et_texts = re.split('\d\d\d?\n',et_texts)
    for et in et_texts:
        et = re.split(" |\n",et)
        if et[0] != '':
            excl_teachers[et[0]] = et[1]+"of"+et[2]
    return excl_teachers


def main():
    extract_appendix()
    texts = split_text()
    names = {}
    names = {**p1(texts),**p2(texts),**p3(texts),**p456(texts),**p7(texts),**p8(texts),**p9(texts)}
    with open('../Appendix-Names.dict.txt','w',encoding='utf-8') as f:
        for name in names:
            print(name, "nr", file=f) # get user_dict for jieba tokenizing


if __name__ == '__main__':
    main()

