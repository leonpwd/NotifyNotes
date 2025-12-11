#!/bin/sh
# filepath: entrypoint.sh

set -e

# Récupérer l'UID/GID de appuser dynamiquement
APPUSER_UID=$(id -u appuser 2>/dev/null || echo 1000)
APPUSER_GID=$(id -g appuser 2>/dev/null || echo 1000)

# Changer le propriétaire du dossier monté avec les bonnes permissions
chown -R ${APPUSER_UID}:${APPUSER_GID} /config

# Exécuter l'application avec l'utilisateur non-root
exec su-exec ${APPUSER_UID}:${APPUSER_GID} "$@"