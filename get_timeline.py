import os
import re
import numpy as np
#
from Utilities import parallelly_process, get_biography_text, get_people_in_text_within_people
from nltk.parse.corenlp import CoreNLPDependencyParser
dpsr = CoreNLPDependencyParser()
# Simplified and Traditional Chinese
from opencc import OpenCC
toTrad = OpenCC("s2t")
toSimp = OpenCC("t2s")
# database
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"

def get_timeline(text, concise_bool = False):
    positions_of_year = []

    start_pos_pattern = r'((民國)|(大正)|(昭和)|(光緒)|(明治)|咸豐|(乾隆)|(宣統))\d+年' #pattern that indicates the starting point
    for match in re.finditer(start_pos_pattern, text): #find 民國XX年、大正XX年...
        positions_of_year.append( match.start() ) #each starting position of year
    
    timeline_dict = {}
    end_pos_pattern = r'。|([^到至]((民國)|(大正)|(昭和)|(光緒)|(明治)|咸豐|(乾隆)|(宣統)))\d+年' #pattern that indicates the ending point
    for starting_pos in positions_of_year: #iterate through years
        try: #possibly find nothing and return None
            ending_pos = re.search(end_pos_pattern, text[starting_pos + 1:]).span()[0] + starting_pos + 1
            #+1 to avoid finding itself
        except: #if pattern not found
            ending_pos = len(text) #search to the end of text

        raw_str_year_and_event_of_the_year = text[starting_pos: ending_pos]
        (year_start_pos, year_end_pos) = re.search(r'19\d{2}|20\d{2}', raw_str_year_and_event_of_the_year).span() #finf the position of year
        year = raw_str_year_and_event_of_the_year[year_start_pos:year_end_pos] #get year
        raw_str_event_of_the_year = raw_str_year_and_event_of_the_year[year_end_pos+1:] #抓出事件字串，+1 因為有全形右括號

        if concise_bool == False:
            try:
                event_of_the_year = remove_leading_comma(raw_str_event_of_the_year)
            except:
                event_of_the_year = raw_str_event_of_the_year
        else: 
            event_of_the_year = complex_process_raw_event_of_the_year(raw_str_event_of_the_year)
        
        timeline_dict[int(year)] = event_of_the_year #key:year, value: event
    
    return timeline_dict
    
def remove_leading_comma(raw_eoty): #eoty: event of the year
    if raw_eoty[0] == '，':
        return raw_eoty[1:] #delete the leading comma
    return raw_eoty

def dependency_parsing(some_string):
    list_desired_eoty = []
    simplified_substring = toSimp.convert(some_string) 
    for dependency in next(dpsr.raw_parse(simplified_substring)).triples():
        if dependency[1] in ['dobj', 'iobj']: #if is a certain type of desired dependency
            desired_eoty = dependency[0][0] + dependency[2][0] #(('接收', 'VV'), 'nsubj', ('政府', 'NN'))
            desired_eoty = toTrad.convert(desired_eoty)
            list_desired_eoty.append(desired_eoty)
        elif dependency[1] in ['nsubj','csubj']:
            desired_eoty = dependency[2][0] + dependency[0][0]
            desired_eoty = toTrad.convert(desired_eoty)
            list_desired_eoty.append(desired_eoty)
    return list_desired_eoty

def complex_process_raw_event_of_the_year(raw_eoty):
    raw_eoty = remove_leading_comma(raw_eoty)
    list_eoty = dependency_parsing(raw_eoty)
    if len(list_eoty) == 0: #if no desired dependencies found
        return remove_leading_comma(raw_eoty)
    eoty = '，'.join(list_eoty)
    return eoty

def sort_timeline_dict(timeline_dict): #sort event by time
    import collections
    timeline_ordered_dict = collections.OrderedDict(sorted(timeline_dict.items()))
    return timeline_ordered_dict

def print_timeline(time_line_dict):
    print('\n#--------------------------------------------------#')
    for key, value in time_line_dict.items():
        print(key, ':', value)
    print('#--------------------------------------------------#\n')

def get_text_by_name(path, person_name):
    file_names = os.listdir(path)
    specific_file_name = list(filter(lambda x: person_name in x, file_names))[0]
    f = open('/home/.../Summarize_People-master/DataBase/mature_txt/' + specific_file_name)
    text = f.read()
    return text

def output_chronologicalTable(biograpy, ordered_chronologicalTable, whetherConcise):
    try:
        os.makedirs('./DataBase/chronological-table')
    except FileExistsError: # directory is exist
        pass

    with open('./DataBase/chronological-table/{}-{}{}'.format(biograpy['StartPage'], biograpy['Name'], "" if not whetherConcise else "_concise"), 'w', encoding='utf-8') as f:
        print('\n#--------------------------------------------------#', file=f)
        for key, value in ordered_chronologicalTable.items():
            print(key, ':', value, file=f)
        print('#--------------------------------------------------#\n', file=f)


def main_process(biographies):
    for biography in biographies:
        text = get_biography_text(biography)
        for whetherConcise in [False, True]:
            chronologicalTable = get_timeline(text, concise_bool=whetherConcise)
            ordered_chronologicalTable = sort_timeline_dict(chronologicalTable)
            output_chronologicalTable(biography, ordered_chronologicalTable, whetherConcise)

def main():
    parallelly_process(main_process, list(db.biographies.find()))

if __name__ == '__main__':    
    main()
