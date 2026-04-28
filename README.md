# Transaction Classifier

An intelligent transaction classification system that uses Machine Learning and Vector Similarity to automatically categorize financial transactions.

## 🚀 Overview

This project provides a full-stack solution for managing and classifying bank transactions. It uses natural language processing (NLP) to understand transaction descriptions and match them to categories based on semantic similarity.

### Key Features

-   **Automated Classification**: Uses `sentence-transformers` (`all-MiniLM-L6-v2`) to generate embeddings for transaction descriptions.
-   **Vector Database**: Leverages `pgvector` in PostgreSQL for efficient similarity searches and storage.
-   **Smart Mapping**: Automatically suggests categories based on the closest matches in the database.
-   **Category Management**: Create, rename, and delete custom categories.
-   **Web Interface**: Interactive Next.js dashboard for uploading CSVs, verifying predictions, and managing categories.
-   **Batch Processing**: Efficiently handle bulk updates and transaction uploads.

## 🏗️ Architecture

-   **Backend**: FastAPI (Python 3.12)
    -   `uv` for dependency management.
    -   `SQLAlchemy` ORM with `pgvector` integration.
    -   `sentence-transformers` for ML-powered embeddings.
-   **Frontend**: Next.js 14 (TypeScript)
    -   `Tailwind CSS` for styling.
    -   `Lucide React` for iconography.
    -   `Axios` for API communication.
-   **Database**: PostgreSQL with `pgvector` extension.
-   **Orchestration**: Docker Compose for seamless environment setup.

## 📂 Project Structure

```text
.
├── apps/
│   ├── api/          # FastAPI Backend
│   │   ├── src/      # Core logic (ML, DB, API)
│   │   └── tests/    # Backend test suite
│   └── web/          # Next.js Frontend
│       ├── src/      # Dashboard and Components
│       └── public/   # Static assets
├── Makefile          # Shortcut commands for development
└── docker-compose.yml # Full stack orchestration
```

## 🚦 Getting Started

### Prerequisites

-   [Docker](https://www.docker.com/) and Docker Compose
-   [uv](https://github.com/astral-sh/uv) (for local backend development)
-   [Node.js](https://nodejs.org/) (for local frontend development)

### Quick Start (Docker)

To run the entire stack (API, Web UI, and Database):

```bash
docker-compose up --build
```

-   **Web UI**: `http://localhost:3000`
-   **API**: `http://localhost:8000`
-   **API Docs**: `http://localhost:8000/docs`

### Local Development

#### Backend (API)

1.  Navigate to the api directory: `cd apps/api`
2.  Install dependencies: `uv sync`
3.  Run tests: `make test` (from root) or `uv run pytest`

#### Frontend (Web)

1.  Navigate to the web directory: `cd apps/web`
2.  Install dependencies: `npm install`
3.  Start dev server: `npm run dev`

## 🛠️ Development Tools

The root `Makefile` provides shortcuts for common tasks:

| Command | Description |
| :--- | :--- |
| `make install` | Sync backend dependencies using `uv`. |
| `make test` | Run backend pytest suite. |
| `make lint` | Run Ruff linter. |
| `make format` | Format code with Ruff. |
| `make typecheck` | Run MyPy type checks. |

## 🧠 How it Works

1.  **Ingestion**: When a CSV is uploaded, descriptions are cleaned and pre-processed.
2.  **Embedding**: Each description is converted into a 384-dimensional vector using a Sentence Transformer model.
3.  **Classification**: 
    -   The system looks for similar previously-categorized transactions using cosine similarity.
    -   It applies a mapping logic to suggest the most likely category.
4.  **Verification**: Users can verify predictions in the UI, which improves the system's accuracy as the database grows.
