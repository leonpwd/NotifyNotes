FROM python:3-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Paris

WORKDIR /app

# Crée l'utilisateur avant de faire le chown
RUN adduser --disabled-password --gecos "" --shell /sbin/nologin appuser

# Création du dossier /config avec les bonnes permissions pour appuser
RUN mkdir -p /config && chown -R appuser /app /config

COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chmod 0755 /entrypoint.sh

RUN apk add --no-cache su-exec

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "src/main.py"]
LABEL org.opencontainers.image.source="https://github.com/leonpwd/NotifyNotes"