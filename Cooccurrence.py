from collections import namedtuple
PairValue = namedtuple('PairValue', ['person', 'other', 'value'])
from Utilities import parallelly_process
# database
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"
db.cooccurrences.remove() # remove data in collection if exist
db['cooccurrences'] # create collection "cooccurrence" if not exist
# Global variables
DELEMITERS = ["，", "。", "\n\n"]
INCREASEMENT = [1, 2, 3]
DISTANCE2SCORE_FACTOR = 4
DEPRECIATE_FACTOR = 0.65
DISTANCE_TO_BIOGRAPHEE = 2

def main():
    parallelly_process(main_process, list(db.biographies.find()))
    
def main_process(biographies):
    for biograpy in biographies:
        text = get_biography_text(biograpy)
        people = get_people_in_text_within_people(text, db.people.find())
        indexed_people = tag_people_index_in_text(people, text)
        pair_distances = count_cooccurence_distance(indexed_people)
        pair_distances.append( set_cooccurrence_to_biographee(people, biograpy['Name']) )
        pair_scores = count_coccurrence_score(pair_distances)
        update_scores_to_db(pair_scores)
        
def get_biography_text(biography):
    with open('./DataBase/mature_txt/{}-{}.txt'.format(biography['StartPage'], biography['Name']),'r' ,encoding='utf-8', ) as f:
        text = f.read()
    return text

def get_people_in_text_within_people(text, within_people, repeatOK=False):
    in_text_people = []
    get = False
    for person in within_people:
        #
        if text.find(person['Name']) is not -1:
            get = True
            in_text_people.append(person)
        #    
        for (aliasType, aliasName) in person['Alias_s']:
            if get and not repeatOK:
                break
            elif text.find(aliasName) is not -1:
                get = True
                in_text_people.append(person)
                
    return in_text_people

def tag_people_index_in_text(total_people, text):
    total_indexed_people = []
    pos = 1
    left_most_split, delimiter, rest_text = one_split_by_any_delimiter(text, DELEMITERS)
    while left_most_split is not None:
         people = get_people_in_text_within_people(left_most_split, total_people, repeatOK=True)
         indexed_people = list(zip( [pos] * len(people), people))
         #
         if indexed_people: # if not empty
             total_indexed_people += indexed_people
         pos += INCREASEMENT[DELEMITERS.index(delimiter)]
         left_most_split, delimiter, rest_text = one_split_by_any_delimiter(rest_text, DELEMITERS)
         
    return total_indexed_people
        

def one_split_by_any_delimiter(text, delimiters):
    for (i, char) in enumerate(text):
        if char in delimiters:
            return (text[:i], char, text[i+1:len(text)-1])
    return (None, None, text)

def count_cooccurence_distance(indexed_people):
    pair_distances = []
    for (i, (index, person)) in enumerate(indexed_people):
        for other_index, other_person in indexed_people[i+1:]:
            if person['_id'] != other_person['_id']:
                i = person['_id']
                oi = other_person['_id']
                pair_distances.append( PairValue(max(i,oi), min(i,oi), other_index-index+1) )
    
    return pair_distances

def set_cooccurrence_to_biographee(people, biographee_name):
    biographee = db.people.find_one(filter={'Name':biographee_name})
    pair_distances = []
    for person in people:
        i = biographee['_id']
        oi = person['_id']
        pair_distances.append( PairValue( max(i,oi), min(i,oi), DISTANCE_TO_BIOGRAPHEE) )

    return pair_distances

def count_coccurrence_score(pair_distances):
    pair_distances = sorted(pair_distances) # lexicographically sort
    
    pair_scores = []
    pair = None
    for tpl in pair_distances:
        if (tpl.person, tpl.other) is not pair:
            pair = (tpl.person, tpl.other)
            depre = DEPRECIATE_FACTOR
            pair_scores.append(PairValue(tpl.person, tpl.other, DISTANCE2SCORE_FACTOR / tpl.value))
        else:
            pair_score = pair_scores[-1]
            pair_scores[-1] = PairValue(tpl.person, tpl.other, pair_score + tpl.value * depre)
            depre **= 2
            
    return pair_scores

def update_scores_to_db(pair_scores):
    for pair_score in pair_scores:
        db.cooccurrences.insert_one(
            {'ID1':pair_score.person,
             'ID2':pair_score.other,
             'Score':pair_score.value,}
        )

if __name__ == '__main__':
    main()
