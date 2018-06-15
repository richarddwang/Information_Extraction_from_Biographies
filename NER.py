import os
import re
import argparse
from functools import reduce
from Utilities import parallelly_process
# jieba
import jieba.posseg
jieba.set_dictionary('./Tools/dict.txt.big')
jieba.load_userdict('./Tools/names_appendix.dict.txt')
jieba.load_userdict('./Tools/Taiwanese_place_names.txt')
# stanford
from stanfordcorenlp import StanfordCoreNLP
nlp = StanfordCoreNLP('./Tools/stanford-corenlp-full-2018-02-27', lang='zh') #
# simplified and traditional Chinese
from hanziconv import HanziConv
toSimplified = HanziConv.toSimplified
toTraditional = HanziConv.toTraditional
# DataBase
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"
db['people'] # create collection "people" if not exist

def main():
    try:
        temporarily_enhance_jieba_dict()
        
        biographyIDs = db.biographies.distinct('_id')    
        results = parallelly_process(biographyIDs, 4, extract_names_from_biograpies)
        names_s, alias_pairs_s = list(zip(*results)) #
        names = reduce(lambda set1, set2: set1 | set2, names_s) # '|' is set union
        alias_tuples = reduce(lambda set1, set2: set1 | set2, alias_pairs_s)
        
        initialize_people(names, alias_tuples)
        
    finally:  # whether any error occur in main, we need to shut down server to save memory 
        nlp.close()

def extract_names_from_biograpies(biographyIDs):
    total_names = set()
    total_alias_tuples = set()
    for ID in biographyIDs:
        biography = db.biographies.find_one(filter={'_id':ID})
        startPage = str(biography['StartPage'])
        name = biography['Name']
        with open('./DataBase/mature_txt/{}-{}.txt'.format(startPage,name), 'r', encoding='utf-8') as f:
            text = f.read()

        names, alias_tuples = extract_names_from_biograpy(text, name)
        total_names = total_names | names # set union
        total_alias_tuples = total_alias_tuples | alias_tuples # set union

    return total_names, total_alias_tuples

def extract_names_from_biograpy(text, biographee_name):
    biographee_lastName = get_lastName(biographee_name)

    names_jieba = get_names_jieba(text, biographee_lastName)
    names_stanford = get_names_stanford(text)
    names = names_jieba | names_stanford # set union

    alias_tuples = get_englishNames(text, names)
    alias_tuples = alias_tuples | get_otherNames(text, biographee_name) # set union

    output_ner_result(biographee_name, names, alias_tuples)
    
    return (names, alias_tuples)
    
def get_lastName(name):
    compoundNames = ["歐陽"] # 可添加
    return name[:2] if name[:2] in compoundNames else name[0]

def get_names_jieba(text, biographee_lastName):
    tokens = jieba.posseg.cut(text)
    names = set()
    children = ['女','孫','子']
    parents = ['父','母']
    for name, flag in tokens:
        # 名字至少兩個字，篩掉部分標注錯誤的情況
        if flag == "nr" and len(name) > 1 and re.match('[A-Z]',name) == None and name[-1]!='寺':  
            char_before = re.search(r'.(?={})'.format(name),text)
            if char_before == None:
                names.add(name)
            # 如果前一個字是“子”“女”等
            elif name[0] != biographee_lastName and len(name) < 3 and char_before.group() in children:  
                names.add(biographee_lastName + name)  # 冠傳主的姓。問題：如果傳主是女性怎麽辦？如：陳靜秋
            # 如果被斷成“子某某”，換成傳主的姓
            elif name[0] in children:  
                names.add(biographee_lastName + name[1:])
            #如果被切成“母某某”，切掉第一個字
            elif name[0] in parents:  
                names.add(name[1:])
            else:
                names.add(name)
    return names

def get_names_stanford(text):
    names = set()
    text = toSimplified(text)
    entities = nlp.ner(text)
    for entity in entities :
        if entity[1] == 'PERSON' \
           and len(entity[0]) > 1 \
           and entity[0][-1]!='寺' \
           and re.match('[A-Z]',entity[0]) == None:  #不要英文名
            names.add(toTraditional(entity[0]))  
    
    return names 

def get_englishNames(text, names):
    engName_tuples = set()
    brackets = '（[A-Z].*?）'
    for name in names:
        rlt = re.search('{}{}'.format(name,brackets),text)
        if rlt != None :
            rlt = re.split('[（）]',rlt.group())
            engName_tuples.add((name,"英文名" ,rlt[1]))
    return engName_tuples

def get_otherNames(text, biographee_name):
    '''
    傳主別名一般出現在第一句話，句式為“……人，別名/字/筆名/本名/原名/俗名/受洗名……。”
    examples:
    “俗名李林泉，號俊英。”
    “湖南湘鄉人。原名希箕，又名漢勳，筆名丁一、平、小白、舍我。”
    '''
    nickNames = set()
    types = ['字','號','別名','筆名','本名','原名','俗名','受洗名','又名', '藝名', '小名']
    sent = re.search('.*?。',text ).group() #第一句 
    for typ in types:
        rlt = re.search('{}.*?[，。]'.format(typ),sent)
        if rlt != None:
            rlt = re.split('{}|[，。]'.format(typ),rlt.group())
            nickNames.add((biographee_name, typ, rlt[1]))
    return nickNames

def output_ner_result(biographee_name, names, alias_tuples):
    try:
        os.makedirs('./DataBase/ner_result')
    except FileExistsError: # directory is exist
        pass

    results = list(alias_tuples) + list(map(lambda x: (x,"",""), names))

    with open('./DataBase/ner_result/{}.txt'.format(biographee_name), 'w', encoding='utf-8') as f:
        for tpl in results:
            print(tpl[0], tpl[1], tpl[2], file=f)

def temporarily_enhance_jieba_dict():
    names = db.biographies.distinct('Name')
    for name in names:
        jieba.add_word(name, tag='nr') # tag 是其詞性

def initialize_people(names, alias_tuples):
    aliasNames = set(map(lambda tpl: tpl[2], alias_tuples))
    names = names - aliasNames # set differentiation
    
    for name in names:
        db.people.find_and_modify(
            query={'Name':name,},
            update={'$set':
                    {'Name' : name,
                     'Alias_s' : [],
                     'Identities' : [],
                    }
            }, 
            upsert=True,
        )

    for alias_tuple in alias_tuples:
        alias_pair = {'type': alias_tuple[1], 'alias':alias_tuple[2]}
        db.people.find_and_modify(
            query={'Name':alias_tuple[0]},
            update={'$push': {'Alias_s' : alias_pair}},
        )

if __name__ == "__main__":    
    main()
    
