from stardict import StarDict
dic = StarDict("ecdict_sqlite")

word = "include"
print(dic.query(word))
