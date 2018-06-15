import subprocess
import argparse
from ConvertAndExtract import main as convert_and_extract
from Preprocess import main as preprocess
from GetAppendixNames import main as get_appendix_names
from NER import main as ner
from Cooccurrence import main as cooccurrence
from Relationship import main as relation

def main():
    if OUTPUT is True:
        convert_and_extract()
        preprocess()
        get_appendix_names()
        ner()
        cooccurrence()
        relation()

if __name__ == '__main__':
    main()
