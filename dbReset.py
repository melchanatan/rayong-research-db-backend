#!/bin/python3
from pymongo.server_api import ServerApi

import pymongo
from bson.objectid import ObjectId

dbIp = "mongodb+srv://rayongcd:2iD6XuQNyGO8LkIw@rayong-research-db.itkvdme.mongodb.net/?retryWrites=true&w=majority&appName=rayong-research-db"

dbServer = pymongo.MongoClient(dbIp,server_api=ServerApi('1'))
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
    {"name": "Physicist", "tagColor": "#D95030", "docIDs": [docId[0],docId[1]]},
    {"name": "Chemist","tagColor": "#354D73", "docIDs": [docId[2],docId[3]]},
    {"name": "Lecturer","tagColor": "#6D3F5B", "docIDs": [docId[2],docId[4]]}
]

TopicCollection = db["Topic"]
y = TopicCollection.insert_many(topicDatabase)

print(y.inserted_ids)
