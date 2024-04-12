from pymongo import MongoClient
import os

from dotenv import load_dotenv
load_dotenv()

MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_CLUSTER_ADDRESS = os.getenv('MONGO_CLUSTER_ADDRESS')
MONGO_APP = os.getenv('MONGO_APP')

uri = f'mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER_ADDRESS}/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&appName={MONGO_APP}'
client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)