# Summarize_People
Use 「History of City of Taipei」 as laguage material, summarize the lives of people recorded in it. 
  
# Prerequisite
jieba:  
`pip install jieaba`
  
ckip(中研院)  
1. 到官網申請線上服務(中研院斷詞沒有線下服務)
http://ckipsvr.iis.sinica.edu.tw/webservice.htm → 申請服務帳號 → 按此申請 → 到信箱啟動帳號 → 等待一段時間開通帳號  
2. 修改此目錄底下`config.ini.example`，將申請的帳號密碼寫入，並改名成`config.ini`  

# Usage
1. Convert pdf into biographies in txt, and create meta data schema for every biography  
`python ConverAndExtract.py`

2. Normalize text and extract some meta data(birth, death, ...) to biography  
`python Preprocess.py`

# More
See more explanation to know more about this project and help you figure out the code !!  
[Gihub Wiki](https://github.com/frankie8518/Summarize_People/wiki)
