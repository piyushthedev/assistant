from config import Config
import google.generativeai as genai
import os
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# --- CONFIGURE KEYS HERE ---
GEMINI_API_KEY = Config.GEMINI_API_KEY
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") 
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "india-knowledge"

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

try:
    from langchain_pinecone import PineconeVectorStore
except ImportError:
    PineconeVectorStore = None

class AIService:
    def __init__(self):
        self.gemini_configured = False
        self.openai_configured = False
        self.conversation = None
        self.vectorstore = None
        
        # Setup Gemini
        if GEMINI_API_KEY:
            try:
                # Direct API for Images (Legacy/backup)
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
                
                # Pinecone Vector Store will be lazy-loaded in ask_gemini()
                # LangChain Setup for Text (Memory)
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-lite", 
                    google_api_key=GEMINI_API_KEY,
                    temperature=0.7,
                    convert_system_message_to_human=True 
                )
                
                # System Prompt Template
                template = """You are a helpful voice assistant named Broklin. Answer concisely (max 2 sentences) for speech output. If background info is provided, prioritize answering using that background info.

Current conversation:
{history}
Human: {input}
Broklin:"""
                
                PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
                
                self.memory = ConversationBufferMemory(ai_prefix="Broklin")
                self.conversation = ConversationChain(
                    prompt=PROMPT,
                    llm=self.llm, 
                    verbose=True, 
                    memory=self.memory
                )
                
                self.gemini_configured = True
            except Exception as e:
                print(f"Gemini Config Error: {e}")

        # Setup OpenAI (Placeholder)
        if OPENAI_API_KEY and OPENAI_API_KEY != "YOUR-OPENAI-KEY-HERE":
            self.openai_configured = True

    def ask_gemini(self, prompt, image=None):
        if not self.gemini_configured:
            return "Gemini API key is missing."
        try:
            if image:
                # Use direct API for images as LangChain memory + images is complex
                response = self.gemini_model.generate_content([prompt, image])
                return response.text.replace("*", "")
            else:
                # Lazy Load Vector Store for RAG if Pinecone is configured
                if self.vectorstore is None and PINECONE_API_KEY and PineconeVectorStore:
                    print("Lazy Initializing Pinecone Vector Store...")
                    embeddings = GoogleGenerativeAIEmbeddings(
                        model="models/gemini-embedding-001", 
                        google_api_key=GEMINI_API_KEY
                    )
                    self.vectorstore = PineconeVectorStore(
                        index_name=PINECONE_INDEX_NAME, 
                        embedding=embeddings, 
                        pinecone_api_key=PINECONE_API_KEY
                    )

                # RAG: Retrieve context from Vector DB if available
                augmented_prompt = prompt
                if self.vectorstore:
                    docs = self.vectorstore.similarity_search(prompt, k=3)
                    if docs:
                        context = "\n\n".join([doc.page_content for doc in docs])
                        augmented_prompt = f"Background Information (Use this to answer the user if relevant):\n{context}\n\nUser Question: {prompt}"
                
                # Use LangChain for text (Preserves Memory)
                response = self.conversation.predict(input=augmented_prompt)
                return response.replace("*", "")
        except Exception as e:
            return f"Gemini Error: {e}"

    def ask_openai(self, prompt):
        if not self.openai_configured:
            return "OpenAI API key is missing. Please add it to ai_service.py."
        return "OpenAI is not yet fully implemented."

    def ask_ai(self, prompt, provider="gemini", image=None):
        """Unified method to ask AI."""
        if provider.lower() == "gemini":
            return self.ask_gemini(prompt, image)
        elif provider.lower() == "openai" or provider.lower() == "gpt":
            return self.ask_openai(prompt)
        else:
            return "Unknown AI provider."

# Create a singleton instance
ai = AIService()

def get_response(prompt, image=None):
    """Simple helper function for external modules."""
    print(f"DEBUG: ai_service.get_response called with prompt: {prompt[:50]}...")
    return ai.ask_ai(prompt, image=image)
