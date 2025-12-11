# 📢 NotifyNotes

Script Python auto-hébergé qui surveille vos notes du groupe OMNES et envoie des notifications instantanées via [ntfy](https://ntfy.sh/).

## 🚀 Fonctionnalités

- Surveillance automatique des notes
- Notifications push sur téléphone/navigateur
- Configuration simple via variables d'environnement
- Déploiement Docker facile

## 🛠️ Prérequis

- Docker (ou Python 3.9+)
- URL de votre page de notes : Ouvrez Devtools (F12) → Onglet Network → Relevé de notes → Copiez l'URL de la requête `note_ajax.php`
- Application ntfy (Android/iOS)

## ⚡ Installation

### Docker Compose

```yaml
services:
  notifynotes:
    image: ghcr.io/leonpwd/notifynotes:latest
    container_name: notifynotes
    environment:
      - URL=https://campusonline.inseec.net/note/note_ajax.php?AccountName=VOTRE_ID
      - NTFY_URL=https://ntfy.sh/mon-topic # Optionnel
    volumes:
      - /config/notifynotes:/config
    restart: unless-stopped
    network_mode: host
```

```bash
docker compose up -d
```

### Docker CLI

```bash
docker run -d --name notifynotes \
  -e URL="https://campusonline.inseec.net/note/note_ajax.php?AccountName=VOTRE_ID" \
  -v /config/notifynotes:/config \
  --restart unless-stopped --network host \
  ghcr.io/pingoleon/notifynotes:latest
```

## 📲 Configuration ntfy

1. Installez l'app ntfy ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/us/app/ntfy/id1625396347))
2. Abonnez-vous au topic affiché dans les logs (ex: `notes-xxxxxxx`)
3. Recevez vos notifications ! 🎉

## ⚙️ Variables d'environnement

| Variable                    | Description                        | Défaut          | Requis |
| --------------------------- | ---------------------------------- | ---------------- | ------ |
| `URL`                     | URL de la page de notes            | -                | ✅     |
| `NTFY_URL`                | URL du serveur ntfy                | Auto-généré   | ❌     |
| `NTFY_AUTH`               | Authentification ntfy              | `false`        | ❌     |
| `NTFY_USER`               | User ntfy                          | -                | ❌     |
| `NTFY_PASS`               | Mot de passe ntfy                  | -                | ❌     |
| `NTFY_URL_LOCAL_FALLBACK` | URL de secours (réseau local)     | -                | ❌     |
| `CHECK_INTERVAL`          | Intervalle de vérification (s)    | `1800`         | ❌     |
| `TZ`                      | Fuseau horaire                     | `Europe/Paris` | ❌     |
| `LOG_LEVEL`               | Niveau de log (`INFO`/`DEBUG`) | `INFO`         | ❌     |

> Si `NTFY_URL` n'est pas défini, une URL aléatoire sera générée et sauvegardée dans `/config/ntfy_url.txt`.

## 📝 Exemple `.env` (hors Docker)

```env
URL=https://campusonline.inseec.net/note/note_ajax.php?AccountName=VOTRE_ID
NTFY_URL=https://ntfy.sh/mon-topic
LOG_LEVEL=DEBUG
```

## 🤝 Contribuer

Contributions bienvenues ! Ouvrez une issue ou une pull request.

## 📝 Licence

Unlicense – Partage libre
