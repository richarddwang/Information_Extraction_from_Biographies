import networkx as nx
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"

G = nx.Graph()

person = db.people.find(filter={'Name':""})
G.add_noed(person['Name'], aliases=person['Alias_s'])

