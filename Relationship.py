import re
import os
from stanfordcorenlp import StanfordCoreNLP
nlp = StanfordCoreNLP('./Tools/stanford-corenlp-full-2018-02-27', lang='zh')
# Simplified and Traditional Chinese
from opencc import OpenCC
toTrad = OpenCC("s2t")
toSimp = OpenCC("t2s")
# database
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"
db.relations.remove() # remove data in collection if exist
db['relations'] # create collection "cooccurrence" if not exist
#
from Cooccurrence import get_biography_text, get_people_in_text_within_people
from Utilities import parallelly_process

def main():
    try:
        parallelly_process(main_process, list(db.biographies.find()))
    finally:
        nlp.close()
    
def main_process(biographies):
    total_relations = []
    for biograpy in biographies:
        text = get_biography_text(biograpy)
        people = get_people_in_text_within_people(text, db.people.find())
        names = get_all_names_of_people(people)
        relations = []
        for name in names:
            lines_have_name = extract_line(text, name)
            for line in lines_have_name:
                relations.extend(relationship(line, biograpy['Name'], name))
        output_relations_of_biography(relations, biograpy)
        total_relations += relations
                
    update_relations_to_db(total_relations)

def get_all_names_of_people(people):
    names = []
    for person in people:
        names.append(person['Name'])
        for (aliasType, aliasName) in person['Alias_s']:
            names.append(aliasName)
    return names

def extract_line(corpus, name):
    corpus = corpus.replace("\n\n", "")
    corpus = re.split("，|。", corpus)
    corpus = list(filter(None, corpus))
    result = []
    for line in corpus:
        if name in line:
            if "（" in line:
                line = re.sub("（(.*?)）", "", line)
            result.append(line)
    return result

def relationship(text, main_char, obj):
    """
    test_txt = "被王小明殺害"
    relationship(test_txt, "王世慶", "王小明")
    >>> ['王小明 杀害 王世庆']
    
    test_txt = "和美國學者史威廉教授合作共同發表論文"
    relationship(test_txt, "王世慶", "史威廉")
    >>> ['王世慶 合作發表論文 史威廉']
    """
    text = toSimp.convert(text)
    main_char = toSimp.convert(main_char)
    obj = toSimp.convert(obj)
    pos = nlp.pos_tag(text)
    dep = nlp.dependency_parse(text)
    dep_dict = build_dict(pos, dep)
    verb_output = []
    nn_output = []
    if obj in dep_dict.keys():
        if "nsubj" in dep_dict[obj]['dependency'].keys(): # 母亲为xxx / 父亲xx，也就是目標人名與某個詞有直接的主賓依賴關係
            sentence = '{} {} {}'.format(main_char, dep_dict[obj]['dependency']['nsubj'], obj)
            return [toTrad.convert(sentence)]
    for word in dep_dict:
        if dep_dict[word]['pos'] == 'VV': # Verb
            if (word not in obj) and (word not in main_char): # 確保斷詞不是人名的一部分
                word_deps = dep_dict[word]['dependency'].keys()
                if 'nsubj' in word_deps: # 如果該字前面有主語
                    nsubj = dep_dict[word]['dependency']['nsubj']
                    if 'dobj' in word_deps: # 如果該字後面有賓語
                        dobj = dep_dict[word]['dependency']['dobj']
                        if nsubj == main_char: # 如果該字前面的主語等於主要人物名稱，則不寫入
                            if dobj == obj:
                                verb_output.append('{} {} {}'.format(main_char, word, obj))
                            else:
                                verb_output.append('{} {}{} {}'.format(main_char, word, dobj, obj))
                        else:
                            if dobj == obj:
                                verb_output.append('{} {}{} {}'.format(main_char, nsubj, word, obj))
                            else:
                                verb_output.append('{} {}{}{} {}'.format(main_char, nsubj, word, dobj, obj))
                    else: # 在傳記文體中，如果該字前面有主語而無賓語，則可能是關係可能是 對方 -> action -> 主要人物
                        if (nsubj == obj) or (nsubj == main_char):
                            verb_output.append('{} {} {}'.format(obj, word, main_char))
                        else:
                            verb_output.append('{} {}{} {}'.format(obj, nsubj, word, main_char))
                else:
                    if 'dobj' in word_deps:
                        dobj = dep_dict[word]['dependency']['dobj']
                        if dobj == obj:
                            verb_output.append('{} {} {}'.format(main_char, word, obj))
                        else:
                            verb_output.append('{} {}{} {}'.format(main_char, word, dobj, obj))
                    else:
                        verb_output.append('{} {} {}'.format(main_char, word, obj))
            else: # 斷詞是人名的一部分，不處理。比如 中川
                None
        else: # not verb
            word_dep = dep_dict[word]['dependency']
            if "nmod:assmod" in word_dep.keys() and word_dep["nmod:assmod"] == obj: # 目標人名若是某個名詞的修飾詞
                sentence = '{} {} {}'.format(obj, word, main_char)  # 則很有可能代表關係的方向是 目標 -> 名詞 -> 主要人物
                return [toTrad.convert(sentence)]                    
            else:
                for dp in word_dep:
                    if dp == "case" and dep_dict[word]["pos"] == "NN": # 因美国学者田武雅教授的推荐
                        nn_output.append('{} {} {}'.format(obj, word, main_char))
                    elif dep_dict[word]['dependency'][dp] == obj:
                        nn_output.append('{} {} {}'.format(main_char, word, obj))
    if verb_output:
        verb_output = list(map(lambda x: toTrad.convert(x), verb_output))
        return verb_output
    elif nn_output:
        nn_output = list(map(lambda x: toTrad.convert(x), nn_output))
        return nn_output
    else:
        return "there has no relationships" ## be treated as list when extend the reture value of this func

