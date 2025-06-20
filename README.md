## Setup
### 1. Build container
```bash
# build & compose
docker-compose -f docker-compose.dev.yml up -d --build

# enter into container
docker-compose -f docker-compose.dev.yml exec python-dev bash

# Or if you use vscode:
# Choose "Dev Containers: Reopen in Container"

# exit
docker-compose -f docker-compose.dev.yml down
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
### 3. Download Wikipedia dump data / Parse XML data and save to DB
```bash
docker-compose exec python-dev python scripts/download_wiki.py

docker-compose exec python-dev python scripts/parse_wiki.py
```
This process will takes a long time. If you want to see if datas inserted correctly in process:
```bash
docker exec -it dify-rag-dev-db psql -U user -d chatbot_db
```
then
```sql
chatbot_db=# SELECT COUNT(*) FROM articles;
```
And you can see numbers of datas inserted to DB.