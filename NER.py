import os
import re
import sys
import json
from functools import reduce
from Utilities import parallelly_process
# jieba
import jieba.posseg
jieba.set_dictionary('./Tools/dict.txt.big')
jieba.load_userdict('./Tools/Appendix-Names.dict.txt') #
jieba.load_userdict('./Tools/Biographee-Names.dict.txt') #
# stanford
from pycorenlp import StanfordCoreNLP
nlp = StanfordCoreNLP('http://localhost:9000')
#Simplified and Traditional Chinese
from opencc import OpenCC
toTrad = OpenCC("s2t")
toSimp = OpenCC("t2s")
# DataBase
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary" 
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

# 親屬關係的關鍵字
# 有順序的是都取
# 沒有順序是會按照元素順序來當優先順序取，所以長的要在前面，避免其substring也是元素且在前面的話，會優先取到那個substring
GIRL_ORDER_CHILD = ["長女", "次女", "三女", "四女", "五女", "六女", "七女", "八女", "九女", "十女", "么女", "幼女", "獨女"]
BOY_ORDER_CHILD = ["長子", "次子", "三子", "四子", "伍子", "五子", "六子", "七子", "八子", "九子", "十子", "么子", "么兒", "幼子", "獨子", "長男", "次男", "三男", "四男", "伍男", "五男", "六男", "七男", "八男", "九男", "十男", "么男",]
GIRL_CHILD_CHARS = ["女兒", "女",]
BOY_CHILD_CHARS = ["兒子", "子", "兒",]
MAN_PARENT_CHARS = ["父親", '父', "爹", "爸",]
WOMAN_PARENT_CHARS = ["母親", '母', "娘", "媽",]
OTHER_PARENT_CHARS = ["乾爸", "乾媽", "乾爹", "乾娘", "繼父", "繼母", '祖父', '祖母',]
SMALL_BROTHER_ORDER = ["大弟", "二弟", "三弟", "四弟", "五弟", "六弟", "七弟",]
SMALL_BROTHER_CHARS = ["弟弟", "弟"]
BIG_BROTHER_ORDER = ["大哥", "二哥", "三哥", "四哥", "五哥", "六哥", "七哥",]
BIG_BROTHER_CHARS = ["兄長", "哥哥", "兄"]
BIG_SISTER_ORDER = ["大姐", "二姐", "三姐", "四姐", "五姐", "六姐", "七姐",]
BIG_SISTER_CHARS = ["姐姐", "姐"]
SMALL_SISTER_ORDER = ["大妹", "二妹", "三妹", "四妹", "五妹", "六妹", "七妹",]
SMALL_SISTER_CHARS = ["妹妹", "妹"]
WOMAN_SPOUSE_CHARS = ["妻為", "妻過", "妻子", "娶", "妻"]
MAN_SPOUSE_CHARS = ["丈夫為", "丈夫", "夫為" , "夫"]
OTHER_CHILD_CHARS = ["乾女兒", "乾兒子", "乾孫子", ]
GRAND_CHILD_ORDER = ["長孫", "次孫",]
GRAND_CHILD_CHARS = ["孫子", "孫"]
# 親屬關係全部的關鍵字加起來
KINSHIP_CHARS = GIRL_ORDER_CHILD + BOY_ORDER_CHILD + GRAND_CHILD_ORDER + GIRL_CHILD_CHARS + BOY_CHILD_CHARS + GRAND_CHILD_CHARS + MAN_PARENT_CHARS + WOMAN_PARENT_CHARS + OTHER_PARENT_CHARS + MAN_SPOUSE_CHARS + WOMAN_SPOUSE_CHARS + BIG_SISTER_CHARS + BIG_SISTER_ORDER +BIG_BROTHER_CHARS + BIG_BROTHER_ORDER + SMALL_SISTER_CHARS + SMALL_SISTER_ORDER + SMALL_BROTHER_CHARS + SMALL_BROTHER_ORDER


def main():
    # 先淨空舊紀錄
    db.people.remove() # 因為當import 此python檔時，會把全部都eval一次，所以如果放在函式外的話，會在import 的同時把people 移除掉，糟糕..，所以要放在函式內。

    # 提領出所有傳記
    biographies = list(db.biographies.find())
    # 平行處理，將傳記裡的姓名提出來
    results = parallelly_process(extract_names_from_biograpies, divide_param=biographies)
    # 將平行處理的結果合回一個結果
    names_s, alias_pairs_s = list(zip(*results)) # 每個result 都是(names, alias_pairs) ### * ?
    names = reduce(lambda set1, set2: set1 | set2, names_s) # '|' is set union
    alias_tuples = reduce(lambda set1, set2: set1 | set2, alias_pairs_s)
    # 將擷取出的人名倒進資料庫裡
    initialize_people(names, alias_tuples)

