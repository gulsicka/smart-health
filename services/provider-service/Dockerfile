FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . . # Copy the entire application code (left .) to the container (right .)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]