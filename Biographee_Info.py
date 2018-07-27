import re
import operator
import json
import sys
# DataBase
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary" 

with open('./Tools/Taiwanese-Place-Names.json', 'r', encoding='utf-8') as f:
    PLACE_NAMES = json.load(f)
with open('./Tools/Mainland-Place-Names.json', 'r', encoding='utf-8') as f:
    PLACE_NAMES += json.load(f)
PLACE_NAME_CONCATENATION = "|".join(PLACE_NAMES)

def main():
    for biography in db.biographies.find():
        with open('./DataBase/mature_txt/{}-{}.txt'.format(biography['StartPage'], biography['Name']), 'r') as f:
            text = f.read()
        extract_more_biographee_info(biography, text)

def extract_more_biographee_info(biography, text):
    first_paragraph = text.split("\n\n")[0]
    match = re.search(r'({})人(，|。)'.format(PLACE_NAME_CONCATENATION), text)
    if match is None:
        biography['Hometown'] = None
    else:
        biography['Hometown'] = match[1]

    db.biographies.find_and_modify(
        query={'_id':biography['_id']},
        update={'$set':
                {'Hometown' : biography['Hometown']}},
    )

def query():
    biograpies = list(db.biographies.find())
    where = input("請輸入查詢：")
    for condition in where.split(","):
        match1 = re.match(r' ?出生 (.+) ((\d\d\d\d)(.(\d\d))?(.(\d\d))?) ?', condition)
        if match1 is not None:
            comp = match1[1]
            year = int(match1[3]) if match1[3] is not None else None
            month = int(match1[5]) if match1[5] is not None else None
            day = int(match1[7]) if match1[7] is not None else None
            relate = convert_comparison_str2func(comp)
            biograpies = filter_by_date("Birth", biograpies, relate, year, month, day)
            
        match2 = re.match(r' ?死亡 (.+) ((\d\d\d\d)(.(\d\d))?(.(\d\d))?) ?', condition)
        if match2 is not None:
            comp = match2[1]
            year = int(match2[3]) if match2[3] is not None else None
            month = int(match2[5]) if match2[5] is not None else None
            day = int(match2[7]) if match2[7] is not None else None
            relate = convert_comparison_str2func(comp)
            biograpies = filter_by_date("Death", biograpies, relate, year, month, day)

        match3 = re.match(r' ?家鄉 = (\w+) ?', condition)
        if match3 is not None:
            biograpies = list(filter(lambda x:
                                     x['Hometown'] is not None and
                                     (x['Hometown'] in match3[1] or match3[1] in x['Hometown'])
                                     , biograpies))
            
    for biograpy in biograpies:
        print(biograpy['Name'], biograpy['Birth'], biograpy['Death'], biograpy['Hometown'])
        
        
def convert_comparison_str2func(comp):
    if comp == ">":
        relate = operator.gt
    elif comp == "<":
        relate = operator.lt
    elif comp == "=":
        relate = operator.eq
    elif comp == ">=":
        relate = operator.ge
    elif comp == "<=":
        relate = operator.le
    else:
        assert False, "{} is not a valid comparison operator".format(comp)
    return relate
    
def filter_by_date(attr, biograpies, relate, year, month, day):
    filtered_biographies = []
    for biography in biograpies:
        if filter_biography_by_date(attr, biography, relate, year, month, day) is True:
            filtered_biographies.append(biography)
    return filtered_biographies

def filter_biography_by_date(attr, biography, relate, year, month, day):
    #
    if biography[attr] is None: 
        return False
        
    for (left, right) in zip(biography[attr].split("."), [year, month, day]): #
        #
        if right is not None:
            #
            try:
                left = int(left)
            except:
                print(biography['Name'], biography['Birth'], biography['Death'], biography['Hometown'])
                return False

            if left == right: #
                continue
            #
            elif relate(left, right):
                return True
            else:
                return False
            
    return relate(1,1)
            

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    elif len(sys.argv) == 2 and sys.argv[1] == "--query":
        query()
