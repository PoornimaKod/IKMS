# Class 12 Multi-Agent RAG Demo (IKMS)

This project is a **FastAPI** application designed to demonstrate a **Multi-Agent RAG (Retrieval-Augmented Generation)** pipeline. It allows users to upload PDF documents (specifically vector database papers), index them into a **Pinecone** vector store, and ask questions about the content.

## Features

-   **Question Answering**: Ask natural language questions about the indexed documents.
-   **Session History**: Supports conversational memory via `session_id`.
-   **PDF Indexing**: Upload and index PDF files directly via the API.
-   **Static UI**: Includes a simple static frontend for interaction.

## Tech Stack

-   **Backend**: Python, FastAPI
-   **Vector Store**: Pinecone
-   **LLM Orchestration**: LangChain, LangGraph
-   **PDF Processing**: PyPDF

## Installation

### Prerequisites

-   Python 3.11 or higher
-   Pinecone API Key

### Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    # using uv (recommended)
    uv venv
    # or using python
    python -m venv .venv
    
    # Activate script (Windows)
    .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    # using uv
    uv sync
    # or using pip
    pip install .
    ```

4.  **Environment Configuration**:
    Create a `.env` file in the root directory and add your Pinecone credentials:
    ```env
    PINECONE_API_KEY=your_pinecone_api_key
    PINECONE_ENV=your_pinecone_environment
    OPENAI_API_KEY=your_openai_api_key
    ```

## Usage

1.  **Start the server**:
    ```bash
    uvicorn src.app.api:app --reload
    ```

2.  **Access the API Documentation**:
    Open your browser and navigate to `http://127.0.0.1:8000/docs` to view the interactive API documentation (Swagger UI).

3.  **Access the UI**:
    Navigate to `http://127.0.0.1:8000/static/index.html` (if available) or simply use the root endpoint `http://127.0.0.1:8000/`.

## Endpoints

-   `POST /qa`: Submit a question.
-   `POST /index-pdf`: Upload and index a PDF file.
-   `GET /`: Health check / UI redirection.
