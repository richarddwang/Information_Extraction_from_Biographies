import os
import re
import json
from functools import reduce
from itertools import product
from Utilities import parallelly_process
# jieba
import jieba.posseg
jieba.set_dictionary('./Tools/dict.txt.big')
jieba.load_userdict('./Tools/Appendix-Names.dict.txt') #
jieba.load_userdict('./Tools/Biographee-Names.dict.txt') #
# stanford
from stanfordcorenlp import StanfordCoreNLP
nlp = StanfordCoreNLP('./Tools/stanford-corenlp-full-2018-02-27', lang='zh') #
#Simplified and Traditional Chinese
from opencc import OpenCC
toTrad = OpenCC("s2t")
toSimp = OpenCC("t2s")
# DataBase
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"
db.people.remove()
db['people'] # create collection "people" if not exist

# Tools and GLOBAL VARIABLES
with open('./Tools/Hundred-Family-Surnames.json', 'r', encoding='utf-8') as f:
    CHINESE_SURNAMES = json.load(f)
with open('./Tools/Japanese-Surnames-in-zhTW.json', 'r', encoding='utf-8') as f:
    JAPANESE_SURNAMES = json.load(f)
SURNAMES = set(CHINESE_SURNAMES + JAPANESE_SURNAMES)
with open('./Tools/Taiwanese-Place-Names.json', 'r', encoding='utf-8') as f:
    PLACE_NAMES = json.load(f)
with open('./Tools/Mainland-Place-Names.json', 'r', encoding='utf-8') as f:
    PLACE_NAMES += json.load(f)
# elements in the same list may have only one
# by length : the fronter in re | the prefer
GIRL_ORDER_CHILD = ["長女", "次女", "三女", "四女", "五女", "六女", "七女", "八女", "九女", "十女", "么女", "幼女", "獨女"]
BOY_ORDER_CHILD = ["長子", "次子", "三子", "四子", "伍子", "五子", "六子", "七子", "八子", "九子", "十子", "么子", "么兒", "幼子", "獨子", "長男", "次男", "三男", "四男", "伍男", "五男", "六男", "七男", "八男", "九男", "十男", "么男",]
GIRL_CHILD_CHARS = ["女兒", "女",]
BOY_CHILD_CHARS = ["兒子", "子", "兒",]
#
MAN_PARENT_CHARS = ["父親", '父', "爹", "爸",]
WOMAN_PARENT_CHARS = ["母親", '母', "娘", "媽",]
OTHER_PARENT_CHARS = ["乾爸", "乾媽", "乾爹", "乾娘", "繼父", "繼母", '祖父', '祖母',]
SMALL_BROTHER_ORDER = ["大弟", "二弟", "三弟"]
SMALL_BROTHER_CHARS = ["弟弟", "弟"]
BIG_BROTHER_ORDER = [""]
WOMAN_SPOUSE_CHARS = ["妻為", "妻過", "妻子", "娶", "妻"]
MAN_SPOUSE_CHARS = ["丈夫為", "丈夫", "夫為" , "夫"]
OTHER_CHILD_CHARS = ["乾女兒", "乾兒子", "乾孫子", ]
GRAND_CHILD_ORDER = ["長孫", "次孫",]
GRAND_CHILD_CHARS = ["孫子", "孫"]

KINSHIP_CHARS = GIRL_ORDER_CHILD + BOY_ORDER_CHILD + GRAND_CHILD_ORDER + GIRL_CHILD_CHARS + BOY_CHILD_CHARS + GRAND_CHILD_CHARS + MAN_PARENT_CHARS + WOMAN_PARENT_CHARS + OTHER_PARENT_CHARS + MAN_SPOUSE_CHARS + WOMAN_SPOUSE_CHARS


def main():
    try:
        biographies = list(db.biographies.find())
        results = parallelly_process(extract_names_from_biograpies, divide_param=biographies)
        names_s, alias_pairs_s = list(zip(*results)) #
        names = reduce(lambda set1, set2: set1 | set2, names_s) # '|' is set union
        alias_tuples = reduce(lambda set1, set2: set1 | set2, alias_pairs_s)
        
        initialize_people(names, alias_tuples)
        
    finally:  # whether any error occur in main, we need to shut down server to save memory 
        nlp.close()

