# TinyGen

## Overview
A trivial version of CodeGen

## Getting Started

### 1. Environment
You'll need to define the following secrets in a .env.secrets file at the root of this repo:
- `OPENAI_API_KEY`
- `SUPABASE_KEY`

Consider setting `ENV_FILE` to `.env.development` to configure the service for the dev environment. This value defaults to `.env` for production.

Reach out to emeka.igwegbu@gmail.com for secret keys.

### 2. Run the service
Run the service locally using
```bash
docker-compose up
```

The service runs on port 8000 by default. To run the service on a different port, update the port mapping in the docker-compose.yml file.