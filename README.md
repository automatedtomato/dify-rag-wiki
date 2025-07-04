# Dify-Powered Wikipedia Q\&A Chatbot Backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)

This is the backend system for a sophisticated Q&A chatbot powered by Dify. It leverages the entire Japanese Wikipedia as its knowledge base, providing a hybrid search API that combines high-speed keyword search (`pg_trgm`) with modern semantic search (`pg_vector`). The system is fully containerized with Docker for easy setup and reproducibility.

## Features

- **Robust & Decoupled Data Pipeline**: A multi-stage, resumable pipeline to parse the entire Wikipedia XML dump, insert it into a database, generate vector embeddings, and build all indexes.
- **Hybrid Search Engine**: Implements both keyword search (`pg_trgm` with GIN index) and vector search (`pg_vector` with HNSW index), providing a foundation for advanced, accurate information retrieval.
- **GPU-Accelerated Vectorization**: Utilizes NVIDIA GPUs via Docker to dramatically speed up the process of converting millions of articles into vector embeddings with Sentence Transformer models.
- **FastAPI Backend**: A modern, high-performance API server providing endpoints for hybrid search and a simple chat interface.
- **Dify Agent Integration**: Designed to integrate with a self-hosted Dify instance as a custom tool via a dynamically generated OpenAPI schema.
- **Fully Containerized & Networked**: Manages both this project and a local Dify instance via Docker Compose, bridging them with a shared network for stable inter-container communication.


## Architecture

The system operates with two main `docker-compose` projects communicating over a shared Docker network. The data preparation pipeline consists of a series of independent scripts, each with a single responsibility, ensuring robustness and maintainability.

### Tech Stack

-   **Backend**: Python, FastAPI, Pydantic
-   **Database**: PostgreSQL with `pg_trgm` & `pg_vector` extensions
-   **AI/ML**: Dify (Self-hosted), Sentence Transformers, PyTorch
-   **Infrastructure**: Docker, Docker Compose, NVIDIA Container Toolkit (for GPU on WSL2)

## Setup and Installation

This setup involves running two separate `docker-compose` projects (this project and Dify) and connecting them.

### Prerequisites

-   Git
-   Docker & Docker Compose
-   (Optional but Highly Recommended) An NVIDIA GPU with up-to-date drivers and NVIDIA Container Toolkit support for your OS (e.g., via Docker Desktop on WSL2).


## Setup and Installation

This setup involves running two separate `docker-compose` projects (this project and Dify) and connecting them.

### Prerequisites

  - Git
  - Docker & Docker Compose
  - (Optional but Highly Recommended) An NVIDIA GPU with up-to-date drivers and NVIDIA Container Toolkit support for your OS (e.g., via Docker Desktop on WSL2).

### Step 1: Clone Repositories

Clone this project and the official Dify repository.

```bash
git clone https://github.com/automatedtomato/dify-rag-wiki.git
cd dify-rag-wiki
# You are now in the chatbot project root

cd ..
git clone https://github.com/langgenius/dify.git
```

### Step 2: Create a Shared Docker Network

This allows the two separate projects to communicate. This only needs to be done once.

```bash
docker network create chatbot-network
```

### Step 3: Configure and Launch Services

You will need two separate terminals.

**In Terminal 1 (This Project):**

1.  Navigate to the `dify-rag-wiki` directory.
2.  Create your environment file: `cp .env.example .env`.
3.  Launch the containers.
      - **For GPU:** `docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build`
      - **For CPU:** `docker-compose up -d --build`

**In Terminal 2 (Dify Project):**

1.  Navigate to the `dify/docker` directory.
2.  Create the Dify environment file: `cp .env.example .env`.
3.  Modify `dify/docker/docker-compose.yml` to join the shared network (as we discussed, by adding `chatbot-network` to the top-level `networks:` block and to the `networks:` list of the `api`, `worker`, and `db` services).
4.  Launch the Dify containers: `docker-compose up -d`.

### Step 4: Run the Data Preparation Pipeline

This is a multi-step manual process. Execute these commands from the **root of the `dify-rag-wiki` project** on your **host machine (WSL2 terminal)**.

```bash
docker-compose exec python-dev python scripts/init_pipeline.py
```

Or instead, run separately:
```bash
# 1. Download all necessary data dumps
docker-compose exec python-dev python scripts/wiki_loader.py

# 2. Parse the main XML dump into an intermediate file
# This is a long, CPU-intensive process
docker-compose exec python-dev python scripts/wiki_parser.py

# 3. Insert the parsed data into the database
# This runs inside the container
docker-compose exec python-dev python scripts/inserter.py

# 4. Vectorize all articles (uses the host's GPU)
# This is a very long, GPU-intensive process
docker-compose exec python-dev python scripts/vectorizer.py

# 5. Create all final database indexes
# This is a very long, I/O-intensive process
docker-compose exec python-dev python scripts/index_generator.py
```

## Usage and Testing
Once the pipeline is complete, you can test the system in two ways.

### **1. Test the Backend API via Swagger UI**
This tests the API in isolation.
1. Navigate to `http://localhost:8088/docs` in your browser.
2. Find the `GET /api/articles/search` endpoint and expand it.
3. Click "Try it out", enter a query (e.g., `Dinosaurs`), and click "Execute".
4. You should receive a 200 OK response with a JSON list of the most relevant articles, found via the hybrid search, almost instantly.

### **2. Test with the Frontend and Dify**
This tests the full end-to-end application.
1. **Set up the Dify Tool:**
      - Access your local Dify instance (`http://localhost/`).
      - Create a new Agent type application.
      - Go to **Tools** -> **Add Tool** -> **Custom**.
      - Get the OpenAPI schema from `http://localhost:8088/openapi.json`.
      - **Modify the schema** to include a servers block pointing to the API container: `"servers": [ { "url": "http://dify-rag-dev:8000" } ]`.
      - Paste the modified schema into Dify and save the tool.
      - In the Agent's **Orchestration** view, add the tool and configure your prompt to use it.
2. **Run the Frontend Server:**
      - From the root of the `dify-rag-wiki project`, run the following command:
        ```Bash
        python -m http.server 8000 --directory ./frontend
        ```

3. **Chat!**
      - Open your browser and navigate to `http://localhost:8000`.
      - Start asking questions and see the full system in action.

## Troubleshooting

  - **Permission Denied on WSL2**: If you encounter `Permission Denied` errors related to the `./postgres-data` directory during a `docker-compose build` or other operations, run the following command on your WSL2 host after starting the containers for the first time:
    ```bash
    sudo chmod -R 777 ./postgres-data
    ```
  - **Out of Memory during Indexing**: If the `create_indexes.py` script fails due to memory, ensure you have set `mem_limit` and `shm_size` in your `docker-compose.yml` for the `db` service (e.g., `mem_limit: 4g`, `shm_size: 2g`).

## License

This project is licensed under the MIT License.

## Author
Hikaru Tomizawa

-----
