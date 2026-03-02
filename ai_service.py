from config import Config
import google.generativeai as genai
import os
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# --- CONFIGURE KEYS HERE ---
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
        # Fetch keys dynamically so Vercel dotenv injection happens first
        self._gemini_key = Config.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY')
        self._openai_key = os.environ.get("OPENAI_API_KEY") 
        self._pinecone_key = os.environ.get("PINECONE_API_KEY")
        
        # Force the OS Environment to use the correct key so Langchain Embeddings don't fall back to old cached keys
        if self._gemini_key:
            os.environ['GOOGLE_API_KEY'] = self._gemini_key
            os.environ['GEMINI_API_KEY'] = self._gemini_key
        
        self.gemini_configured = False
        self.openai_configured = False
        self.conversation = None
        self.vectorstore = None
        
        # Setup Gemini
        if self._gemini_key:
            try:
                # Direct API for Images (Legacy/backup)
                genai.configure(api_key=self._gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Pinecone Vector Store will be lazy-loaded in ask_gemini()
                # LangChain Setup for Text (Memory)
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash", 
                    api_key=self._gemini_key,
                    temperature=0.7,
                    max_output_tokens=8192,
                    convert_system_message_to_human=True 
                )
                
                # System Prompt Template
                template = """You are a highly capable AI assistant named Broklin. Provide comprehensive, detailed, and completely expansive answers to the user's questions. Do not restrict your length. If background info is provided, prioritize answering using that background info in detail.

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
                self.gemini_init_error = None
            except Exception as e:
                import traceback
                self.gemini_init_error = f"Init crashed: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                print(f"Gemini Config Error: {self.gemini_init_error}")
        else:
            self.gemini_init_error = "GEMINI_API_KEY environment variable is empty or not loaded."

        # Setup OpenAI (Placeholder)
        if self._openai_key and self._openai_key != "YOUR-OPENAI-KEY-HERE":
            self.openai_configured = True

    def ask_gemini(self, prompt, image=None):
        if not self.gemini_configured:
            return f"Gemini configuration failed: {getattr(self, 'gemini_init_error', 'Unknown Error')}"
        try:
            if image:
                # Use direct API for images as LangChain memory + images is complex
                response = self.gemini_model.generate_content([prompt, image])
                return response.text.replace("*", "")
            else:
                # Lazy Load Vector Store for RAG if Pinecone is configured
                if self.vectorstore is None and self._pinecone_key and PineconeVectorStore:
                    print("Lazy Initializing Pinecone Vector Store...")
                    embeddings = GoogleGenerativeAIEmbeddings(
                        model="models/gemini-embedding-001", 
                        api_key=self._gemini_key
                    )
                    self.vectorstore = PineconeVectorStore(
                        index_name=PINECONE_INDEX_NAME, 
                        embedding=embeddings, 
                        pinecone_api_key=self._pinecone_key
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
