import os
import random
import re

ERROR_HASH = "9c287ec0f172e07215c5af2f96445968c266bcc24519ee0cf70f43f178fa613e"

def validate_ntfy_url(url):
    """Valider le format d'une URL ntfy"""
    pattern = r'^https?://[a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,}/[a-zA-Z0-9_\-]+$'
    return re.match(pattern, url) is not None

#* Activer ou non le dotenv si le fichier .env est présent
if os.path.exists(".env"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Le module python-dotenv n'est pas installé, mais .env détecté.")

#* Variables d'environnement
STORAGE_NOTES_JSON = os.getenv("STORAGE_NOTES_JSON", "/config/old_notes.json")
STORAGE_NOTES_JSON_2 = os.getenv("STORAGE_NOTES_JSON_2", "/config/new_notes.json")
STORAGE_FILE_URL = os.getenv("STORAGE_FILE_URL", "/config/ntfy_url.txt")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "1800"))

#* Ajout de la gestion du timezone
TZ = os.getenv("TZ", "Europe/Paris")
# Validation simple du fuseau horaire
try:
    from zoneinfo import ZoneInfo
    ZoneInfo(TZ)  # Vérifie que le TZ est valide
except Exception:
    print(f"Erreur: Fuseau horaire '{TZ}' invalide. Utilisation de Europe/Paris par défaut.")
    TZ = "Europe/Paris"

#* Validation de CHECK_INTERVAL
try:
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "1800"))
    if CHECK_INTERVAL < 30 or CHECK_INTERVAL > 86400:
        print(f"Avertissement: CHECK_INTERVAL doit être entre 30s et 24h. Utilisation de 1800s.")
        CHECK_INTERVAL = 1800
except ValueError:
    print("Erreur: CHECK_INTERVAL doit être un nombre. Utilisation de 1800s.")
    CHECK_INTERVAL = 1800

#! Chargement des variables d'environnement importantes
#? URL des notes à surveiller
URL = os.getenv("URL") 
if not URL:
    print("Erreur: La variable URL doit être définie dans le fichier .env ou en ENV docker. (ex:https://campusonline.inseec.net/note/note_ajax.php?AccountName=)")
    exit(1)
elif not URL.startswith("https://campusonline.inseec.net/note/note_ajax.php?AccountName="):
    print("Erreur: L'URL doit commencer par 'https://campusonline.inseec.net/note/note_ajax.php?AccountName='")
    exit(1)

#? Vérification de l'authentification
NTFY_AUTH = os.getenv("NTFY_AUTH", "False").lower() == "true" 
NTFY_USER = None
NTFY_PASS = None
auth = None
if NTFY_AUTH:
    NTFY_USER = os.getenv("NTFY_USER")
    NTFY_PASS = os.getenv("NTFY_PASS")
    auth = (NTFY_USER, NTFY_PASS)
    if not NTFY_USER or not NTFY_PASS:
        print("Erreur: Les variables d'environnement NTFY_USER et NTFY_PASS doivent être définies si NTFY_AUTH est activé.")
        exit(1)

#? Endpoint de notification NTFY
NTFY_URL = os.getenv("NTFY_URL") 
if NTFY_URL:
    if not validate_ntfy_url(NTFY_URL):
        print("Erreur: L'URL NTFY est invalide. Format attendu: https://domain.com/topic")
        exit(1)
    print("URL ntfy custom utilisée :", NTFY_URL,"\n")
    NTFY_URL_LOCAL_FALLBACK = os.getenv("NTFY_URL_LOCAL_FALLBACK", None)
    if NTFY_URL_LOCAL_FALLBACK and not validate_ntfy_url(NTFY_URL_LOCAL_FALLBACK):
        print("Erreur: L'URL NTFY_LOCAL_FALLBACK est invalide.")
        exit(1)
else:
    # Si pas de variable d'env, on regarde dans le fichier STORAGE_FILE_URL
    if os.path.exists(STORAGE_FILE_URL):
        with open(STORAGE_FILE_URL, "r") as f:
            NTFY_URL = f.read().strip()
        if not validate_ntfy_url(NTFY_URL):
            print("Erreur: L'URL NTFY stockée est invalide. Supprimez le fichier et relancez.")
            exit(1)
        print("URL ntfy récupérée depuis le fichier :", NTFY_URL,"\n")
        NTFY_AUTH = False
        auth = None
    else:
        # Sinon, on en génère une nouvelle et on la sauvegarde
        random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))
        NTFY_URL = f"https://ntfy.sh/notes-{random_suffix}"
        with open(STORAGE_FILE_URL, "w") as f:
            f.write(NTFY_URL)
        os.chmod(STORAGE_FILE_URL, 0o600)  # Restreindre les permissions
        print("URL ntfy par défaut générée :", NTFY_URL,"\n")
        NTFY_AUTH = False
        auth = None

#? Niveau de log
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL == "DEBUG":
    CHECK_INTERVAL = 30