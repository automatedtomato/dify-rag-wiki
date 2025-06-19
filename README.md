## Setup
```bash
# build & compose
docker-compose -f docker-compose.dev.yml up -d --build

# enter into container
docker-compose -f docker-compose.dev.yml exec python-dev bash

# Or if you use vscode:
# Press 'cmd + shift + P' and select "Dev Containers: Reopen in Container"

# exit
docker-compose -f docker-compose.dev.yml down
```
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