import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("d:\\STEMLink\\IKMS\\.env")

try:
    from src.app.core.retrieval.vector_store import index_documents
    print("Indexing test.pdf...")
    count = index_documents(Path("test.pdf"))
    print(f"Success! Indexed {count} chunks.")
except Exception as e:
    import traceback
    traceback.print_exc()
