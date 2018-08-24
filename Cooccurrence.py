import re
import sys
from collections import namedtuple
# 共現關係與其值的資料結構，值隨著處理階段可能是文面距離或初始分數或最後分數
PairValue = namedtuple('PairValue', ['person', 'other', 'value'])
from Utilities import parallelly_process, get_biography_text, get_people_in_text_within_people
# 資料庫相關的引用
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # 建立對本地的Mongodb daemon 的連接
db = client['Summary'] # 接觸"Summary" 資料庫
db['cooccurrences'] # 如果不存在collection "cooccurrence" 則建立
# 加權共現排名計算方法的調整參數
DELEMITERS = ["，", "。", "。\n\n"] # 句子的區隔，越後面的代表越大的間隔
INCREASEMENT = [1, 2, 3] # 依順序給每個間隔設定的間隔距離
DISTANCE2SCORE_FACTOR = 4 # 將共現的兩名子之間的距離，轉成分數的參數
DEPRECIATE_FACTOR = 0.65 # 讓重複的共現關係的分數折舊的參數
DISTANCE_TO_BIOGRAPHEE = 2 # 設定傳記中登場人物與傳主間的距離(因為傳主名子通常不再內文出現)

def main():
    # db.cooccurrences.remove() # remove data in collection if exist
    parallelly_process(main_process, list(db.biographies.find()))
    
def main_process(biographies):
    for biography in biographies:
        text = get_biography_text(biography) 
        people = get_people_in_text_within_people(text, db.people.find()) # 掃描出傳記裡所有的名子
        indexed_people = tag_people_index_in_text(people, text) # 將每個名子標注其所在句子的文面位置
        pair_distances = count_cooccurence_distance(indexed_people) # 算出兩兩名子間的距離
        pair_distances +=  set_cooccurrence_to_biographee(people, biography['Name']) # 還有各名子與傳主的預設距離
        pair_scores = count_coccurrence_score(pair_distances) # 將距離轉換成分數並將重複的共現關係折舊相加，成為分數
        # output_scores_in_biography(pair_scores, biography) # 將結果以檔案型式輸出
        # update_scores_to_db(pair_scores) # 將結果加到資料庫裡

# 將每個名子標注其所在句子的文面位置
def tag_people_index_in_text(total_people, text):
    total_indexed_people = [] # 收集所有標注好位置的人名
    pos = 1 # 目前所在句子的位置
    # 依往右最近碰到的間隔，來切割成句子、間隔、剩下的文章
    left_most_split, delimiter, rest_text = one_split_by_any_delimiter(text, DELEMITERS)
    while left_most_split is not None:
        # 在先前得出的此傳記裡所有出現的人名裡，找出此句子裡的人名
        people = get_people_in_text_within_people(left_most_split, total_people, repeatOK=True)
        # 將人名標上現在所在句子的位置
        indexed_people = list(zip( [pos] * len(people), people))
        # 如果這句子裏面其實沒有人名，就不管它，否則將標注好的收集起來
        if indexed_people: # if not empty
            total_indexed_people += indexed_people
        # 依間隔的種類，更新目前所在句子的位置
        pos += INCREASEMENT[DELEMITERS.index(delimiter)]
        # 重複切割出句子，直到沒得切為止
        left_most_split, delimiter, rest_text = one_split_by_any_delimiter(rest_text, DELEMITERS)

    return total_indexed_people
        
# 依往右最近碰到的間隔，來切割成句子、間隔、剩下的文章
def one_split_by_any_delimiter(text, delimiters):
    regex_ORGroup = '|'.join(DELEMITERS) # 將間隔符號OR起來變成Regex
    regex = r'({})\w'.format(regex_ORGroup) # 用此Regex 搜尋最近的間隔(regex的OR會優先靠前的東西)
    match = re.search(regex, text)
    if match is None :
        return (None, None, text)
    else:
        delimiter = match[1] # group 1 是該間隔
        delimeter_startPos, rest_StartPos = match.span(1) # 找出該間隔的起始位置和剩下文章的起始位置 (match 的 end 其實是mathc 的結尾位置再+1)
        return (text[:delimeter_startPos], delimiter, text[rest_StartPos:sys.maxsize]) # 割成間隔本身和剩下的文章

# 算出兩兩名子間的距離
def count_cooccurence_distance(indexed_people):
    pair_distances = []
    for (i, (index, person)) in enumerate(indexed_people):
        for other_index, other_person in indexed_people[i+1:]:
            if person['_id'] != other_person['_id']: # 此共現關係兩個人名不能是同一人名
                name = person['Name']
                otherName = other_person['Name']
                two_names = sorted( [name, otherName] ) # 保證在資料結構中，前面的名子在字典排序上比後面的名子小
                pair_distances.append( PairValue(two_names[0], two_names[1], other_index-index+1) ) # 距離有可能是0，所以全部+1 來作一個smooth的動作
    
    return pair_distances

# 產生名子和傳主的距離
def set_cooccurrence_to_biographee(people, biographee_name):
    pair_distances = []
    for person in people:
        name = biographee_name
        otherName = person['Name']
        two_names = sorted( [name, otherName] )
        pair_distances.append( PairValue( two_names[0], two_names[1], DISTANCE_TO_BIOGRAPHEE) )

    return pair_distances

# 算出分數
def count_coccurrence_score(pair_distances):
    # 由於先前保證過比較小的名子一定會在前面，所以在字典排序下，描述相同兩人物的共現關係們會聚在一起
    # 在描述相同兩人物的共現關係們中，距離越小的在越前面，讓距離越大的折舊越多
    pair_distances = sorted(pair_distances)
    
    pair_scores = []
    pair = None # 目前記住的共現關係的兩人物
    for tpl in pair_distances:
        # 跟上一個共現關係描述不同的兩人物
        if (tpl.person, tpl.other) != pair: 
            pair = (tpl.person, tpl.other)
            depre = DEPRECIATE_FACTOR
            pair_scores.append(PairValue(tpl.person, tpl.other, DISTANCE2SCORE_FACTOR / tpl.value))
        # 跟上一個共現關係描述相同的兩人物，要將算折舊的分數，並且是加到上一個共現關係的分數而不是成為另外一個分數
        else:
            pair_score = pair_scores[-1]
            pair_scores[-1] = PairValue(tpl.person, tpl.other, pair_score.value + DISTANCE2SCORE_FACTOR / tpl.value * depre)
            depre **= 2
            
    return pair_scores

def output_scores_in_biography(pair_scores, biography):
    with open('./DataBase/cooccurrence/{}-{}-{}.txt'.format(biography['Book'], biography['StartPage'], biography['Name']) , 'w', encoding='utf-8') as f:
        for pair_score in sorted(pair_scores, key=lambda x: x.value, reverse=True):
            if pair_score.person != pair_score.other:
                print(pair_score.person, round(pair_score.value, 2), pair_score.other, file=f)

def update_scores_to_db(pair_scores):
    for pair_score in pair_scores:
        if pair_score.person != pair_score.other:
            db.cooccurrences.insert_one(
                {'Name1':pair_score.person,
                 'Name2':pair_score.other,
                 'Score':pair_score.value,}
            )

if __name__ == '__main__':
    main()
