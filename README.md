# Summarize_People
Use 「History of City of Taipei」 as laguage material, summarize the lives of people recorded in it. 
  
# Prerequisite
jieba:  
`pip install jieaba`
  
ckip(中研院)  
1. 到官網申請線上服務(中研院斷詞沒有線下服務)
http://ckipsvr.iis.sinica.edu.tw → 線上服務申請 → 按此申請 → 到信箱啟動帳號 → 等待一段時間開通帳號  
2. 修改`config.ini.example`，將申請的帳號密碼寫入，並改名成`config.ini`  
  
# Usage
`python SplitAndExtract.py`
`python Tokenize.py <Tokenize tool> <ouput format> <path_to_txt_file / directory>`
<Tokenize tool> : `"jieba"` | `"ckip"`  
<ouput format> : `"shell"` (直接印在shell上) | `"txt"` | `"json"`
<path_to_txt_file / directory> : 例如 `"/home/shulin/Summarize_People/Texts/"` 或 `"/home/shulin/Summarize_People/Texts/何基明.txt"` (Windows的自行類推)  
  
# Regular Expression in SplitAndExtract
^ : 這裡是行首  
\w+ ： 一個以上的字符(人名)  
 ？ ：有可能有空白有可能沒有 (四字人名後面沒有空格)  
\.+ ：一個以上的.  
\d\d\d : 三個數字(頁數)  
$ ：這裡是行尾  
() : 括號裏面的pattern 所match到的東西形成一個group  
  
re.findall 會回傳list of tuples
每個tuple 代表一個對pattern的match 裡的groups, i.e. tuple為 (group1, group2, ...)  
第3個argument是flags, re.MULTILINE 是把認清字串是多行的，才能在pattern裡用 ^ 和 $
