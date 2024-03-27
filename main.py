#!/bin/python3
import os
from flask import Flask, abort, make_response, request
from flask import send_file
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import json
import pymongo
import time


#Database setup
databaseIP = "172.0.0.1"
databasePort = 27017

archiveDirectory = 'DocArchive' + '/'

allowedFileExtension = ['txt','pdf','docx']



app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024 
app.config['UPLOAD_FOLDER'] = archiveDirectory

@app.route("/ping")
def ping():
    return "pong"



@app.route("/getTopic", methods = ['GET'])
def SearchDocument():
    
    user_auth = request.cookies.get('auth-id')
    
    if not validateAuthID(user_auth):
        abort(401)

    dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
    db = dbServer['webDataBase']
    topicCollection = db['Topic']

    payload = []

    for iterPayload in topicCollection.find({},{"_id" : 0, "TopicName" : 1, "FieldColor" : 1, "posX" : 1, "posY" : 1, "DocCount" : 1}):
        payload.append(str(iterPayload))
    
    payload = "["+",".join(payload)+"]"

    return payload.replace("'",'"')



@app.route("/getDocID/<topic>", methods = ['GET'])
def GetDocumentSample(topic):

    user_auth = request.cookies.get('auth-id')
    
    if not validateAuthID(user_auth):
        abort(401)

    dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
    db = dbServer['webDataBase']
    topicCollection = db['Topic']

    payload = []
    topic = topic.split('&')
    for t in topic:
        
        payload.append(topicCollection.find_one({"TopicName": t},{"_id" : 0, "TopicName" : 1 ,"DocID" : 1}))
    
    
    return str(payload).replace("'",'"')
    



@app.route("/getDocData/<docID>", methods = ['GET'])
def GetDocumentData(docID):
    user_auth = request.cookies.get('auth-id')
    
    if not validateAuthID(user_auth):
        abort(401)

    
    dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
    db = dbServer['webDataBase']
    documentCollection = db['Doc']
    
    payload = []
    docID = docID.split('&')
    for i in docID:
        i = ObjectId(i)
        payload.append(documentCollection.find_one({"_id": i},{"_id" : 0, "DocName" : 1, "Author" : 1,"PubDate" : 1, "Content" : 1, "DownloadCount" : 1}))
    
    return str(payload).replace("'",'"')



@app.route("/getDoc/<docID>", methods = ['GET'])
def downloadDocument(docID):
    user_auth = request.cookies.get('auth-id')

    if not validateAuthID(user_auth):
        abort(401)

    dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
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


    return send_file(os.path.join(archiveDirectory, str(path)), as_attachment=True)



@app.route("/postDoc", methods = ['POST'])
def uploadDocument():
    
    #Get user authentication
    user_auth = request.cookies.get('auth-id')
    
    if not validateAuthID(user_auth):
        abort(401)

    # Get files from POST request, metadata.json and document
    files = request.files.getlist('files')

    if len(files) != 2:
        abort(400)

    # Find metadata.json, isolate and save it
    inputFileName = [files[0].filename, files[1].filename]
    
    if not 'metadata.json' in inputFileName:
        abort(400)

    metadataFileIndex = inputFileName.index("metadata.json")
    files[metadataFileIndex].save(secure_filename("metadata.json"))
    files.pop(metadataFileIndex)
    
    
    # Check document file extension
    documentFile = files[0].filename.split('.')[0]
    documentExtension = files[0].filename.split('.')[-1]
    if not documentExtension in allowedFileExtension:
        abort(400)
    
    
    # Avoid filename confict by adding epoch
    documentFile = documentFile + str(int(time.time())) + '.' + documentExtension


    # Parse .json file to mongodb
    try:
        f = open("./metadata.json")
        metadata = json.load(f)
        f.close()
        docFileName = metadata['DocName']
        docContent = metadata['Content']
        docAuthor = metadata['Author']
        docTopic = metadata['Topic']

    except:
        return "Bad metadata file"

    # Connect to database
    dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
    db = dbServer['webDataBase']
    DocumentCollection = db['Doc']
    TopicCollection = db['Topic']

    # Find topic
    uniqueTopic = []
    for Top in docTopic:
        if TopicCollection.find_one({"TopicName": Top}) is None:
            return Top + " topic doesn't exist in the database."
        if Top in uniqueTopic:
            return "Topic name repeated"
        uniqueTopic.append(Top)

    # Turn metadata into document for mongodb
    payloadToDB = {"DocName" : docFileName, "Author" : docAuthor, "PubDate" : time.asctime(time.gmtime()), "Content" : docContent, "DownloadCount": 0, "Link": documentFile}

    docid = DocumentCollection.insert_one(payloadToDB)    
    
    # Update Topic database
    for Top in docTopic:
        TopicCollection.update_one({"TopicName": Top},{"$push":{"DocID":ObjectId(docid.inserted_id)}})
        TopicCollection.update_one({"TopicName": Top},{'$inc': {'DocCount': 1}})
    
    files[0].save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(documentFile)))

    return "Uploaded"

@app.route("/delDoc/<docID>", methods = ['GET'])
def deleteDocument(docID):
    
    dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
    db = dbServer['webDataBase']
    DocumentCollection = db['Doc']
    TopicCollection = db['Topic']
    DocCollection = db['Doc']

    path = DocCollection.find_one({"_id":ObjectId(docID)},{"_id":0, "Link":1}) 

    TopicCollection.update_many({"DocID": ObjectId(docID)},{"$inc" : {"DocCount":-1}})
    TopicCollection.update_many({"DocID": ObjectId(docID)},{"$pull" : {"DocID" : ObjectId(docID)}})

    DocCollection.delete_one({"_id" : ObjectId(docID)})


    os.remove(os.path.join(archiveDirectory, str(path["Link"])))


    return "Document deleted"


@app.route("/addTopic", methods = ['POST'])
def addTopic():
    content_type = request.headers.get("Content-Type")
    if (content_type == 'application/json'):
        json = request.json
        try:
            payload = {"TopicName" : str(json["TopicName"]), "FieldColor" : str(json["FieldColor"]), "PosX" : int(json["PosX"]), "PosY" : int(json["PosY"]), "DocCount" : 0, "DocID" : []}
            
            dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
            db = dbServer['webDataBase']
            TopicCollection = db['Topic']

            TopicCollection.insert_one(payload)
            
            return "Topic added"

        except:
            return "Json doesn't contain the data"


        return json
    else:
        return "Content is not json"



@app.route("/removeTopic/<top>", methods = ['GET'])
def removeTopic(top):
    
    dbServer = pymongo.MongoClient(str(databaseIP),int(databasePort))
    db = dbServer['webDataBase']
    TopicCollection = db['Topic']

    x = TopicCollection.delete_one({"TopicName" : top})
    
    if x.deleted_count < 1:
        return "Topic not in database"

    return "Topic removed"

def validateAuthID(auth):
    #if auth in authCache:
    #    return True
    #
    #if auth == 'LOWERCASE GUY':
    #    authCache.append(auth)
    #    return True

    return True


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











