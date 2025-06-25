# Dify-Powered Wikipedia Q\&A Chatbot Backend

A backend system designed to power a Dify AI chatbot with the entire Japanese Wikipedia as its knowledge base. This project provides a high-speed, full-text search API that can be integrated into Dify as a custom tool, enabling the chatbot to answer questions based on verified information.

## Features

  - **Complete Data Pipeline**: Ingests and processes the entire Japanese Wikipedia XML dump.
  - **High-Speed Full-Text Search**: Utilizes PostgreSQL and the `pg_trgm` extension with GIN indexes to perform fast searches across millions of articles.
  - **FastAPI Backend**: A robust and modern API server built with FastAPI, providing endpoints for search and chat.
  - **Dify Agent Integration**: Seamlessly integrates with a self-hosted Dify instance as a custom API tool.
  - **Chat History Management**: Persists conversation history in the database to enable contextual dialogue.
  - **Fully Containerized**: The entire environment, including the database and the Dify platform, is managed via Docker and Docker Compose for easy setup and reproducibility.

## Architecture

The system operates with two main `docker-compose` projects communicating over a shared Docker network.

```
+----------------+      +--------------------------------+      +---------------------+      +----------------------+
| End User       | <--> |  Dify Web/Agent (Localhost)    | <--> |  Shared Docker      | <--> |  FastAPI Backend     |
| (Browser)      |      |  (Handles prompt, calls tool)  |      |  Network            |      |  (dify-rag-dev:8000) |
+----------------+      +--------------------------------+      |  ("chatbot-network")|      +---------------------+
                                                                +---------------------+                |
                                                                                                       | <--> +----------------------+
                                                                                                       |      |  PostgreSQL Database |
                                                                                                       |      |  (Wikipedia Data)    |
                                                                                                       +------> +----------------------+
```

### Tech Stack

  - **Backend**: Python, FastAPI
  - **Database**: PostgreSQL with `pg_trgm` extension
  - **Platform**: Dify (Self-hosted)
  - **Infrastructure**: Docker, Docker Compose

## Setup and Installation

This project requires both this repository and a local Dify instance to be running and connected.

### Prerequisites

  - Git
  - Docker
  - Docker Compose

### Step 1: Clone Repositories

First, clone this project and the official Dify repository into separate directories.

```bash
# Clone this project
git clone https://github.com/automatedtomato/dify-rag-wiki.git
cd dify-rag-wiki

# Go back to the parent directory and clone Dify
cd ..
git clone https://github.com/langgenius/dify.git
```

### Step 2: Create a Shared Docker Network

Create a dedicated Docker network to allow the two projects to communicate with each other.

```bash
docker network create chatbot-network
```

### Step 3: Configure the Chatbot Project

1.  Navigate to the `dify-rag-wiki` directory.

2.  Create your environment file from the example.

    ```bash
    cp .env.example .env
    ```

    *Make sure to fill in the necessary values in your new `.env` file.*

### Step 4: Configure the Dify Project

1.  Navigate to the `dify/docker` directory.

2.  Create the environment file for Dify.

    ```bash
    cp .env.example .env
    ```

3.  Modify `dify/docker/docker-compose.yml` to connect its services to the shared network.

    a. Add the network definition to the end of the file:

    ```yaml
    # At the end of dify/docker/docker-compose.yml
    networks:
      # ... (keep existing network definitions like ssrf_proxy_network)
      chatbot-network:
        external: true
    ```

    b. Add `chatbot-network` to the `networks` list for the `db`, `api`, and `worker` services:

    ```yaml
    # Inside the services: block in dify/docker/docker-compose.yml
    services:
      db:
        # ...
        networks:
          - default # Or other existing networks
          - chatbot-network
      api:
        # ...
        networks:
          - default # Or other existing networks
          - chatbot-network
      worker:
        # ...
        networks:
          - default # Or other existing networks
          - chatbot-network
    ```

### Step 5: Launch All Services

Launch both projects from their respective directories.

a. If **GPU is unavailabel**:

```bash
# In the dify-rag-wiki directory
docker-compose up -d --build

# In the dify/docker directory
docker-compose up -d
```

a. If **GPU is available**:

```bash
# In the dify-rag-wiki directory
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build

# In the dify/docker directory
docker-compose up -d
```

Wait for all containers to start up and become healthy.

### Step 6: Run the Data Initialization Pipeline

Once all containers are running, execute the all-in-one pipeline script from the `dify-rag-wiki` directory. This will download the Wikipedia data, parse it, and create the necessary search indexes.

**Warning:** This process is extremely time-consuming and can take hours or even days to complete.

```bash
docker-compose exec dify-rag-dev python scripts/init_pipeline.py
```

## Usage

### 1\. Set up the Dify Tool

1.  Access your local Dify instance at `http://localhost/` and complete the initial setup.

2.  Create a new application, selecting the **Agent** type.

3.  Navigate to **Tools** -\> **Add Tool** -\> **Custom**.

4.  Get the OpenAPI schema for our API by visiting `http://localhost:8088/openapi.json` in your browser. Copy the entire JSON content.

5.  **Crucially, modify the copied JSON.** Add a `servers` block right after the `info` block, pointing to the API container's internal address.

    ```json
    {
      "openapi": "3.1.0",
      "info": { ... },
      "servers": [
        {
          "url": "http://dify-rag-dev:8000"
        }
      ],
      "paths": { ... }
    }
    ```

6.  Paste the **modified** schema into the OpenAPI schema input field in Dify and save the tool.

### 2\. Configure the Prompt

In your Dify Agent's **Orchestration / Prompt Engineering** view:

1.  Add the newly created Wikipedia search tool to the context.

2.  Provide a system prompt that instructs the agent on how and when to use the tool.

    **Example Prompt:**

    ```
    # Role
    You are an expert assistant who accurately answers questions using knowledge from the Japanese Wikipedia.

    # Tools
    You have access to a tool to search for articles in the Japanese Wikipedia by a given keyword.

    # Workflow
    1. First, extract the most important keyword from the user's question.
    2. You MUST use the Wikipedia search tool with that keyword in the `q` parameter.
    3. From the search results returned by the tool, carefully read the `content` of the most relevant article.
    4. Based ONLY on the information in the article's content, generate a comprehensive answer.
    5. At the end of your answer, you must cite the article `title` you used.

    # Constraints
    - Do not use your own knowledge. If the answer is not in the search results, state that you could not find relevant information.
    ```

### 3\. Chat\!

Use the **Debug and Preview** panel in Dify to start asking questions. Observe the orchestration log to see how the agent uses your custom API tool to find information and formulate responses.

## API Endpoints

  - `GET /api/articles/search?q={query}`: Performs a full-text search on article titles and content.
  - `POST /api/chat/`: Handles a chat interaction, manages session history, and communicates with Dify.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Future Work

  - **Implement Vector Search**: Integrate `pg_vector` and Sentence Transformer models to enable true semantic search, complementing the existing keyword search.
  - **Frontend Interface**: Build out the simple chat interface defined in the project roadmap.
  - **CI/CD Pipeline**: Automate testing and deployment.

## Author

Hikaru Tomizawa