def extract_names_from_biograpies(biographies):
    total_names = set()
    total_alias_tuples = set() # alias_tuple : (本名, 別名的類別, 別名)
    # 從各個傳記擷取名子並收集起來
    for biography in biographies:
        # 前置作業
        startPage = str(biography['StartPage'])
        name = biography['Name']
        book = biography['Book']
        with open('./DataBase/mature_txt/{}-{}-{}.txt'.format(book, startPage, name), 'r', encoding='utf-8') as f:
            text = f.read()
        # 擷取名子
        names, alias_tuples = extract_names_from_biograpy(text, biography)
        # 收集起來
        total_names = total_names | names # set union
        total_alias_tuples = total_alias_tuples | alias_tuples # set union

    return total_names, total_alias_tuples

# 從一個傳記中抽取名子
def extract_names_from_biograpy(text, biography):
    # 擷取名子
    names = set()
    # 傳主的名子當然也要算進去
    names.add(biography['Name'])
    # 用jieba 擷取出的名子
    names_jieba = get_names_jieba(text)
    # 用stanford ner 擷取出的名子
    names_stanford = get_names_stanford(text)
    # 用regex 擷取出來的親屬的名子
    names_kinship, kinship_alias_tuples = get_names_kinship(text, biography['Name'])
    # 統統合起來
    names |= (names_jieba | names_stanford | names_kinship) # set union
    # 一起過濾
    names = process_and_filter_names(names)

    # 擷取別名
    # 擷取英文別名
    eng_alias_tuples = get_englishNames(text, names)
    # 擷取其他種類的別名
    other_alias_tuples = get_otherNames(text, biography['Name'])
    # 蒐集本名真的是名子的別名tuple
    alias_tuples = set()
    for (name, aliasType, alias) in (eng_alias_tuples | other_alias_tuples  | kinship_alias_tuples):
        if name in names:
            alias_tuples.add( (name, aliasType, alias) )

    # 輸出for insight
    output_ner_result_for_check(biography, names, alias_tuples, names_jieba, names_stanford)

    # 回傳
    return (names, alias_tuples)

# 抓jieba 斷詞結果中tag是nr 的
def get_names_jieba(text):
    tokens = jieba.posseg.cut(text)
    names = set()
    for name, tag in tokens:
        if tag == "nr":
            names.add(name)
            
    return names

# 抓corenlp ner 中判別是PERSON的
def get_names_stanford(text):
    try:
        text = toSimp.convert(text)
        output = nlp.annotate(text, properties={
            'annotators': "tokenize, ssplit, pos, lemma, ner",
            'outputFormat': 'json',
        })
        names = set()
        for sent in output['sentences']:
            for entity in sent['entitymentions']:
                if entity['ner'] == 'PERSON':
                    entity_name = entity['text']
                    names.add(toTrad.convert(entity_name))
    except:
        print("Error {} while get_names_stanford, text is :\n{}".format(sys.exc_info()[0], text) )
        
    return names

# 抓親屬關係的名子
def get_names_kinship(text, biographee_name):
    # 抓小孩和配偶的名子
    names_childAndSpouse, childAndSpouse_alias_tuples = get_names_child_and_spouse(text, biographee_name)
    # 抓其他親屬關係的名子
    names_otherKinship, otherKinship_alias_tuples = get_otherKinship_names(text)
    # 合起來
    names_kinship = names_otherKinship | names_childAndSpouse
    # 有些alias tuple 是假的，拿來偷存兩人的關係，標注這些是假的再合起來
    kinship_alias_tuples = set()
    for (name, aliasType, alias) in otherKinship_alias_tuples | childAndSpouse_alias_tuples:
        if alias is None:
            kinship_alias_tuples.add( (name, "親屬關係暫存", biographee_name+":"+aliasType) )
        else:
            kinship_alias_tuples.add( (name, aliasType, alias) )
            
    return names_kinship, kinship_alias_tuples

