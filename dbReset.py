#!/bin/python3

import pymongo
from bson.objectid import ObjectId

dbIp = "192.168.0.52"

dbServer = pymongo.MongoClient(dbIp,27017)
dbServer.drop_database("webDataBase")

db = dbServer["webDataBase"]
DocCollection = db["Doc"]

docDatabase = [
        {"DocName":"Robert Oppenheimer","Content":"Head of US's neuclear program.","DownloadCount":0,"Link":"RO123456.txt"},
        {"DocName":"Werner Heisenberg","Content":"Head of German's neuclear program.","DownloadCount":0,"Link":"WH123456.txt"},
        {"DocName":"Walter White","Content":"Best meth cook ever","DownloadCount":0,"Link":"WW123456.txt"},
        {"DocName":"Fritz Harber","Content":"A German chemist who invent fertilizer","DownloadCount":0,"Link":"FH123456.txt"},
        {"DocName":"Bawornsak Sakulkueakulsuk","Content":"Best FIBO lecturer","DownloadCount":0,"Link":"BS123456.txt"}
        ]

x = DocCollection.insert_many(docDatabase)

print(x.inserted_ids)
docId = x.inserted_ids

topicDatabase = [
    {"TopicName": "Physicist", "FieldColor": "Red", "posX": 0, "posY": 1, "DocID": [docId[0],docId[1]]},
    {"TopicName": "Chemist","FieldColor": "Green","posX": 10,"posY": 11,"DocID": [docId[2],docId[3]]},
    {"TopicName": "Lecturer","FieldColor": "Blue","posX": 20,"posY": 21,"DocID": [docId[2],docId[4]]}
]

TopicCollection = db["Topic"]
y = TopicCollection.insert_many(topicDatabase)

print(y.inserted_ids)
