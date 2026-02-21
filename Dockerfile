# Usa imagem oficial Python slim
FROM python:3.11-slim

# Evita prompts no apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Diretório de trabalho no container
WORKDIR /app

# Instala dependências do sistema (necessário para psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (cache de layers)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copia o restante do projeto
COPY backend/ ./backend/

# Expõe a porta usada pelo Cloud Run
ENV PORT=8080
EXPOSE 8080

# Inicia a aplicação
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
