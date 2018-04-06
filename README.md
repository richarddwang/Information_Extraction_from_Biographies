# Summarize_People
Use 「History of City of Taipei」 as laguage material, summarize the lives of people recorded in it. 

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