def extract_names_from_biograpies(biographies):
    total_names = set()
    total_alias_tuples = set()
    for biography in biographies:
        startPage = str(biography['StartPage'])
        name = biography['Name']
        with open('./DataBase/mature_txt/{}-{}.txt'.format(startPage, name), 'r', encoding='utf-8') as f:
            text = f.read()

        names, alias_tuples = extract_names_from_biograpy(text, biography)
        total_names = total_names | names # set union
        total_alias_tuples = total_alias_tuples | alias_tuples # set union

    return total_names, total_alias_tuples

def extract_names_from_biograpy(text, biography):
    names_jieba = get_names_jieba(text)
    names_stanford = get_names_stanford(text)
    names_kinship, kinship_alias_tuples = get_names_kinship(text, biography['Name'])
    names = names_jieba | names_stanford | names_kinship # set union
    names = process_and_filter_names(names)

    eng_alias_tuples = get_englishNames(text, names)
    other_alias_tuples = get_otherNames(text, biography['Name'])
    alias_tuples = set()
    for (name, aliasType, alias) in (eng_alias_tuples | other_alias_tuples  | kinship_alias_tuples):
        if name in names:
            alias_tuples.add( (name, aliasType, alias) )

    output_ner_result_for_check(biography, names, alias_tuples, names_jieba, names_stanford)
    
    return (names, alias_tuples)

def get_names_jieba(text):
    tokens = jieba.posseg.cut(text)
    names = set()
    for name, tag in tokens:
        if tag == "nr":
            names.add(name)
            
    return names

def get_names_stanford(text):
    text = toSimp.convert(text)
    entities = nlp.ner(text)
    names = set()
    for (name, label) in entities :
        if label == 'PERSON':
            names.add(toTrad.convert(name))
            
    return names

def get_names_kinship(text, biographee_name):
    names_parent, parent_alias_tuples = get_names_parent(text)
    names_child, child_alias_tuples = get_names_child_and_spouse(text, biographee_name)
    names_kinship = names_parent | names_child
    kinship_alias_tuples = set()
    for (name, aliasType, alias) in parent_alias_tuples | child_alias_tuples:
        if alias is None:
            kinship_alias_tuples.add( (name, "親屬關係暫存", biographee_name+":"+aliasType) )
        else:
            kinship_alias_tuples.add( (name, aliasType, alias) )
            
    return names_kinship, kinship_alias_tuples

def get_names_parent(text):
    names_parent = set()
    parent_alias_tuples = set()
    # Parent
    first_paragraph = text.split("\n\n")[0]
    man_parent_names, man_parent_alias_tuples = get_kin_name("|".join(MAN_PARENT_CHARS), first_paragraph, "父")
    woman_parent_names, woman_parent_alias_tuples = get_kin_name("|".join(WOMAN_PARENT_CHARS), first_paragraph, "母")
    names_parent |= (man_parent_names | woman_parent_names)
    parent_alias_tuples |= (man_parent_alias_tuples | woman_parent_alias_tuples)
    # Other Parents
    for other_parent_kinship in OTHER_PARENT_CHARS:
        names_other_parent, other_parent_alias_tuples = get_kin_name(other_parent_kinship, text, other_parent_kinship)
        names_parent |= names_other_parent
        parent_alias_tuples |= other_parent_alias_tuples
        
    return names_parent, parent_alias_tuples
    
    
def get_kin_name(identifier, text, kinship):
    # get name
    match = re.search(r'[。，:]({})(\w+?)[是。為，（在、務\(\<\:]'.format(identifier), text)
    if match is None:
        return set(), set()
    name_candidate = match[2]
    surname = get_surname(name_candidate)
    if kinship not in ["女兒", "兒子", ] and surname is None:
        return set(), set()
    if len(name_candidate) > 4:
        first_word, tag = list(jieba.posseg.cut(name_candidate))[0]
        if tag.startswith("n"): # len filter
            name = first_word
        else:
            return set(), set()
    else:
        name = name_candidate
        
    #
    alias_tuples = set()
    #
    match2 = re.search(r'{}{}（([a-zA-Z].+?)）'.format(match[1], match[2]), text)
    if match2 is not None:
        match3 = re.search(r'[a-zA-Z ]+', match2[1])
        if kinship in ["女兒", "兒子", ]:
            name = "💗" + name
        alias_tuples.add( (name, "英文名", match3[0]) )
    #
    alias_tuples.add( (name, kinship, None) )

    names = set()
    names.add(name)
    return names, alias_tuples    

