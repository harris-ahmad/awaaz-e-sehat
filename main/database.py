from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

URI = "mongodb+srv://harris:harris123@atlascluster.1jhzzr5.mongodb.net/?retryWrites=true&w=majority"

CLIENT = MongoClient(URI, server_api=ServerApi("1"))
DB = CLIENT["users"]

try:
    CLIENT.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
