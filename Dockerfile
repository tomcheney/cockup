FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[web]"

EXPOSE 8000
ENTRYPOINT ["cockup"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
