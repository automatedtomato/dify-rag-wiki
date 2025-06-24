## Setup
### 0. Setup Environment
Rename .env.example to .env:

```bash
mv .env.example .env
```
then edit the file:
```text
// E.g.

POSTGRES_USER=example
POSTGRES_PASSWORD=example
...
```
### 1. Build container
```bash
# build & compose
docker-compose up -d --build

# enter into container
docker-compose exec python-dev bash

# Or if you use vscode:
# Choose "Dev Containers: Reopen in Container"

# exit
docker-compose down
```
### 2. Build DB
```bash
# Check if table is created when API starts
docker exec -it dify-rag-dev-db psql -U user -d chatbot_db

\dt
# OUTPUT
#           List of relations
#  Schema |  Name   | Type  | Owner
# --------+---------+-------+-------
#  public | articles| table | user
# (1 row)


\d articles # Check if dtypes match with the definition
# OUTPUT
#                                        Table "public.articles"
#    Column   |           Type           | Collation | Nullable |               Default                
# ------------+--------------------------+-----------+----------+--------------------------------------
#  id         | integer                  |           | not null | nextval('articles_id_seq'::regclass)
#  wiki_id    | bigint                   |           | not null | 
#  title      | character varying(255)   |           | not null | 
# ...
```
### 3. Data initializing pipeline
Run data processing pipeline by command below. This command execute:
- Download Wikipedia dump data
- Parse XML data and save to DB
- Create GIN indexes to title and content for faster searching
```bash
docker-compose exec python-dev python scripts/init_pipeline.py --dl --parse --id
```

...Or instead, you can run each process separately:
```bash
docker-compose exec python-dev python scripts/download_wiki.py

docker-compose exec python-dev python scripts/parse_wiki.py

docker-compose exec python-dev python scripts/create_indexes.py
```

This process will takes a long time. If you want to see if datas inserted correctly:
```bash
docker exec -it dify-rag-dev-db psql -U user -d chatbot_db
```
then
```sql
SELECT COUNT(*) FROM articles;
```
And you can see numbers of datas inserted to DB!


### 4. Setup Dify
In other directory outside of this project root, clone Dify official repo and open container.
```bash
git clone https://github.com/langgenius/dify.git
cd diy/docker
cp .env.example .env
docker-compose up -d
```
Add these lines at the end of `docker-compose.yml` in the project;
```yaml
networks:
  default:
    external:
      name: chatbot-network
```
then, add some difinitions to `docker/docker-compos.template.yml` in the Dify repo;
```yaml
services:
  # ... (no modification) ...
  api:
    networks:
      - chatbot-network # Add this
  # ...
  worker:
  # ...
    networks:
      - chatbot-networks # Add this
networks:
  # ...
  # Add these
  chatbot-network:
    external: true
```
then, connect API container and Dify container creatig network between them;
```bash
docker network create chatbot-network
```

Run `dify/docker/generate_docker_compose.py`, then deploy containers
```bash
# dify/docker
python dify/docker/generate_docker_compose.py

docker-compose up -d

# Project root
docker-compose up -d
```
Access to `http://localhost` and login!
### Setup Custom Tool for Dify
1. Access to `http://localhost:8088/openapi.json` in your browser, and copy all the JSON texts displayed.
2. Edit the JSON file: add `servers` block right after `info` block. Designate `dify-rag-dev' container to URL.
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
    // ...
```
3. Input this modified schemas to Dify Custom Tool's "OpenAPI shcema" section.
4. Add custom tool we just registered to the model.
5. Create system prompt and you can talk debug!