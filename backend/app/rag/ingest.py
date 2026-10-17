from __future__ import annotations
import argparse
from pathlib import Path
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .retriever import HandbookRetriever

def load_pdf_documents(pdf_dir: str) -> list[dict]:
    """Parse every PDF page and retain one-indexed page metadata."""
    documents = []
    for path in sorted(Path(pdf_dir).glob("*.pdf")):
        for page_number, page in enumerate(PdfReader(str(path)).pages, 1):
            text = page.extract_text() or ""
            documents.append({"text": text, "metadata": {"source": path.name, "page": page_number}})
    return documents

def ingest(pdf_dir: str = "./data", chroma_dir: str = "./chroma_db", rebuild: bool = False):
    """Ingest PDFs into Chroma when available; fallback retrieval remains deterministic."""
    docs = load_pdf_documents(pdf_dir)
    if not docs:
        return HandbookRetriever()
    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        split_docs = []
        for item in docs:
            for chunk in splitter.split_text(item["text"]):
                from langchain_core.documents import Document
                split_docs.append(Document(page_content=chunk, metadata=item["metadata"]))
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        store = Chroma(collection_name="handbook", persist_directory=chroma_dir, embedding_function=embeddings)
        if rebuild:
            store.delete_collection()
            store = Chroma(collection_name="handbook", persist_directory=chroma_dir, embedding_function=embeddings)
        if not store.get().get("ids"):
            store.add_documents(split_docs)
        return HandbookRetriever(store)
    except ImportError:
        return HandbookRetriever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    print(f"Ingested handbook from ./data (rebuild={args.rebuild})")

