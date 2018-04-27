import argparse # command line arguments 相關library
import threading # 多線程處理用library
from SplitAndExtract import split_and_extract
from Tokenize import tokenize
from Statistic import statistic

def firstSetUp():
    split_and_extract()
    # The threads is designed to executre target with args
    t1 = threading.Thread(target=tokenize, args=['ckip'])
    t2 = threading.Thread(target=tokenize, args=['jieba'])
    # start the threads 
    t1.start()
    t2.start()
    # stop calling thread (for this case, is main thread) until t1 and t2 end
    t1.join()
    t2.join()

def main(people=None, len_of_word=None, mostRank=None):
    statistic('ckip', people, len_of_word, mostRank)
    statistic('jieba', people, len_of_word, mostRank)

if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-p', '--people',
                           nargs='+',
                           help="specify people you want to analyze, otherwise analyze all.")
    argParser.add_argument('-c','--chars',
                           type=int,
                           help="specify you want to count word with how many chars")
    argParser.add_argument('-m','--most',
                           type=int,
                           help="specify you want to the most how many frequent words")
    argParser.add_argument('--set-up',
                           action='store_true', # 此option argument 後面沒有arguments, 出現此option 就是設成true
                           dest='setUp')
    args = argParser.parse_args()
    
    if args.setUp:
        firstSetUp()
    main(args.people, args.chars, args.most)

#========================================================
#                       Test
#========================================================
# python main.py --chars 2 --most 5 --set-up
# python main.py -m 5 --people 何凡 何基明
    
