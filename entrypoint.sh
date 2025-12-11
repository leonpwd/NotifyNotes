#!/bin/sh
# filepath: entrypoint.sh

# On tourne déjà en tant qu'appuser grâce à USER appuser dans le Dockerfile.
# Pas besoin de su-exec : il échoue sur setgroups en environnement non privilégié.
exec "$@"