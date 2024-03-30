#!/bin/python3
import datetime
import os
import random
from flask import Flask, abort, jsonify, make_response, request
from flask import send_file
from flask_cors import CORS, cross_origin
from pymongo.server_api import ServerApi
import colorsys

from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import json
import pymongo
import time
from dotenv import load_dotenv

load_dotenv()

allowedFileExtension = ['xlsx','pdf','docx', 'csv']

app = Flask(__name__)
cors = CORS(app, support_credentials=True)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024 
app.config['UPLOAD_FOLDER'] = str(os.getenv('ARCHIVE_DIRECTORY'))

print(os.path.join(os.path.abspath(os.sep), app.config['UPLOAD_FOLDER'],"ues"))
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

@app.route("/getDocsSnippet/<topic>", methods = ['GET'])
def GetDocumentSnippet(topic):
    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    documentCollection = db['Doc']
    topicCollection = db['Topic']
    
    allDocsId = topicCollection.find_one({"name": topic},{"_id" : 0, "docIDs" : 1})
    
    if allDocsId is None or len(allDocsId["docIDs"]) <= 0:
        return bad_request("Topic not found")
    
    for (i, e) in enumerate(allDocsId["docIDs"]):
        allDocsId["docIDs"][i] = str(e)
         
    payload = []
    for (i, e) in enumerate(allDocsId["docIDs"]):
        document = documentCollection.find_one({"_id": ObjectId(e)},{"_id" : 0, "header" : 1, "abstract" : 1, "organization" : 1, "date": 1})
        if document is None:
            continue
        document["id"] = allDocsId["docIDs"][i]
        payload.append(document)

    return payload
    
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
    payload = documentCollection.find_one({"_id": docID},{"_id" : 0, "header" : 1, "abstract" : 1, "downloadCount" : 1, "files": 1, "contactEmail": 1, "date": 1, "organization" : 1, "researchers": 1})
    
    return str(payload).replace("'",'"')



@app.route("/downloadDoc/<docID>/<index>", methods = ['GET'])
def downloadDocument(docID, index):

    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    documentCollection = db['Doc']

    try:
        index = int(index)
        if index < 0:
            abort(400)

        docID = ObjectId(docID)
        path = documentCollection.find_one({"_id": docID},{"_id":0, "files":1})
        print(path)
        path = path["files"][index]

        print(os.path.join(app.config['UPLOAD_FOLDER'], str(path)))
    except Exception as e:
        print(os.path.join(app.config['UPLOAD_FOLDER'], str(path)))
        print(e)
        abort(400)

    documentCollection.update_one({"_id":docID},{"$inc":{"DownloadCount":1}})

    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], str(path)), as_attachment=True)



@app.route("/postDoc", methods = ['POST'])
def uploadDocument():
    
    # print(json_data.get('metadata')) 
    # Get files from POST request, metadata.json and document
    documents = request.files.getlist('files')
    metadata = request.files.getlist('metadata')
    
    print(documents)
    # Find metadata.json, isolate and save it
    if metadata is None:
        return bad_request("Request must contain metadata.json and document")

    metadata_data = metadata[0].read().decode('utf-8')
    metadata_data = json.loads(metadata_data)
    

    # Get the current timestamp
    current_timestamp = int(time.time())

    # Convert timestamp to datetime object
    dt = datetime.datetime.fromtimestamp(current_timestamp)

    # Get the date as a string
    date_str = dt.strftime("_%Y-%m-%d")
    
    documentFiles = []
    for (index, document) in enumerate(documents):

        # Check document file extension
        file_buffer = documents[index].filename.split('.')[0]
        documentExtension = documents[index].filename.split('.')[-1]
        if not documentExtension in allowedFileExtension:
            print(documentExtension)
            abort(400)
        
        # Avoid filename confict by adding epoch
        documentFiles.append(file_buffer + date_str + '.' + documentExtension)

    print("pass check document file")
    # Parse .json file to mongodb
    try:
        research_header = metadata_data['header']
        research_abstract = metadata_data['abstract']
        research_organization = metadata_data.get('organization', "")
        research_email = metadata_data.get('contactEmail', "")
        research_researchers = metadata_data.get('researchers', "")
        research_topic = metadata_data['tag']
    except KeyError:
        abort(400)

    # Connect to database
    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    DocumentCollection = db['Doc']
    TopicCollection = db['Topic']

    # Turn metadata into document for mongodb
    payloadToDB = {"header" : research_header, "researchers" : research_researchers, "organization" : research_organization, "contactEmail" : research_email, "date" : time.asctime(time.gmtime()), "abstract" : research_abstract, "downloadCount": 0, "files": documentFiles, "tag": research_topic}
    
    docid = DocumentCollection.insert_one(payloadToDB)

      # Update Topic database
    TopicCollection.update_one(
        {"name": research_topic},
        {"$setOnInsert": {"tagColor": generate_pleasing_color()}},
        upsert=True
    )
    TopicCollection.update_one(
        {"name": research_topic},
        {"$push":{"docIDs":ObjectId(docid.inserted_id)}},
    )
    TopicCollection.update_one(
        {"name": research_topic},
        {'$inc': {'docCount': 1}}
    )
    
    print("pass update topic database")

    print(str(os.path.join(app.config['UPLOAD_FOLDER'])))
    print(str(os.path.abspath(os.sep)))
    print(str(os.path.join(os.path.abspath(os.sep), app.config['UPLOAD_FOLDER'], documentFiles[index])))

    for (index, document) in enumerate(documents):
        print(documents[index])
        print(documentFiles[index])
        
        try:
            documents[index].save(os.path.join(app.config['UPLOAD_FOLDER'], documentFiles[index]))
        except Exception as err:
            print(err)

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
    
    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    TopicCollection = db['Topic']
    DocCollection = db['Doc']

    path = DocCollection.find_one({"_id":ObjectId(docID)},{"_id":0, "files":1, "tag":1}) 

    TopicCollection.update_one({"name": path["tag"]},{"$inc" : {"docCount":-1}})
    TopicCollection.update_one({"name": path["tag"]},{"$pull" : {"docIDs" : ObjectId(docID)}})

    DocCollection.delete_one({"_id" : ObjectId(docID)})
    TopicCollection.delete_many({"docCount":0})

    for (index, files) in enumerate(path["files"]):
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], str(files)))
        except:
            abort("File not found")

    return "Document deleted"


@app.route("/getTopicColor/<topic>", methods = ['GET'])
def getTopicColor(topic):
    dbServer = pymongo.MongoClient(str(os.getenv('MONGO_DB_URI')),server_api=ServerApi('1'))
    db = dbServer['webDataBase']
    TopicCollection = db['Topic']
    topic = TopicCollection.find_one({"name": topic},{"_id":0, "tagColor":1})
    print(topic)
    
    if topic is None:
        abort("Topic not found")
    return topic


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

def generate_pleasing_color():
    """Generate a pleasing color using the HSL color model."""
    hue = random.random()

    # Choose a random saturation value between 0.5 and 0.9 (moderately high to high saturation)
    saturation = random.uniform(0.5, 0.9)

    # Choose a random lightness value between 0.3 and 0.7 (moderately low to moderately high lightness)
    lightness = random.uniform(0.3, 0.7)
    # Convert HSL to RGB
    rgb = colorsys.hls_to_rgb(hue, lightness, saturation)

    # Convert RGB values to integers between 0 and 255
    r, g, b = [int(x * 255) for x in rgb]
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)











