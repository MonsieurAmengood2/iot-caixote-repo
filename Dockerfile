# Dockerfile

# 1. Base: imagem oficial Python 3.11 minimalista
FROM python:3.11-slim

# 2. Diretório de trabalho dentro do container
WORKDIR /app

# 3. Copia o requirements.txt e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia todo o código da aplicação para /app
COPY . .

# 5. Expõe a porta 8080 (Fly vai mapear para o exterior)
EXPOSE 8080

# 6. Comando para arrancar a app em produção:
#    gunicorn lê o "app" (módulo app.py) e expõe o objeto Flask chamado "app"
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
