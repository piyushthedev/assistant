import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Langchain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Load environment variables
load_dotenv()

# Ensure keys are present
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "india-knowledge"

if not GEMINI_API_KEY or not PINECONE_API_KEY:
    print("Error: GEMINI_API_KEY and PINECONE_API_KEY must be set in your .env file.")
    exit(1)

# List of Wikipedia pages about India to scrape
URLS = [
    "https://en.wikipedia.org/wiki/India",
    "https://en.wikipedia.org/wiki/History_of_India",
    "https://en.wikipedia.org/wiki/Geography_of_India",
    "https://en.wikipedia.org/wiki/Economy_of_India",
    "https://en.wikipedia.org/wiki/Culture_of_India",
    "https://en.wikipedia.org/wiki/Politics_of_India",
    "https://en.wikipedia.org/wiki/Demographics_of_India",
    "https://en.wikipedia.org/wiki/Foreign_relations_of_India",
    "https://en.wikipedia.org/wiki/States_and_union_territories_of_India"
]

def scrape_wikipedia_text(url):
    print(f"Scraping: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return ""
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract only paragraph texts from the main content area
    content_div = soup.find(id="mw-content-text")
    if not content_div:
        return ""
        
    paragraphs = content_div.find_all('p')
    text = "\n\n".join([p.get_text() for p in paragraphs if p.get_text().strip() != ""])
    return text

def main():
    print("Starting data ingestion process...")
    all_text = ""
    for url in URLS:
        text = scrape_wikipedia_text(url)
        all_text += text + "\n\n"
        
    print(f"Total characters scraped: {len(all_text)}")
    
    # Chunk the text
    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.create_documents([all_text])
    # Add source metadata
    for chunk in chunks:
        chunk.metadata = {"source": "Wikipedia - India Custom Intelligence"}

    print(f"Created {len(chunks)} chunks.")
    
    # Initialize embeddings
    print("Initializing Google Gemini Embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Upload to Pinecone
    print(f"Uploading vectors to Pinecone index: '{PINECONE_INDEX_NAME}'...")
    PineconeVectorStore.from_documents(
        chunks, 
        embeddings, 
        index_name=PINECONE_INDEX_NAME
    )
    
    print("Upload complete! The custom dataset is ready for the RAG pipeline.")

if __name__ == "__main__":
    main()
