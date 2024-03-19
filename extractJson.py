#!/bin/python3
from pymongo.server_api import ServerApi

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

dbServer = pymongo.MongoClient("mongodb+srv://rayongcd:2iD6XuQNyGO8LkIw@rayong-research-db.itkvdme.mongodb.net/?retryWrites=true&w=majority&appName=rayong-research-db",server_api=ServerApi('1'))
db = dbServer['webDataBase']
col = db['Topic']

for i in docTopic:
    print(i)
    payload = col.find_one({"TopicName": i})
    print(payload)
