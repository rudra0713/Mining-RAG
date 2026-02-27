import argparse
import os
import shutil
from pdf_splitter_test import extract_sections
from langchain.schema.document import Document
from langchain.vectorstores.chroma import Chroma
from chromadb import PersistentClient
from chromadb.config import Settings
from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"
DATA_PATH = "data"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    parser.add_argument("--pdf_path", type=str,
                        default="data/2024_Joint_Application_Information_Requirements.pdf",
                        help="Path to the PDF file.")
    parser.add_argument("--embedding", type=str, default="ollama_nomic",
                        choices=["ollama_nomic", "ollama_mxbai", "ollama_minilm", "openai", "bge_large", "e5_large", "mpnet", "bge_m3", "bedrock"],
                        help="Which embedding type to use.")
    args = parser.parse_args()

    if args.reset:
        print(f"✨ Clearing Database for embedding={args.embedding}")
        clear_database(args.embedding)

    documents = load_documents(args.pdf_path)
    add_to_chroma(documents, args.embedding)


def load_documents(pdf_path: str) -> list:
    sections = extract_sections(pdf_path)
    documents = []
    for section in sections:
        documents.append(Document(
            page_content=section["text"],
            metadata={
                "source": pdf_path,
                "section_number": section["section_number"],
                "title": section["title"],
                "page": section["page"]
            }
        ))
    print(f"total documents: {len(documents)}")
    return documents


def add_to_chroma(documents: list[Document], embedding_type: str):
    client = PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )

    collection_name = f"my_collection_{embedding_type}"
    db = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=get_embedding_function(embedding_type),
        collection_metadata={"hnsw:space": "cosine"}
    )

    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB ({collection_name}): {len(existing_ids)}")

    new_documents = [doc for doc in documents if doc.metadata["section_number"] not in existing_ids]
    if new_documents:
        print(f"👉 Adding new documents: {len(new_documents)}")
        new_doc_ids = [doc.metadata["section_number"] for doc in new_documents]
        db.add_documents(new_documents, ids=new_doc_ids)
    else:
        print("✅ No new documents to add")


def clear_database(embedding_type: str):
    collection_dir = os.path.join(CHROMA_PATH, f"my_collection_{embedding_type}")
    if os.path.exists(collection_dir):
        shutil.rmtree(collection_dir)
        print(f"Deleted collection: {collection_dir}")


if __name__ == "__main__":
    main()