def get_otherKinship_names(text):
    # 小孩和配偶以外的親屬通常都出現在第一段落
    first_paragraph = text.split("\n\n")[0]
    
    names = set()
    aliasTuples = set()
    # Parent
    man_parent_names, man_parent_aliasTuples = get_kin_name("|".join(MAN_PARENT_CHARS), first_paragraph, "父")
    woman_parent_names, woman_parent_aliasTuples = get_kin_name("|".join(WOMAN_PARENT_CHARS), first_paragraph, "母")
    names |= (man_parent_names | woman_parent_names)
    aliasTuples |= (man_parent_aliasTuples | woman_parent_aliasTuples)

    # Other Parents
    for otherParent_kinship in OTHER_PARENT_CHARS:
        names_otherParent, otherParent_aliasTuples = get_kin_name(otherParent_kinship, text, otherParent_kinship)
        names |= names_otherParent
        aliasTuples |= otherParent_aliasTuples

    # Siblings
    # 用沒有配輩份順序的下去搜
    bigBrother_names, bigBrother_aliasTuples = get_kin_name("|".join(BIG_BROTHER_CHARS), first_paragraph, "兄")
    smallBrother_names, smallBrother_aliasTuples = get_kin_name("|".join(SMALL_BROTHER_CHARS), first_paragraph, "弟")
    bigSister_names, bigSister_aliasTuples = get_kin_name("|".join(BIG_SISTER_CHARS), first_paragraph, "姐")
    smallSister_names, smallSister_aliasTuples = get_kin_name("|".join(SMALL_SISTER_CHARS), first_paragraph, "妹")
    names |= (bigBrother_names | smallBrother_names | bigSister_names | smallSister_names)
    aliasTuples |= (bigBrother_aliasTuples | smallBrother_aliasTuples | bigSister_aliasTuples | smallSister_aliasTuples)
    # 用有輩份順序的下去搜
    for (orders, kinship) in [(BIG_BROTHER_ORDER, "兄"), (SMALL_BROTHER_ORDER, "弟"), (BIG_SISTER_ORDER, "姐"), (SMALL_SISTER_ORDER, "妹")]:
        for order in orders:
            sibling_names, sibling_aliasTuples = get_kin_name(order, first_paragraph, kinship)
            names |= sibling_names
            aliasTuples |= sibling_aliasTuples
    
        
    return names, aliasTuples
    

def get_kin_name(identifier, text, kinship):
    # get name
    """
    通常的形式：
    標點符號 親屬關係關鍵詞 名子 標點符號
    標點符號間夾的也有可能是一句句子，例如「父江將好務農為生」之類的，所以也考慮看到某些字就收掉
    """
    match = re.search(r'[。，:]({})(\w+?)[是。為，（在、務\(\<\:]'.format(identifier), text)
    # 用regex 找東西，第一件事就是要確認有沒有找到東西
    if match is None:
        return set(), set()
    name_candidate = match[2] # group 2
    surname = get_surname(name_candidate)
    # 如果不是兒女又沒有姓，那就是非法的名子
    if kinship not in ["女兒", "兒子", ] and surname is None: 
        return set(), set()
    # 如果抓到太長的，那就是名子後又帶了其他東西，此時試著用jieba斷詞並取第一個token
    if len(name_candidate) > 4:
        first_word, tag = list(jieba.posseg.cut(name_candidate))[0]
        if tag.startswith("n"): # len filter
            name = first_word
        else:
            return set(), set()
    else:
        name = name_candidate
        
    # 抓英文別名
    alias_tuples = set()
    # 本名後面如果有括號，裏面如果有英文，就是他的英文名字
    match2 = re.search(r'{}{}（([a-zA-Z].+?)）'.format(match[1], match[2]), text)
    if match2 is not None:
        match3 = re.search(r'[a-zA-Z ]+', match2[1])
        # 我們假設如果是兒女而且有英文名的話，其本名是英文名的翻譯，不用再冠姓，所以冠一個愛心字元做記號
        # 例如：孫先生的兒子叫羅賓(Robin)，明顯他兒子不需要再冠孫姓
        if kinship in ["女兒", "兒子", ]:
            name = "💗" + name
        alias_tuples.add( (name, "英文名", match3[0]) )

    alias_tuples.add( (name, kinship, None) )

    # 即使只抓一個名子，還是把它變成set回傳，讓不管有沒有抓到名子都是一個set(有東西的的set或沒東西的set)，統一都可以用union 來跟其他結果結合起來
    names = set()
    names.add(name)
    return names, alias_tuples    

