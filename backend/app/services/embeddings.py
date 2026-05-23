# embeddings.py
# Real RAG using Gemini embeddings API
# No local model download needed - runs on Google's servers

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import GEMINI_API_KEY
import os

SCHEMES_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../data/schemes/schemes.txt"
)
CHROMA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../data/chroma_db"
)

# Gemini embedding model - free, no download, supports Hindi
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GEMINI_API_KEY
)

def get_vectorstore():
    # If already exists, load it
    if os.path.exists(CHROMA_PATH) and os.listdir(CHROMA_PATH):
        print("Loading existing ChromaDB...")
        return Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings
        )

    print("Creating ChromaDB for first time...")

    # Load schemes text file
    loader = TextLoader(SCHEMES_PATH, encoding="utf-8")
    documents = loader.load()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    print("ChromaDB ready")
    return vectorstore


vectorstore = get_vectorstore()


def get_relevant_schemes(query: str) -> str:
    """Search ChromaDB for relevant scheme information"""
    try:
        results = vectorstore.similarity_search(query, k=3)
        if not results:
            return "Koi relevant scheme nahi mili. PM Kisan, Fasal Bima, KCC ke baare mein poochh sakte hain."

        # Combine top 3 results
        combined = "\n\n".join([doc.page_content for doc in results])
        return combined

    except Exception as e:
        return "Scheme information abhi available nahi hai. Baad mein try karein."