# tinygen

## Overview
A trivial version of CodeGen

## Getting Started

### Prerequisities
- Python 3.11
If you are using pyenv, the .python-version file at the root of this project will automatically select this version if it is installed in your pyenv directory.

### 1. Create a virtual environment
To create a virtual python environment run the following command in your terminal at the root of this repo:
```bash
python -m venv env
```

Then activate virtual environment using:
```bash
source env/bin/activate
```

### 2. Install dependencies
Install the required libraries by running the following command in your terminal at the root of this repo:
```bash
pip install -r requirements.txt
```

### 3. Environment
You'll need to define the following secrets in a .env.secrets file at the root of this repo:
- OPENAI_API_KEY
- SUPABASE_KEY

Reach out to emeka.igwegbu@gmail.com for these secrets.

### 4. Run the service
Run the service locally using
```bash
uvicorn tinygen.app:app
```
#TODO