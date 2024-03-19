#!/bin/python3
from pymongo.server_api import ServerApi

import pymongo

dbServer = pymongo.MongoClient("mongodb+srv://rayongcd:2iD6XuQNyGO8LkIw@rayong-research-db.itkvdme.mongodb.net/?retryWrites=true&w=majority&appName=rayong-research-db",server_api=ServerApi('1'))

db = dbServer['webDataBase']

col = db["Doc"]

print("Document database")

for x in col.find():
    print(x)


print("")
print("")
print("Topic database")

col2 = db["Topic"]
for x in col2.find():
    print(x)