# 找出姓，如果找不到則回傳None
def get_surname(name):
    for surname in SURNAMES:
        if name.startswith(surname):
            return surname
    return None

def get_names_child_and_spouse(text, biographee_name):
    # 配偶和子女通常在倒數第一、二段
    splits = text.split("\n\n")
    # 如果傳記不到三段，則只取最後一段
    if len(splits) >= 3:
        paragraph = "\n\n".join([splits[-2], splits[-1]])
    else:
        paragraph = splits[-1]
    
    # 找配偶的名子
    man_spouse_names, man_spouse_alias_tuples = get_kin_name("|".join(MAN_SPOUSE_CHARS), paragraph, "夫")
    woman_spouse_names, woman_spouse_alias_tuples = get_kin_name("|".join(WOMAN_SPOUSE_CHARS), paragraph, "妻")

    # 如果有女性配偶，則家姓應該是傳主的姓
    # 或是如果有男性配偶，則家性應該是配偶的性
    # 如果都找不到配偶，則假設家姓是傳主的姓
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

    """
    通常在台北市傳記會有兩種點出子女關係的方式，順序提及型，和列舉型
    順序提及型如「長女慧蛛，次女丁丁。」
    列舉型如「育有3子，長明、長照、長長，」, 「育有1子賢銘」，有時候可能還會有「依序為」等字樣
    而男、女子女獨立地各被提及，而且兩方都是，如果用了其中一型，就不會用另外一型
    但是男女方可能用不同型
    而也有可能直接「育有3子3女，XX、XX、XX....」的這種不知道是兒子還是女兒的情況出現
    """
    # 女兒(順序提及型)
    girl_child_names = set() # a= b =set() is not what i want
    girl_child_alias_tuples = set()
    for girl_order_child in GIRL_ORDER_CHILD:
        girl_order_child_names, girl_order_child_alias_tuples = get_kin_name(girl_order_child, paragraph, "女兒")
        girl_child_names |= girl_order_child_names
        girl_child_alias_tuples |= girl_order_child_alias_tuples

    # 兒子(順序提及型)
    boy_child_names = set()
    boy_child_alias_tuples = set()
    for boy_order_child in BOY_ORDER_CHILD:
        boy_order_child_names, boy_order_child_alias_tuples = get_kin_name(boy_order_child, paragraph, "兒子")
        boy_child_names |= boy_order_child_names
        boy_child_alias_tuples |= boy_order_child_alias_tuples

    # 列舉型
    # 看兒子和女兒哪方還沒找到名子的，列舉的名子就屬於那方
    # 如果兩方都有，就不用再找，如果兩方都沒有，就看傳主的生育狀況
    # 找「育有XXX」 來看傳主的生育狀況(兒子和女兒的有無狀況)，如果有「女」字代表有女兒，有「子」字代表有兒子
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
    # 如果真的有兒子或女兒，且還沒找到他們的名子
    # 則試試看用列舉型來找
    continuous_child_names = set()
    continuous_child_alias_tuples = set()
    if notFound_kinship is not None:
        continuous_child_names, continuous_child_alias_tuples = get_continuous_child_names(paragraph, notFound_kinship)

    # 總合用兩種型找的兒女的名子
    child_names = girl_child_names | boy_child_names | continuous_child_names
    child_alias_tuples = girl_child_alias_tuples | boy_child_alias_tuples | continuous_child_alias_tuples
    # 統一為兒女作冠姓的處理(某些特例情況不會冠姓)
    child_names = prepend_family_name_to_childs(child_names, family_name)
    child_alias_tuples = prepend_family_name_to_childs(child_alias_tuples, family_name)

    return (child_names | man_spouse_names | woman_spouse_names), (child_alias_tuples | man_spouse_alias_tuples | woman_spouse_alias_tuples)

