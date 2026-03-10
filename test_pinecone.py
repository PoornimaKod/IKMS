from dotenv import load_dotenv
import os
from pinecone import Pinecone

load_dotenv("d:\\STEMLink\\IKMS\\.env")

try:
    print("Initializing Pinecone...")
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    print("Fetching index stats...")
    stats = index.describe_index_stats()
    print("Success! Stats:", stats)
except Exception as e:
    import traceback
    traceback.print_exc()
