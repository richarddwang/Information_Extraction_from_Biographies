import subprocess
import argparse
from Convert_And_Extract import main as convert_and_extract
from Preprocess import main as preprocess
from NER import main as ner
from Cooccurrence import main as cooccurrence
from Relationship import main as relation
from Graph import main as generate_graphs
from Get_timeline import main as get_chronologicalTable

def main():
    print("Check tools and environments")
    check_tools_and_environemnts()
    print("All tools requirements satisfied")
    main_process()

def main_process():
    print("Convert and extracting")
    convert_and_extract()
    print("Preprocessing")
    preprocess()
    print("NERing")
    ner()
    print("Counting cooccurrence")
    cooccurrence()
    print("Relation Analyzing")
    relation()
    print("Generating graphs")
    generate_graphs()
    print("Generating chronologicalTable")
    get_chronologicalTable()

def check_tools_and_environemnts():
    print("Checking output directories exist")
    makedirs_if_not_exist('./DataBase/tmp')
    makedirs_if_not_exist('./DataBase/raw_txt')
    makedirs_if_not_exist('./DataBase/mature_txt')
    makedirs_if_not_exist('./DataBase/ner_result')
    makedirs_if_not_exist('./DataBase/relation')
    makedirs_if_not_exist('./DataBase/chronological-table')
    
    
    print("Checking python packages")
    subprocess.run("pip3 install --require ./requirements.txt".split())

    print("Checking supplement files")
    if not os.path.isfile('./Tools/Appendix-Names.dict.txt'):
        raise ToolsError("No Appendix-Names.dict.txt, goto Get-Tools and execute Get_Appendix_Names.py")
    if not os.path.isfile('./DataBase/tmp/Japanese-Surnames.json'):
        raise ToolsError("No Japanese-Surnames.json, goto Get-Tools and execute Japanese_Surname_Crowler.py")
    if not os.path.isfile('./Tools/Japanese-Surnames-in-zhTW.json'):
        raise ToolsError("No Japanese-Surnames-in-zhTW.json, goto Get-Tools and execute Translate_Word_Jp2zhTW_Crowler.py. !! ABOUT SIX HOURS NEEDED !!")
    if not os.path.isfile('./Tools/Mainland-Place-Names.json'):
        raise ToolsError("No Mainland-Place-Names.json, goto Get-Tools and execute Mainland-Placename-Crowler.py")

    print("Checking stanford tool")
    if not os.path.isdir('./Tools/stanford-corenlp-full-2018-02-27'):
        raise ToolsError("No corenlp, Download corenlp and unzip under Tools.")
    if not os.path.isfile('./Tools/stanford-corenlp-full-2018-02-27/stanford-chinese-corenlp-2018-02-27-models.jar'):
        raise ToolsError("No corenlp-chinese-model, Download it and place under stanford directory")
    
    
if __name__ == '__main__':
    main()

class ToolsError(Exception):
    def __init__(self, message):
        super().__init__(message)

def makedirs_if_not_exist(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass
