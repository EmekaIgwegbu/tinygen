FROM python:3.12
RUN pip install poetry
WORKDIR /tinygen
ENV PYTHONPATH="/tinygen/src"
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi
COPY . .
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
