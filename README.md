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