#!/bin/python3

import json
import pymongo

f = open('metadata.json')

metadata = json.load(f)

f.close()

try:
    docFileName = metadata['DocName']
    docContent = metadata['Content']
    docTopic = metadata['Topic']

except:
    print("Metadata format is illegal")
    exit()

print(docFileName)
print(docContent)

dbServer = pymongo.MongoClient("192.168.0.52",27017)
db = dbServer['webDataBase']
col = db['Topic']

for i in docTopic:
    print(i)
    payload = col.find_one({"TopicName": i})
    print(payload)
