from stanfordcorenlp import StanfordCoreNLP
nlp = StanfordCoreNLP('./Tools/stanford-corenlp-full-2018-02-27', lang='zh') 
from opencc import OpenCC 
convert_s2t = OpenCC("s2t") # 簡轉繁
convert_t2s = OpenCC("t2s") # 繁轉簡
import re # for re.split
import os # for os.listdir()
import argparse

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
    text = convert_t2s.convert(text)
    main_char = convert_t2s.convert(main_char)
    obj = convert_t2s.convert(obj)
    pos = nlp.pos_tag(text)
    dep = nlp.dependency_parse(text)
    dep_dict = build_dict(pos, dep)
    verb_output = []
    nn_output = []
    if obj in dep_dict.keys():
        if "nsubj" in dep_dict[obj]['dependency'].keys(): # 母亲为xxx / 父亲xx，也就是目標人名與某個詞有直接的主賓依賴關係
            sentence = '{} {} {}'.format(main_char, dep_dict[obj]['dependency']['nsubj'], obj)
            return [convert_s2t.convert(sentence)]
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
                return [convert_s2t.convert(sentence)]                    
            else:
                for dp in word_dep:
                    if dp == "case" and dep_dict[word]["pos"] == "NN": # 因美国学者田武雅教授的推荐
                        nn_output.append('{} {} {}'.format(obj, word, main_char))
                    elif dep_dict[word]['dependency'][dp] == obj:
                        nn_output.append('{} {} {}'.format(main_char, word, obj))
    if verb_output:
        verb_output = list(map(lambda x: convert_s2t.convert(x), verb_output))
        return verb_output
    elif nn_output:
        nn_output = list(map(lambda x: convert_s2t.convert(x), nn_output))
        return nn_output
    else:
        return "there has no relationships"
    
def corpus_path(name, paths):
    for p in paths:
        if name in p:
            return "./DataBase/mature_txt/" + p

def ner_dict(ner):
    result = {}
    for n in ner:
        if "中文名" not in n:
            n = re.sub(" .*", "", n)
            result[n] = [n]
        else:
            n = n.split('：')
            n[0] = n[0][:-2]
            if ":" in n[1]:
                n[1] = re.sub(":.*", "", n[1])
            else:
                n[1] = re.sub("\(.*", "", n[1])
            result[n[0]] = [n[1]]
    return result
        
def output(result, p):
    with open("./{}_有向關係.txt".format(p), 'w', encoding="utf8") as f:
        for r in result:
            print(r)
            f.write(r + "\r\n")
    return

def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-p", "--people",
                     nargs='+', dest="people")
    args = argParser.parse_args()
    paths = os.listdir("./DataBase/mature_txt/")
    for p in args.people:
        result = []
        with open(corpus_path(p, paths), "r") as f: # corpuspath() 還沒寫
            corpus = f.read()
        with open( "./{}_NER與別名.txt".format(p), "r", encoding="utf8") as f: # NERpath() 還沒寫
            ner = f.read().split("\n")
        ner = ner_dict(ner)
        for n in ner:
            for name in ner[n]:
                lines = extract_line(corpus, name)
                for line in lines:
                    result.extend(relationship(line, p, name))
        output(result, p) # output() 還沒寫
        
if __name__ == "__main__":
    main()