def get_surname(name):
    for surname in SURNAMES:
        if name.startswith(surname):
            return surname
    return None

def get_names_child_and_spouse(text, biographee_name):
    splits = text.split("\n\n")
    if len(splits) >= 3:
        paragraph = "\n\n".join([splits[-2], splits[-1]])
    else:
        paragraph = splits[-1]
    
    #
    man_spouse_names, man_spouse_alias_tuples = get_kin_name("|".join(MAN_SPOUSE_CHARS), paragraph, "夫")
    woman_spouse_names, woman_spouse_alias_tuples = get_kin_name("|".join(WOMAN_SPOUSE_CHARS), paragraph, "妻")

    #
    if len(woman_spouse_names) == 1:
        isMan = True
    elif len(man_spouse_names) == 1:
        isMan = False
    else:
        isMan = True
        
    if isMan:
        family_name = get_surname(biographee_name)
    else:
        man_spouse_name = list(man_spouse_names)[0]
        if man_spouse_name is None:
            family_name = get_surname(biographee_name)
        else:
            family_name = get_surname(man_spouse_name)

    #
    girl_child_names = set() # a= b =set() is not what i want
    girl_child_alias_tuples = set()
    for girl_order_child in GIRL_ORDER_CHILD:
        girl_order_child_names, girl_order_child_alias_tuples = get_kin_name(girl_order_child, paragraph, "女兒")
        girl_child_names |= girl_order_child_names
        girl_child_alias_tuples |= girl_order_child_alias_tuples

    #
    boy_child_names = set()
    boy_child_alias_tuples = set()
    for boy_order_child in BOY_ORDER_CHILD:
        boy_order_child_names, boy_order_child_alias_tuples = get_kin_name(boy_order_child, paragraph, "兒子")
        boy_child_names |= boy_order_child_names
        boy_child_alias_tuples |= boy_order_child_alias_tuples

    # Continuous
    # if Continuous, there must be yu you
    match = re.search(r'育有\w+?[，。：（]', paragraph)
    if match is None:
        notFound_kinship = None
    else:
        if len(boy_child_names)==0 or len(girl_child_names)==0:
            if "女" in match[0] and "子" in match[0]:
                notFound_kinship = "兒女"
            elif "女" in match[0]:
                notFound_kinship = "女兒"
            elif "子" in match[0] and len(boy_child_names)==0:
                notFound_kinship = "兒子"
            else:
                notFound_kinship = None
        elif len(boy_child_names)==0 and "子" in match[0]:
            notFound_kinship = "兒子"
        elif len(girl_child_names)==0 and "女" in match[0]:
            notFound_kinship = "女兒"
        else:
            notFound_kinship = None
        
    continuous_child_names = set()
    continuous_child_alias_tuples = set()
    if notFound_kinship is not None:
        continuous_child_names, continuous_child_alias_tuples = get_continuous_child_names(paragraph, notFound_kinship)

    #
    child_names = girl_child_names | boy_child_names | continuous_child_names
    child_alias_tuples = girl_child_alias_tuples | boy_child_alias_tuples | continuous_child_alias_tuples
    # bouzu not surname, but it is ok cause bouzu often don't have children
    child_names = prepend_family_name_to_childs(child_names, family_name)
    child_alias_tuples = prepend_family_name_to_childs(child_alias_tuples, family_name)

    return (child_names | man_spouse_names | woman_spouse_names), (child_alias_tuples | man_spouse_alias_tuples | woman_spouse_alias_tuples)
        
def get_continuous_child_names(text, kinship):
    match = re.search(r'育有?(\d子)?(\d女)?(.*?)(。|，)', text)
    if match is None:
        return set(), set()

    if match[3] is not "":
        unchecked_names = match[3].split("、")
    else:
        match2 = re.search(r'(.+?)(。|，)', text[match.end():])
        if match2 is None:
            return set(), set()
        match3 = re.search(r'(為|是)(：|：)?(.+)', match2[1])
        if match3 is not None:
            unchecked_names = match3[3].split("、")
        else:
            unchecked_names = match2[1].split("、")

    names = set()
    alias_tuples = set()
    for unchecked_name in unchecked_names:
        #
        if unchecked_name.startswith("子"):
            kinship = "兒子"
            unchecked_name = unchecked_name[1:]
        elif unchecked_name.startswith("女"):
            kinship = "女兒"
            unchecked_name = unchecked_name[1:]
        else:
            pass
        # 
        detectParen_match = re.search(r'(.+)（(.+?)）', unchecked_name)
        if detectParen_match is not None:
            eng_match = re.match(r'[a-zA-Z ]+', detectParen_match[2])
            if eng_match is not None:
                unchecked_name = "💗" + detectParen_match[1] # assume if have english name, we don't need to preprent family name
                english_name = eng_match[0]
                alias_tuples.add( (unchecked_name, "英文名", english_name) )
            else:
                unchecked_name = detectParen_match[1]

        names.add(unchecked_name)
        alias_tuples.add( (unchecked_name, kinship, None) )            

    return names, alias_tuples

