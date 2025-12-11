import requests
import time
import os
import compare_json as comparator
import parse
import datetime
from zoneinfo import ZoneInfo
import shutil
from env import (
    STORAGE_NOTES_JSON, TZ,URL, NTFY_AUTH, NTFY_URL, auth, LOG_LEVEL, STORAGE_NOTES_JSON_2, CHECK_INTERVAL, NTFY_URL_LOCAL_FALLBACK
)

def get_tz_time():
    try:
        return datetime.datetime.now(ZoneInfo(TZ))
    except Exception:
        # Fallback : heure locale (peut être fausse sur Windows)
        print("Avertissement : fuseau Europe/Paris non trouvé, fallback sur l'heure locale.")
        return datetime.datetime.now()

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    ZoneInfo = None

#? Fonction pour récupérer le contenu des notes
def get_notes_content():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    response = requests.get(URL, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Erreur lors de la récupération des notes: {response.status_code} - {response.text}")
    response.raise_for_status()
    return response.text

#! Envoi de notification via NTFY
def send_notification(change):
    if change == []:
        if LOG_LEVEL == "DEBUG":
            try:
                print("Mode debug, envoi d'une notification")
                response = requests.post(NTFY_URL, data=":(", headers={ "Title": "Aucun changement" }, auth=auth, timeout=10)
                if response.status_code == 200:
                    print("Notification envoyée avec succès via https")
                else:
                    print(f"Erreur lors de l'envoi de la notification via https")
                    print()
                    print("DEBUG : {e}")
                    if NTFY_URL_LOCAL_FALLBACK:
                        print("Envoi de la notification via l'URL de fallback local (HTTP)")
                        try :
                            requests.post(NTFY_URL_LOCAL_FALLBACK, data=":(", headers={ "Title": "Aucun changement" }, auth=auth, timeout=10)
                        except Exception as e:
                            print(f"Erreur lors de l'envoi de la notification")
                            print()
                            print("DEBUG : {e}")
                        if response.status_code == 200:
                            print("Notification envoyée avec succès via l'URL de fallback local (HTTP)")
                        else:
                            print(f"Erreur lors de l'envoi de la notification via l'URL de fallback local (HTTP)")
                            print()
                            print("DEBUG : {e}")
                        print()
            except Exception as e:
                print(f"Erreur lors de l'envoi de la notification")
                print()
                print("DEBUG : {e}")
            
        return

    matiere, section, note, ponderation = change
    title = parse.strip_accents(f"{matiere} - {section}")
    if ponderation:
        text = f"➡️ Note: {note} - Pondération: {ponderation}"
    else:
        text = f"➡️ Note: {note}"
    if not note:
        text = "🛠️ Modification de la pondération"
    print(f"Note : {title} - {text}")
    try:
        if NTFY_AUTH:
            response = requests.post(
                NTFY_URL,
                data=text,
                headers={ "Title": title, "Tags": "new" },
                auth=auth,
                timeout=10
            )
        else:
            response = requests.post(
                NTFY_URL,
                data=text,
                headers={ "Title": title, "Tags": "new" },
                timeout=10
            )
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification : {e}") 
    
    if response.status_code == 200:
            print(f"Notification envoyée avec succès (HTTPS)")
    else:
        print(f"Erreur lors de l'envoi de la notification  {response.status_code} - {response.text}")
        if NTFY_URL_LOCAL_FALLBACK:
            print("Envoi de la notification via l'URL de fallback local (HTTP)")
            try:
                if NTFY_AUTH:
                    response = requests.post(
                        NTFY_URL_LOCAL_FALLBACK,
                        data=text,
                        headers={ "Title": title, "Tags": "new" },
                        auth=auth,
                        timeout=10
                    )
                else:
                    response = requests.post(
                        NTFY_URL_LOCAL_FALLBACK,
                        data=text,
                        headers={ "Title": title, "Tags": "new" },
                        timeout=10
                    )
                if response.status_code == 200:
                    print("Notification envoyée avec succès via l'URL de fallback local (HTTP)")
                else:
                    print(f"Erreur lors de l'envoi de la notification via l'URL de fallback local (HTTP) {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Erreur lors de l'envoi de la notification via l'URL de fallback local (HTTP)")
                print()
                print("DEBUG : {e}")

def main():
    while True:
        now = datetime.datetime.now()
        # Mode DEBUG : exécution toutes les 30 secondes, sans contrainte d'heure
        if LOG_LEVEL == "DEBUG":
            interval = 30
        else:
            # Si on est hors de la plage minuit-7h, on attend jusqu'à minuit
            if not (0 <= now.hour < 3):
                next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                sleep_seconds = (next_midnight - now).total_seconds()
                print(f"Hors plage horaire, dodo jusqu'à minuit ({next_midnight.strftime('%Y-%m-%d %H:%M:%S')})")
                time.sleep(sleep_seconds)
                continue
            interval = CHECK_INTERVAL
            # Si on est entre 1h20 et 1h40, on attend 2 minutes
            now_tz = get_tz_time()
            if now_tz.hour == 1 and 20 <= now_tz.minute < 40:
                interval = 120
        
        # Récupérer le contenu des notes
        content = get_notes_content()
        current_time = get_tz_time().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Vérification des notes à {current_time}...")

        # Charger l'ancien JSON
        old_notes = comparator.load_notes_json(STORAGE_NOTES_JSON) if os.path.exists(STORAGE_NOTES_JSON) else []
        
        # Convertir le content dans STORAGE_NOTES_JSON_2
        parse.convert_notes_to_json(content, STORAGE_NOTES_JSON_2)
        if not os.path.exists(STORAGE_NOTES_JSON_2):
            print(f"Erreur : le fichier {STORAGE_NOTES_JSON_2} n'a pas été créé.")
            continue

        new_notes = comparator.load_notes_json(STORAGE_NOTES_JSON_2)
        
        if not old_notes: # Si aucun ancien JSON, on initialise
            print("Aucun ancien JSON trouvé, initialisation des notes")
            if os.path.exists(STORAGE_NOTES_JSON):
                os.remove(STORAGE_NOTES_JSON)
            shutil.move(STORAGE_NOTES_JSON_2, STORAGE_NOTES_JSON)
        else: # Si un ancien JSON existe, on compare les notes
            # Comparer
            changes = comparator.find_new_notes(old_notes, new_notes)
            if changes:
                print("#####❗Changement détecté dans les notes❗####")
                for change in changes:
                    send_notification(change)
            else:
                print("🫠  Aucun changement détecté.")
                if LOG_LEVEL == "DEBUG":
                    send_notification([])
            if os.path.exists(STORAGE_NOTES_JSON):
                os.remove(STORAGE_NOTES_JSON)
            shutil.move(STORAGE_NOTES_JSON_2, STORAGE_NOTES_JSON)

        next_time = get_tz_time() + datetime.timedelta(seconds=interval)
        print("Prochain check à", next_time.strftime("%Y-%m-%d %H:%M:%S"))
        print()
        time.sleep(interval)

if __name__ == "__main__":
    main()