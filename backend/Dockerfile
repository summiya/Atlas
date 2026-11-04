FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY atlas ./atlas
RUN pip install --no-cache-dir . && useradd --system --create-home atlas
USER atlas
EXPOSE 8000
CMD ["uvicorn", "atlas.app:app", "--host", "0.0.0.0", "--port", "8000"]
