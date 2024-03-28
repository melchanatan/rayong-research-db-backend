#!/bin/python3
import datetime
import os
from flask import Flask, abort, jsonify, make_response, request
from flask import send_file
from flask_cors import CORS, cross_origin
from pymongo.server_api import ServerApi

from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import json
import pymongo
import time
from dotenv import load_dotenv

load_dotenv()

archiveDirectory = 'DocArchive' + '/'

allowedFileExtension = ['xlsx','pdf','docx', 'csv']

app = Flask(__name__)
cors = CORS(app, support_credentials=True)

app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024 
app.config['UPLOAD_FOLDER'] = archiveDirectory

def bad_request(message):
    response = jsonify({'message': message})
    response.status_code = 400
    return response

@app.route("/ping")
def ping():
    return "pong"


@app.route("/getTopic", methods = ['GET'])
def SearchDocument():
    

    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    topicCollection = db['Topic']

    payload = []

    for iterPayload in topicCollection.find({},{"_id" : 0, "name" : 1, "tagColor" : 1, "docIDs" : 1}):
        docCount = len(iterPayload["docIDs"])
        if docCount > 0:
            payload.append(str({"name": iterPayload["name"], "tagColor": iterPayload["tagColor"], "researchCounts": docCount}))
    
    payload = "["+",".join(payload)+"]"

    return payload.replace("'",'"')

@app.route("/getDocID/<topic>", methods = ['GET'])
def GetDocumentSample(topic):

    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    topicCollection = db['Topic']

    payload = topicCollection.find_one({"name": topic},{"_id" : 0, "docIDs" : 1})
    for (i, e) in enumerate(payload["docIDs"]):
        payload["docIDs"][i] = str(e)
    
    return str(payload).replace("'",'"')
    
@app.route("/getDocData/<docID>", methods = ['GET'])
def GetDocumentData(docID):
    
    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    documentCollection = db['Doc']
    
    docID = ObjectId(docID)
    payload = documentCollection.find_one({"_id": docID},{"_id" : 0, "DocName" : 1, "Content" : 1, "DownloadCount" : 1})
    
    return str(payload).replace("'",'"')



@app.route("/getDoc/<docID>", methods = ['GET'])
def downloadDocument(docID):

    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    documentCollection = db['Doc']

    try:
        docID = ObjectId(docID)
        path = documentCollection.find_one({"_id": docID},{"_id":0, "Link":1})
        path = path["Link"]
         
        print(archiveDirectory + str(path))
    except:
        abort(400)

    documentCollection.update_one({"_id":docID},{"$inc":{"DownloadCount":1}})


    return send_file(archiveDirectory + str(path), as_attachment=True)



@app.route("/postDoc", methods = ['POST'])
def uploadDocument():
    
    # print(json_data.get('metadata')) 
    # Get files from POST request, metadata.json and document
    documents = request.files.getlist('files')
    metadata = request.files.getlist('metadata')
    
    print(documents)
    # Find metadata.json, isolate and save it
    if metadata is None:
        print("1")
        return bad_request("Request must contain metadata.json and document")

    metadata_data = metadata[0].read().decode('utf-8')
    metadata_data = json.loads(metadata_data)
    

    for (index, document) in enumerate(documents):

        # Check document file extension
        documentFile = documents[index].filename.split('.')[0]
        documentExtension = documents[index].filename.split('.')[-1]
        if not documentExtension in allowedFileExtension:
            print(documentExtension)
            abort(400)
        
        # Get the current timestamp
        current_timestamp = int(time.time())

        # Convert timestamp to datetime object
        dt = datetime.datetime.fromtimestamp(current_timestamp)

        # Get the date as a string
        date_str = dt.strftime("_%Y-%m-%d")
        # Avoid filename confict by adding epoch
        documentFile = documentFile + date_str + '.' + documentExtension


    # Parse .json file to mongodb
    try:
        research_header = metadata_data['header']
        research_abstract = metadata_data['abstract']
        research_organization = metadata_data.get('organization', "")
        research_email = metadata_data.get('contactEmail', "")
        research_researchers = metadata_data.get('researchers', "")
        research_topic = metadata_data['tag']
    except KeyError:
        print("err 12")

        abort(400)

    # Connect to database
    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    DocumentCollection = db['Doc']
    TopicCollection = db['Topic']
    print("err 2")

    # Turn metadata into document for mongodb
    payloadToDB = {"header" : research_header, "researchers" : research_researchers, "organization" : research_organization, "contactEmail" : research_email, "date" : time.asctime(time.gmtime()), "abstract" : research_abstract, "downloadCount": 0, "files": documentFile}
    
    docid = DocumentCollection.insert_one(payloadToDB)
    print(docid.inserted_id) 
    print("err 4")


  
    # Update Topic database
    TopicCollection.update_one(
        {"name": research_topic},
        {"$push":{"docIDs":ObjectId(docid.inserted_id)}},
        upsert=True)
    # TopicCollection.update_one(
    #     {"name": research_topic},
    #     {"$setOnInsert": {"tagColor": "#dddddd"}},
    #     upsert=True)
    TopicCollection.update_one(
        {"name": research_topic},
        {'$inc': {'docCount': 1}}
    )
    
    for (index, document) in enumerate(documents):
        print(documents[index])
        documents[index].save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(documentFile)))

    return "Uploaded"



@app.route("/addTopic", methods = ['POST'])
def addTopic():
    content_type = request.headers.get("Content-Type")
    if (content_type == 'application/json'):
        json = request.json
        try:
            payload = {"name" : str(json["name"]), "tagColor" : str(json["tagColor"]), "PosX" : int(json["PosX"]), "PosY" : int(json["PosY"]), "DocCount" : 0, "DocID" : []}
            
            dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI'),int(databasePort)))
            db = dbServer['webDataBase']
            TopicCollection = db['Topic']

            TopicCollection.insert_one(payload)
            return "Topic added"
        except:
            return "Json doesn't contain the data"


        return json
    else:
        return "Content is not json"

@app.route("/delDoc/<docID>", methods = ['GET'])
def deleteDocument(docID):
    
    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI'),int(databasePort)))
    db = dbServer['webDataBase']
    TopicCollection = db['Topic']
    DocCollection = db['Doc']

    path = DocCollection.find_one({"_id":ObjectId(docID)},{"_id":0, "Link":1}) 

    TopicCollection.update_many({"DocID": ObjectId(docID)},{"$inc" : {"DocCount":-1}})
    TopicCollection.update_many({"DocID": ObjectId(docID)},{"$pull" : {"DocID" : ObjectId(docID)}})

    DocCollection.delete_one({"_id" : ObjectId(docID)})


    os.remove(os.path.join(archiveDirectory, str(path["Link"])))


    return "Document deleted"



@app.route("/editDB", methods = ['POST'])
def editDatabase():
    return ""
# For debug purpose never deploy in production. 

@app.route("/login")
def loginCredential():
    respondPayload = make_response("login")
    respondPayload.set_cookie("auth-id", "LOWERCASE GUY", httponly = True, secure = False)
    return respondPayload

@app.route("/logout")
def logoutCredential():
    respondPayload = make_response("logout")
    respondPayload.set_cookie("auth-id", "", max_age=0)
    return respondPayload











