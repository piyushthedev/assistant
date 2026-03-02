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
        self._google_search_api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
        self._google_cse_id = os.environ.get("GOOGLE_CSE_ID")
        
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
                
                # System Prompt for Agent
                system_prompt = """You are a highly capable AI assistant named Broklin. Provide comprehensive, detailed answers to the user's questions. Do not restrict your length. 

You have access to a Google Search tool. If the user asks about live information, current events, recent news, the weather, sports scores, or anything that requires the real-time internet, YOU MUST use the Google Search tool to find the answer.

If background info is provided, prioritize answering using that background info in detail.

Current conversation:
{history}
"""
                
                from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
                
                self.prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])
                
                # Keep memory buffer
                self.memory = ConversationBufferMemory(memory_key="history", return_messages=True)
                
                # Tools will be bound during ask_gemini when Pinecone is ready
                
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

    def _get_agent_executor(self):
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        from langchain.tools import Tool
        
        tools = []
        
        # 1. Google Search Tool
        if self._google_search_api_key and self._google_cse_id:
            try:
                from langchain_community.utilities import GoogleSearchAPIWrapper
                search = GoogleSearchAPIWrapper(
                    google_api_key=self._google_search_api_key, 
                    google_cse_id=self._google_cse_id
                )
                tools.append(
                    Tool(
                        name="google_search",
                        description="Search Google for recent results, live news, current events, and weather.",
                        func=search.run,
                    )
                )
            except Exception as e:
                print(f"Failed to init Google Search Tool: {e}")

        # Create Agent
        agent = create_tool_calling_agent(self.llm, tools, self.prompt)
        return AgentExecutor(agent=agent, tools=tools, memory=self.memory, verbose=True)

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
                augmented_prompt = prompt
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
                if self.vectorstore:
                    docs = self.vectorstore.similarity_search(prompt, k=3)
                    if docs:
                        context = "\n\n".join([doc.page_content for doc in docs])
                        augmented_prompt = f"Background Information (Use this to answer the user if relevant):\n{context}\n\nUser Question: {prompt}"
                
                # Execute Agent
                agent_executor = self._get_agent_executor()
                response = agent_executor.invoke({"input": augmented_prompt})
                return response["output"].replace("*", "")
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
