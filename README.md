# Information_Extraction_from_Biographies
An exploration on NLP methods for information extraction from biographies, with *Extended Taipei Gazetteers*.  
  
[Overview](#overview)  
[Name Entity Recognition](#1pre%20requisite)  
[Usage](#usage)  
[Wiki]()  

# Overview
We propose and implement some new NLP methods for information extraction.
## 1. Name Entity Recognition (NER)
## 2. Relation Extraction
## 3. Weighted Cooccurrence Rank
## 4. Automatically Timeline Generation

# Usage
## Prerequisite
1. Python3 (we develope with Python 3.6)
2. `pip insstall -r requirements.txt` to install all required python packages
3. [MongoDB](https://docs.mongodb.com/manual/administration/install-community/)
4. [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/download.html)  
  download main program and unzip it somewhere  
  download Chinese model jar and move into the Stanford CoreNLP direcotry you just unzipped.
  
## Execution
1. Start MongoDB daemon.  
  `sudo service mongod start` (in Ubuntu)
2. Start CoreNLP server.  
  in Stanford CoreNLP directory, execute command `java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -serverProperties StanfordCoreNLP-chinese.properties -port 9000 -timeout 15000`
3. Execute main pipeline process, and wait for several minutes.  
  `python3 main.py`
4. Results are in `./Database`  
  some results are also kept in MongoDB. (see Wiki:Data)  
  note that graph result is store in `.graphml` format, you can import it to [Gephi](https://gephi.org/) or [Cytoscape](http://www.cytoscape.org/) or whatever you like
