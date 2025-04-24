FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de requisitos
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte
COPY main.py .
COPY backend/ /app/backend/
COPY config/ /app/config/

# Criar diretório de configuração se não existir
RUN mkdir -p /app/config

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["python", "main.py"] 