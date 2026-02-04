import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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
    # Session avec retry et backoff pour la robustesse réseau
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_redirect=False,
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    # Désactiver les redirections pour réduire les risques liés aux redirects
    response = session.get(URL, headers=headers, timeout=(5, 30), verify=True, allow_redirects=False)
    
    if response.status_code != 200:
        # N'imprime pas le corps pour éviter d'exposer des données
        raise Exception(f"Erreur lors de la récupération des notes: {response.status_code}")
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

def check_notes():
    """Fonction pour vérifier et traiter les notes"""
    try:
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
            return

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
    except Exception as e:
        print(f"Erreur lors de la vérification des notes: {e}")

def main():
    # Premier check automatique au lancement
    print("🚀 Premier check automatique au lancement du conteneur...")
    check_notes()
    print()
    
    # Un seul check dans la fenêtre 01:20-01:40 (par jour)
    window_date = None
    window_done = False
    
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
            now_tz = get_tz_time()
            current_date = now_tz.date()
            if window_date != current_date:
                window_date = current_date
                window_done = False

            # Entre 01:20 et 01:40 : on attend 01:40
            if now_tz.hour == 1 and 20 <= now_tz.minute < 40:
                next_140 = now_tz.replace(minute=40, second=0, microsecond=0)
                sleep_seconds = max(0, (next_140 - now_tz).total_seconds())
                print("Fenêtre 01:20-01:40 : attente jusqu'à 01:40 pour un unique check")
                time.sleep(sleep_seconds)
                continue

            # Entre 01:40 et 01:59 : un seul check, puis dodo jusqu'au lendemain
            if now_tz.hour == 1 and now_tz.minute >= 40:
                if window_done:
                    next_midnight = (now_tz + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    sleep_seconds = max(0, (next_midnight - now_tz).total_seconds())
                    print("Check déjà fait à 01:40, dodo jusqu'au lendemain")
                    time.sleep(sleep_seconds)
                    continue
                interval = CHECK_INTERVAL
        
        check_notes()
        if LOG_LEVEL != "DEBUG":
            now_tz = get_tz_time()
            if now_tz.hour == 1 and now_tz.minute >= 40:
                window_done = True
                next_midnight = (now_tz + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                sleep_seconds = max(0, (next_midnight - now_tz).total_seconds())
                print("Check effectué à 01:40, dodo jusqu'au lendemain")
                time.sleep(sleep_seconds)
                continue

        next_time = get_tz_time() + datetime.timedelta(seconds=interval)
        print("Prochain check à", next_time.strftime("%Y-%m-%d %H:%M:%S"))
        print()
        time.sleep(interval)

if __name__ == "__main__":
    main()