def prepend_family_name_to_childs(names_or_aliasTuples, family_name):
    if family_name is None:
        return names_or_aliasTuples
    
    result = set()
    for element in names_or_aliasTuples:
        if isinstance(element, str):
            name = element
        else:
            name = element[0]

        prepend_executed = False
        if name.startswith("💗"):
            prepended_name = name[1:]
        elif name.startswith(family_name):
            prepended_name = name
        else:
            prepended_name = family_name + name
            prepend_executed = True

        if isinstance(element, str):
            result.add(prepended_name)
        else:
            result.add( (prepended_name, element[1], element[2]) )
            if prepend_executed:
                result.add( (prepended_name, "原形", name) )

    return result
    
def process_and_filter_names(names):
    #
    first_processed_names = set()
    for name in names:
        
        # filter
        if( 1 < len(name) <= 4 # 名字至少兩個字
           and name[-1]!='寺' # 篩掉部分標注錯誤的情
           and name not in ["田野", "伯父", "伯母", "元配", "高中生"] 
           and re.match('[a-zA-Z]',name) == None
           and name not in PLACE_NAMES
           and not (name[-1]=="人" and name[:-1] in PLACE_NAMES)
        ):
            for surname in SURNAMES - set(KINSHIP_CHARS):
                if name.startswith(surname):
                    first_processed_names.add(name)
                    break # tanaka talou
                
    #
    first_processed_names = list(first_processed_names)
    second_processed_names = set()
    for name1 in first_processed_names:
        not_substr_of_any = True
        for name2 in first_processed_names:
            if name1 != name2 and name1 in name2:
                not_substr_of_any = False
                break
        if not_substr_of_any:
            second_processed_names.add(name1)
                
    return second_processed_names 

def get_englishNames(text, names):
    engName_tuples = set()
    for name in names:
        match = re.search(r'{}（([a-zA-Z].*?)）'.format(name),text)
        if match != None :
            match2 = re.search(r'[a-zA-Z ]+', match[1]) # Irene Joliot-Curie，1897-1956
            engName_tuples.add((name, "英文名", match2[0]))
    return engName_tuples

def get_otherNames(text, biographee_name):
    '''
    傳主別名一般出現在第一句話，句式為“……人，別名/字/筆名/本名/原名/俗名/受洗名……。”
    examples:
    “俗名李林泉，號俊英。”
    “湖南湘鄉人。原名希箕，又名漢勳，筆名丁一、平、小白、舍我。”
    '''
    otherNames = set()
    aliasTypes = ['字','號','別名','筆名','本名','原名','俗名','受洗名','又名', '藝名', '小名']
    sent = re.search('.*?。',text ).group() #第一句 
    for aliasType in aliasTypes:
        match = re.search('{}(.*?)[，。]'.format(aliasType),sent)
        if match != None:
            alias_s = match[1].split("、")
            for alias in alias_s:
                otherNames.add( (biographee_name, aliasType, alias) )
    return otherNames

def output_ner_result_for_check(biography, names, alias_tuples, names_jieba, names_stanford):
    try:
        os.makedirs('./DataBase/ner_result')
    except FileExistsError: # directory is exist
        pass

    result = """
Names:
{}
    
Alias_s:
{}
    
-------------------------------------------------------
Jieba:
{}
    
Stanford:
{}
    """.format(
        "\n".join(names),
        "\n".join(  map(lambda tpl: "{} {} {}".format(tpl[0], tpl[1], tpl[2]), alias_tuples)  ),
        "\n".join(names_jieba),
        "\n".join(names_stanford),)
    
    with open('./DataBase/ner_result/{}-{}.txt'.format(biography['StartPage'], biography['Name']), 'w', encoding='utf-8') as f:
        print(result, file=f)
        

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
    
