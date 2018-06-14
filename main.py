import subprocess
import argparse
from ConvertAndExtract import main as convert_and_extract
from Preprocess import main as preprocess
from GetAppendixNames import main as get_appendix_names
from NER import main as ner
OUTPUT = False

def main():
    if OUTPUT is True:
        convert_and_extract()
        preprocess()
        get_appendix_names()
        ner()
    else:
        convert_and_extract()
        subprocess.run('python3 Preprocess.py --no-output'.split())
        get_appendix_names()
        subprocess.run('python3 NER.py --no-output'.split())

if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-n', '--no-output',
                           action='store_false',
                           dest='whether_output',
                           help="Output the result for the sake of getting insights.",)
    args = argParser.parse_args()
    OUTPUT = args.whether_output

    main()
