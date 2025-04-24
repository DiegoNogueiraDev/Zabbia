FROM python:3.12-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY app/ app/
COPY mcp_server/ mcp_server/

# Expor porta
EXPOSE 8000

# Executar aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 