FROM python:3.12-slim

# PYTHONUNBUFFERED: os print() aparecem na hora nos logs do Azure
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependências primeiro: o Docker reaproveita esta camada enquanto o requirements.txt não mudar
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código da API (o .env NÃO entra na imagem: as chaves vão como variáveis/segredos no Azure)
COPY main.py .
COPY controller/ controller/
COPY core/ core/
COPY data/ data/
COPY domain/ domain/
COPY service/ service/

# Roda sem privilégios de administrador
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Porta que o Azure Container Apps deve usar como "target port"
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
