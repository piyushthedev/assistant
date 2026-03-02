# Broklin - Intelligent Voice Assistant

Broklin is a highly capable, multimodal AI voice assistant built for the web. It is designed to act as a personal assistant, offering conversational memory, voice interaction, image recognition, and custom knowledge retrieval using a Retrieval-Augmented Generation (RAG) pipeline.

## 🚀 What We Built (Project Overview)

In this project, we built a full-stack AI web application from the ground up:

1. **Intelligent Conversational AI:** Integrated Google's latest **Gemini 2.5 Flash** model via LangChain to provide incredibly fast and accurate human-like responses.
2. **Custom Knowledge Base (RAG):** Built a custom data ingestion pipeline that scrapes Wikipedia (specifically data about India), chunks the text, creates vector embeddings, and stores them in a **Pinecone Vector Database**. This allows Broklin to answer specific domain questions with factual background context.
3. **Multimodal Capabilities:** Implemented image uploading and processing, allowing the AI to "see" and analyze pictures provided by the user.
4. **Voice Interaction:** Wired up the browser's native **WebSpeech API** for Speech-to-Text (allowing users to talk to the AI) and **gTTS (Google Text-to-Speech)** to give the AI a voice to speak back.
5. **User Authentication & History:** Built a robust **Flask** backend using **SQLite** and **SQLAlchemy** to securely handle user signup/login, password hashing, and persistent chat history storage across sessions.
6. **Serverless Deployment Integration:** Architected the application to be fully compatible with Serverless environments. Completely refactored the codebase to bypass dynamic file-system limitations and successfully deployed the engine to **Vercel**.

## 🛠️ Skills and Technologies Used

### Frontend (Client-Side)
- **HTML5/CSS3:** For building a responsive, sleek, dark-themed user interface.
- **Vanilla JavaScript (ES6):** For handling asynchronous API calls, DOM manipulation, and UI state.
- **WebSpeech API:** For in-browser microphone recording and real-time Speech-to-Text translation (specifically tailored for Indian/Hindi accents).
- **Marked.js:** For rendering Markdown-formatted responses from the AI into clean HTML.

### Backend (Server-Side)
- **Python:** The core language powering the entire backend architecture.
- **Flask:** The lightweight web framework used to route HTTP requests, serve frontend templates, and manage API endpoints.
- **SQLAlchemy & SQLite:** For Object-Relational Mapping (ORM) and secure relational database management.
- **Werkzeug:** For secure cryptographic password hashing and verification.
- **gTTS:** For dynamically synthesizing audio files from the AI's response text.

### Artificial Intelligence & Data (AI/ML)
- **Google Gemini API (2.5 Flash):** The primary Large Language Model (LLM) powering reasoning, conversation, and computer vision.
- **LangChain:** The AI orchestration framework used to string together AI memory, custom prompt templates, and database retrievers.
- **Pinecone:** The serverless Vector Database used to store and query high-dimensional embeddings for the RAG pipeline.
- **BeautifulSoup (bs4) & Requests:** Used to build a custom web scraper for automated data ingestion from Wikipedia.

### DevOps & Cloud Deployment
- **Vercel / Serverless Functions:** For hosting the application globally in a serverless ecosystem.
- **Environment Variables (.env):** For handling secure cryptographic secrets and API keys safely.
- **Git & GitHub:** For version control, branching, and automated continuous deployment (CD).

## 🔮 The Future of the Project

Broklin has an extremely solid foundation that can be expanded in numerous directions. Future potential upgrades include:

1. **Live Web Searching:** Upgrading the LangChain agent to have internet access, allowing it to browse Google in real-time to answer questions about the live weather, news, or current events.
2. **Action Agents:** Giving the AI the ability to perform physical tasks on the internet for the user (e.g., booking an Uber, sending an email via Gmail API, adding events to Google Calendar).
3. **Expanded Vector Knowledge:** Creating a massive, automated pipeline to feed Broklin thousands of PDF documents (like textbooks, company manuals, or legal documents) so it can become a specialized expert in any field.
4. **Natural Conversational Voice:** Moving away from standard gTTS and implementing advanced voice synthesis engines like ElevenLabs for ultra-realistic, expressive voice acting.
5. **Mobile Application:** Wrapping the frontend into a progressive web app (PWA) or using React Native to publish Broklin to the iOS App Store and Google Play Store for native mobile usage.

## Setup & Local Installation

1. Clone the repository.
2. Create a virtual environment: `python3 -m venv venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`
4. Set up a `.env` file with your `GEMINI_API_KEY`, `PINECONE_API_KEY`, and a `SECRET_KEY`.
5. Run the web scraper to populate your vector database: `python scripts/scrape_india_data.py`
6. Start the server: `python app.py`
7. Open `http://localhost:5001` in your browser.