# 找出用列舉方式提及的子/女的名子
def get_continuous_child_names(text, kinship):
    # 以育X子X女來定位，找出後面以標點符號結尾的一句話
    match = re.search(r'育有?(\d子)?(\d女)?(.*?)(。|，)', text)
    if match is None: # 用了regex後第一件事就是看有沒有找到
        return set(), set()

    # 如果「育有XXXX」之後就標點符號，則會抓到空字串，則再抓下一句
    if match[3] is not "":
        unchecked_names = match[3].split("、")
    else:
        match2 = re.search(r'(.+?)(。|，)', text[match.end():])
        if match2 is None:
            return set(), set()
        # 有可能會有「分別為」、「依次為」等等詞
        match3 = re.search(r'(為|是)(：|：)?(.+)', match2[1])
        if match3 is not None:
            unchecked_names = match3[3].split("、")
        else:
            unchecked_names = match2[1].split("、")

    # 處理抓到的名子可能有「子」、「女」開頭，例如「育有2子3女，子明達、子明名、女紀君、,,」
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
        # 後面可能有括號，括號裡可能有英文別名
        detectParen_match = re.search(r'(.+)（(.+?)）', unchecked_name)
        if detectParen_match is not None:
            eng_match = re.match(r'[a-zA-Z ]+', detectParen_match[2])
            # 我們假設如果是兒女而且有英文名的話，其本名是英文名的翻譯，不用再冠姓，所以冠一個愛心字元做記號
            # 例如：孫先生的兒子叫羅賓(Robin)，明顯他兒子不需要再冠孫姓
            if eng_match is not None:
                unchecked_name = "💗" + detectParen_match[1] # assume if have english name, we don't need to preprent family name
                english_name = eng_match[0]
                alias_tuples.add( (unchecked_name, "英文名", english_name) )
            else:
                unchecked_name = detectParen_match[1]

        # 收集起來
        names.add(unchecked_name)
        alias_tuples.add( (unchecked_name, kinship, None) )            

    return names, alias_tuples

def prepend_family_name_to_childs(names_or_aliasTuples, family_name):
    # 有可能family name 完全找不到，則不做處理直接回傳
    if family_name is None:
        return names_or_aliasTuples

    # 
    result = set()
    for element in names_or_aliasTuples:
        # 判斷傳進來的是names 還是aliaTuples
        if isinstance(element, str):
            name = element
        else:
            name = element[0]

        # 冠性，但遇心形符號則單純去掉符號而已
        prepend_executed = False
        if name.startswith("💗"):
            prepended_name = name[1:]
        elif name.startswith(family_name):
            prepended_name = name
        else:
            prepended_name = family_name + name
            prepend_executed = True

        # 依是names還是aliasTuples， 裝回去
        if isinstance(element, str):
            result.add(prepended_name)
        else:
            result.add( (prepended_name, element[1], element[2]) )
            if prepend_executed:
                result.add( (prepended_name, "原形", name) )

    return result

# 統一處理和過濾抓到的名子
def process_and_filter_names(names):
    first_processed_names = set()
    for name in names:
        
        # filter
        if( 1 < len(name) <= 4 # 名字至少兩個字
           and name[-1]!='寺' # 篩掉部分標注錯誤的情
           and name not in ["田野", "伯父", "伯母", "元配", "高中生", "於民國"]  # 常抓到的錯誤名子
            and re.match('[a-zA-Z]',name) == None # 如果開頭是英文(本名通常是中文，英文名會括號另外標)
           and name not in PLACE_NAMES # 地名也常常被抓到
           and not (name[-1]=="人" and name[:-1] in PLACE_NAMES)  # 或是福建人這種哪裡人也常被抓出
        ):
            # 能判斷有姓的，才能叫作人名
            for surname in SURNAMES - set(KINSHIP_CHARS):
                if name.startswith(surname):
                    first_processed_names.add(name)
                    break
            # 名稱是XX和尚這種的抓不到姓，但是還是是傳主的名稱，很重要，所以另外處理
            for monk_chars in ["導師", "法師", "和尚"]:
                if name.endswith(monk_chars):
                    first_processed_names.add(name)

    # 有些抓出來的名子是另個抓出來的名子的substring，此時通常長的是全名，另一個是錯抓到其中一部份
    # 用O(N**2) 的掃描方式，掃描任兩個名子之間是否有一方被包含的關係
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
    sent = text.split("\n\n")[0]
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
    
    with open('./DataBase/ner_result/{}-{}-{}.txt'.format(biography['Book'], biography['StartPage'], biography['Name']), 'w', encoding='utf-8') as f:
        print(result, file=f)

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
            upsert=True, # 有紀錄就改它，沒有就建立紀錄
        )

    for (name, aliasType, alias) in alias_tuples:
        alias_pair = (aliasType, alias)
        db.people.find_and_modify(
            query={'Name': name},
            update={'$push': {'Alias_s' : alias_pair}},
            upsert=True,
        )

if __name__ == "__main__":    
    main()
