FROM python:3-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Paris

WORKDIR /app

# Crée l'utilisateur avant de faire le chown
RUN adduser --disabled-password --gecos "" --shell /sbin/nologin appuser

# Création du dossier /config avec les bonnes permissions pour appuser
RUN mkdir -p /config && chown -R appuser:appuser /app /config

# Installer su-exec et les certificats CA
RUN apk add --no-cache su-exec ca-certificates && update-ca-certificates

COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
# Corriger une vulnérabilité connue d'urllib3 via mise à niveau contrôlée
RUN pip install --no-cache-dir --upgrade 'urllib3>=2.6.3,<3'

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown appuser:appuser /entrypoint.sh

# Passer en root temporairement pour l'entrypoint (qui doit gérer les permissions du volume)
# L'entrypoint s'assurera que appuser peut écrire dans /config
USER root

ENTRYPOINT ["/entrypoint.sh"]
CMD ["su-exec", "appuser", "python", "src/main.py"]
HEALTHCHECK --interval=5m --timeout=20s --start-period=30s CMD pgrep -f "python src/main.py" >/dev/null || exit 1
LABEL org.opencontainers.image.source="https://github.com/leonpwd/NotifyNotes"