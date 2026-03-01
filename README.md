# AI Personal Knowledge Assistant (Mini-RAG)

A full-stack AI application that allows users to upload documents (PDFs), process them into embeddings, and query them using retrieval-augmented generation (RAG). Built with FastAPI backend and Streamlit frontend.

## Features

- 📄 **PDF Upload & Processing** - Upload and process PDF documents
- 🔍 **Semantic Search** - Search through documents using embeddings
- 🤖 **RAG-Based Querying** - Get answers from your uploaded documents
- 👤 **User Authentication** - Secure user accounts with JWT authentication
- 📊 **Vector Storage** - FAISS-based vector database for efficient similarity search
- 🎨 **Interactive UI** - Streamlit-based frontend for easy interaction

## Project Structure

```
ai-knowledge-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── core/
│   │   │   └── security.py         # JWT authentication logic
│   │   ├── db/
│   │   │   └── database.py         # Database configuration
│   │   ├── models/
│   │   │   ├── user.py             # User database model
│   │   │   └── schemas.py          # Pydantic schemas
│   │   ├── routes/
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── upload.py           # Document upload endpoints
│   │   │   └── query.py            # Query endpoints
│   │   └── services/
│   │       └── ingestion.py        # PDF processing & embeddings
│   ├── docker/                     # Docker configuration
│   ├── requirements.txt            # Python dependencies
│   └── rag.db                      # SQLite database
├── frontend/
│   └── app.py                      # Streamlit application
├── vector_store/                   # User vector stores
└── README.md
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **JWT** - Secure authentication
- **FAISS** - Vector similarity search
- **Sentence Transformers** - Embedding generation
- **PyPDF** - PDF text extraction

### Frontend
- **Streamlit** - Interactive web UI framework

## Installation

### Prerequisites
- Python 3.9+
- pip or conda package manager

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/SanviShan25/AI-Personal-Knowledge-Assistant-Mini-RAG.git
cd ai-knowledge-assistant
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

Backend:
```bash
cd backend
pip install -r requirements.txt
```

Frontend:
```bash
cd frontend
pip install streamlit
```

## Running the Application

### Backend (FastAPI)

```bash
cd backend
uvicorn app.main:app --reload
```
Backend runs at: `http://localhost:8000`

API Documentation available at: `http://localhost:8000/docs`

### Frontend (Streamlit)

```bash
cd frontend
streamlit run app.py
```
Frontend runs at: `http://localhost:8501`

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /me` - Get current user info

### Documents
- `POST /upload/` - Upload PDF document
- `POST /query/` - Query documents

## How It Works

1. **User Registration & Login** - Secure account creation with JWT tokens
2. **Document Upload** - Upload PDFs which are stored in user-specific directories
3. **Text Extraction** - Extract text from PDFs using PyPDF
4. **Text Chunking** - Split documents into meaningful chunks
5. **Embedding Generation** - Convert chunks to embeddings using `all-MiniLM-L6-v2` model
6. **Vector Storage** - Store embeddings in FAISS for fast similarity search
7. **Query Processing** - Search relevant chunks and generate responses based on document context

## Environment Variables

Create a `.env` file in the backend directory (optional):
```
DATABASE_URL=sqlite:///./rag.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Contributing

Feel free to fork this project and submit pull requests for any improvements.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Made by:** Sanvi and Harshit  
**Repository:** https://github.com/SanviShan25/AI-Personal-Knowledge-Assistant-Mini-RAG
