# TinyGen

## Overview
A trivial version of CodeGen

## Getting Started

### Prerequisities
Install `poetry` on mac using:
```bash
brew install poetry
```

### 1. Install dependencies
Install the required libraries by running the following command in your terminal at the root of this repo:
```bash
poetry install
```

### 2. Environment
You'll need to define the following secrets in a .env.secrets file at the root of this repo:
- `OPENAI_API_KEY`
- `SUPABASE_KEY`

Reach out to emeka.igwegbu@gmail.com for secret keys.

### 3. Run the service
Run the service locally using
```bash
poetry run uvicorn app.main:app
```
