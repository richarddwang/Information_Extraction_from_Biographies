import argparse
import os
from collections import Counter # High performance container datatypes, and with many convenient method

def statistic(tokenizeTool, people=None, num_char=None, mostRank=None):
    # 如果是資料夾，則回傳所有底下ckip/jieba_tokens結尾的檔案的完整路徑
    # 如果是一個檔案，就是就只包含一個檔案的所有路徑
    tokenFiles = get_tokenFiles(tokenizeTool, people)

    # 得到所有指定搜索範圍的所有token
    total_tokens = []
    for tokenFile in tokenFiles:
        tokens = extract_token(tokenFile) # 從tokenFile 抽取出裏面的tokens
        total_tokens += tokens

    # 在可能過濾成n字詞之前，先算好全部的token數和word type數
    num_token = len(total_tokens)
    num_wordType = len(set(total_tokens))

    # 過濾成n字詞 (如果需要)
    if num_char is not None:
        total_tokens = list(filter(lambda w: len(w)==num_char, total_tokens))
    
    # list轉成Counter
    wordType_counter = Counter(total_tokens)

    # 過濾成前n名的list of tupes (過濾只在有需要的情況)
    if mostRank is None:
        wordTypeAndFreq_s = wordType_counter.most_common()
    else:
        wordTypeAndFreq_s = wordType_counter.most_common(mostRank)

    # 輸出結果
    print(
        '''
 {}在{} 斷詞下
 Token 總數: {}
 Word type 總數: {}
 {}字詞中出現最頻繁的前{}名: 
        '''.format(
            "「{}」的文本".format("所有" if people is None else "、".join(people)), # 所有 / 多個人名串接 
            tokenizeTool,
            num_token,
            num_wordType,
            num_char if num_char is not None else "任意",
            mostRank if mostRank is not None else "任意")
    )
    
    for wordTypeAndFreq in wordTypeAndFreq_s:
        print(wordTypeAndFreq[0], wordTypeAndFreq[1], "次")

def get_tokenFiles(tokenizeTool, people_names):
    if people_names is None:
        token_files = list(filter(lambda f: tokenizeTool in f, # 只取名子裡有ckip(jieba) 的檔案
                                  os.listdir('./Texts')) # 從./Texts下的所有檔案和資料夾裡取
        )
        return ['./Texts/' + tokenFile for tokenFile in token_files] # 所有檔名加prefix 變路徑
    else:
        return ['./Texts/{}_{}_tokens'.format(person_name, tokenizeTool) for person_name in people_names] 
    
def extract_token(tokenFile):
    with open(tokenFile, 'r') as f:
        text = f.read()
    return text.split('\n')
        
if __name__ == '__main__':
    assert len(sys.argv) >= 3, "\'python Statistic.py -h\' to see help"

    # 用ArgumentParser 來定義無論optional 和 position arguments(這裡只定義了optional)
    # 然後用這些定義去parse command line 的arguments, 得到每個option arguments 後的arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-p', '--people', # option 的specify 方式
                           nargs='+', # option後有一個以上的argumets # 指定nargs, 結果將是一個list
                           help="specify people you want to analyze, otherwise analyze all.") # -h 裡的敘述
    argParser.add_argument('-t', '--tool',
                           nargs='+',
                           choices=['ckip', 'jieba'], # 限制option後面的argument的可能值
                           required=True, # 此option 必須要有，預設是False
                           metavar="TOOLS", # 在help裡以此來代表option後arguments, 預設是大寫option名
                           dest='tools', # 用什麼名稱access 此option後arguments, 預設是option名
                           help="specify one or two tools to tokenize." 
    )
    argParser.add_argument('-c','--chars',
                           type=int, # 要轉化成int
                           help="specify you want to count word with how many chars")
    argParser.add_argument('-m','--most',
                           type=int,
                           help="specify you want to know the most how many frequent words")
    args = argParser.parse_args() # parse a list of strings, defaults to sys.argv
    
    for tool in args.tools:
        statistic(tool, args.people ,args.chars, args.most)

#========================================================
#                       Test
#========================================================
# python Statistic.py --tool ckip jieba -chars 2 -most 5
# python Statistic.py -m 5 --tool jieba --people 何凡 何基明