def build_dict(pos, depend):
    """
    depend為nlp.dependency_parse()的output
    [('ROOT', 0, 8),
     ('case', 5, 1),
     ('nmod:assmod', 3, 2),
     ('dep', 5, 3),
     ('compound:nn', 5, 4),
     ('nmod:prep', 6, 5),
     ('nsubj', 8, 6),
     ('advmod', 8, 7),
     ('dobj', 8, 9)]
    除了ROOT那個tuple以外，其餘tuple裡面的數字都是句中的第幾個詞（initial=1）
    
    """
    output = {}
    word_list = []
    for t in pos:
        word = t[0]
        p = t[1]
        output[word] = {"pos":p, "dependency":{}}
        word_list.append(word)
    for t in depend:
        depd = t[0] # dependency
        if depd != "ROOT":
            obj = word_list[t[1]-1] # 依賴者
            subj = word_list[t[2]-1] # 被依賴者
            output[obj]["dependency"][depd] = subj
    return output    

def output_relations_of_biography(relations, biography):
    try:
        os.makedirs('./DataBase/relation')
    except FileExistsError: # directory is exist
        pass

    with open('./DataBase/relation/{}-{}.txt'.format(biography['StartPage'], biography['Name']), mode='w', encoding='utf-8') as f:
        for relation in relations:
            relation = relation.split()
            if isinstance(relation, list) and len(relation)==3:
                name1, rel, name2 = relation
                print(name1, rel, name2, file=f)

            
def update_relations_to_db(relations):
    for relation in relations:
        relation = relation.split()
        if isinstance(relation, list) and len(relation)==3:
            name1, rel, name2 = relation
            db.relations.insert_one(
                {'ID1' : None,
                 'Name1' : name1,
                 'Relation' : rel,
                 'ID2' : None,
                 'Name2' : name2,}
            )

if __name__=='__main__':
    main()
    
    # try:
    #     main_process(list(db.biographies.find(filter={'Name':"王世慶"})))
    # finally:
    #     nlp.close()
    
