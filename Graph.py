import networkx as nx
import os
from pymongo import MongoClient
client = MongoClient('localhost', 27017) # create a connection to Mongodb
db = client['Summary'] # access database "Summary"
COOCCURRENCE_ZOOM_FACTOR = 1.2

def insert_all_people_as_nodes(G):
    for person in db.people.find():
        name = person['Name']
        G.add_node(name)
        for (aliasType, alias) in person['Alias_s']:
            G.nodes[name][aliasType] = alias
    
def generate_cooccurrenceGraph():
    G = nx.Graph()
    # Nodes
    insert_all_people_as_nodes(G)

    # Edges
    for cooccurrence in db.cooccurrences.find():
        score = round(cooccurrence['Score'] * COOCCURRENCE_ZOOM_FACTOR, 2)
        G.add_edge(cooccurrence['Name1'], cooccurrence['Name2'], weight=score)

    # Output
    nx.write_graphml(G, "./DataBase/graph/cooccurrence.graphml")

def generate_relationGraph():
    DG = nx.DiGraph()
    # Nodes
    insert_all_people_as_nodes(DG)

    # Edges
    for relation in db.relations.find():
        DG.add_edge(relation['Name1'], relation['Name2'], Relation=relation['Relation'])

    # Output
    nx.write_graphml(DG, "./DataBase/graph/relation_network.graphml", )

def main():
    try:
        os.makedirs("./DataBase/graph")
    except FileExistsError:
        pass
    
    generate_relationGraph()
    generate_cooccurrenceGraph()

if __name__ == "__main__":
    main()
