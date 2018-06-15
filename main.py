import subprocess
import argparse
from ConvertAndExtract import main as convert_and_extract
from Preprocess import main as preprocess
from GetAppendixNames import main as get_appendix_names
from NER import main as ner
from Cooccurrence import main as cooccurrence
from Relationship import main as relation

def main():
    print("ConvertAndExtracting")
    convert_and_extract()
    print("preprocessing")
    preprocess()
    print("getting appendix")
    get_appendix_names()
    print("getting NER")
    ner()
    print("counting cooccurrence")
    cooccurrence()
    print("getting relation")
    relation()

if __name__ == '__main__':
    main()
