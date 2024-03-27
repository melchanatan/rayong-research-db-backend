#!/bin/python3

import pymongo

dbServer = pymongo.MongoClient("192.168.0.52",27017)

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
