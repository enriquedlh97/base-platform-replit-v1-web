#! /usr/bin/env bash

set -e
# Uncomment the next line for debugging
# set -x

# 1. Generate the openapi.json from the backend source
cd backend
# Activate virtual env to ensure dependencies are found
source .venv/bin/activate
python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > ../openapi.json
cd ..

# 2. Move the schema to the frontend directory
mv openapi.json frontend/

# 3. Run the client generation tool inside the frontend workspace
cd frontend
[ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"
nvm use && yarn run generate:api

echo "✅ API client generated successfully in frontend/packages/app/utils/api-client"
