FROM python:3.12.10-slim

RUN pip install poetry
RUN pip install uvicorn

WORKDIR /app

COPY poery.lock .
COPY pyproject.toml .
COPY src .
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
