#!/bin/sh
# filepath: entrypoint.sh

set -eu
set -o pipefail

# Réduire les permissions par défaut des fichiers créés
umask 077

# Créer le répertoire /config s'il n'existe pas
mkdir -p /config

# Restreindre les permissions du répertoire /config et assigner le propriétaire
chmod 700 /config 2>/dev/null || true
chown -R appuser:appuser /config 2>/dev/null || true

# S'assurer que les fichiers JSON existent avec les bonnes permissions
for file in /config/new_notes.json /config/old_notes.json; do
    if [ ! -f "$file" ]; then
        # Crée un fichier JSON vide avec permissions restrictives
        echo "[]" > "$file" 2>/dev/null || true
        chmod 600 "$file" 2>/dev/null || true
        chown appuser:appuser "$file" 2>/dev/null || true
    else
        chmod 600 "$file" 2>/dev/null || true
        chown appuser:appuser "$file" 2>/dev/null || true
    fi
done

# Si su-exec est disponible, exécuter la commande sous appuser; sinon, tenter avec su -s
if command -v su-exec >/dev/null 2>&1; then
    exec "$@"
else
    echo "Avertissement: su-exec introuvable, tentative de bascule via su" >&2
    # shellcheck disable=SC2039
    exec sh -c "su -s /bin/sh appuser -c '$*'"
fi