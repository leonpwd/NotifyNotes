from bs4 import BeautifulSoup
import re
import json
import unicodedata
import time
import sys

def fix_encoding_accents(s):
    return s.replace('�', 'é').replace('Ã©', 'é').replace('Ã¨', 'è').replace('ï¿½', 'Á')

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def split_notes(note_str):
    # Exemples : "13,50 (50%) -  (50%)" ou "16,00 (25%) - 17,50 (75%)"
    if not note_str or note_str.strip() == "":
        return []
    # Sépare sur " - "
    parts = [p.strip() for p in note_str.split(" - ")]
    notes = []
    for part in parts:
        # Cherche une note et une pondération
        m = re.match(r"(?:(?P<note>[\d,]+))?\s*\((?P<pond>[\d.,%]+)\)", part)
        if m:
            notes.append({
                "note": m.group("note") or "",
                "pondération": m.group("pond")
            })
        else:
            # Si pas de parenthèses, essaye de prendre juste la note
            if part:
                notes.append({
                    "note": part,
                    "pondération": ""
                })
    return notes

def convert_notes_to_json(url_response, json_file):
    html_content = url_response
    if not html_content:
        raise ValueError("Le contenu HTML est vide ou invalide.")

    try:
        soup = BeautifulSoup(html_content, "lxml")
        
        thead = soup.find("thead")
        if thead is None:
            print("Avertissement : balise <thead> non trouvée dans la réponse, le serveur est probablement en train de se reload, attente 1 minutes avant relance...")
            import os
            if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG":
                try:
                    with open("debug_last_notes.html", "w", encoding="utf-8") as f:
                        f.write(html_content[:10000])
                    os.chmod("debug_last_notes.html", 0o600)
                except Exception as e:
                    print(f"Impossible de sauvegarder le fichier de debug: {e}")
            time.sleep(60)
            print("Redémarrage du script...")
            sys.exit(1)
        
        # Vérifier que la structure est valide
        tr_elements = thead.find_all("tr")
        if len(tr_elements) < 2:
            raise ValueError("Structure HTML invalide: <thead> ne contient pas assez de <tr>")
        
        header_row = tr_elements[1]
        headers = [fix_encoding_accents(th.get_text(separator=" ", strip=True).split("\n")[0]) for th in header_row.find_all("th")]

        tbody = soup.find("tbody")
        if tbody is None:
            raise ValueError("Structure HTML invalide: <tbody> introuvable")
        
        rows = [
            [fix_encoding_accents(td.get_text(separator=" ", strip=True)) for td in row.find_all("td")]
            for row in tbody.find_all("tr")
            if "master-1" in row.get("class", [])
        ]

        data = [dict(zip(headers, cells)) for cells in rows if any(cells[1:])]

        section_map = {
            "Projet": "Projet",
            "Contrôle Continu": "Contrôle Continu",
            "ContrÃ´le Continu": "Contrôle Continu",
            "Examen": "Examen"
        }

        organized = []
        i = 0
        while i < len(data):
            ligne = data[i]
            if ligne.get("Coef."):
                matiere_nom = ligne[headers[0]]
                coef = ligne["Coef."]
                sections = {"Projet": [], "Contrôle Continu": [], "Examen": []}
                i += 1
                while i < len(data) and not data[i].get("Coef."):
                    sous_ligne = data[i].copy()
                    titre = sous_ligne[headers[0]].strip()
                    section = section_map.get(titre)
                    if section:
                        # Supprimer la clé inutile
                        sous_ligne.pop("Coef.", None)
                        sous_ligne.pop("Rattrapage Re-sit session", None)
                        sous_ligne.pop("Cours et évaluations Courses and evaluations", None)
                        # Renommer la pondération au niveau de la section
                        for key in ["Pondération Weight", "Pondï¿½ration Weight", "PondÁration Weight"]:
                            if key in sous_ligne:
                                sous_ligne["pondération - section"] = sous_ligne.pop(key)
                        if "Notes Grades" in sous_ligne:
                            sous_ligne["note"] = sous_ligne.pop("Notes Grades")
                        # Séparation des notes et pondérations multiples
                        note_val = sous_ligne.pop("note", "")
                        pond_val = sous_ligne.pop("pondération", "")
                        notes = []
                        if note_val and ("(" in note_val and ")" in note_val):
                            notes = split_notes(note_val)
                        elif note_val or pond_val:
                            notes = [{"note": note_val, "pondération": pond_val}]
                        else:
                            notes = []
                        sous_ligne["notes"] = notes
                        # Remettre la pondération de section si elle existe
                        if pond_val:
                            sous_ligne["pondération"] = pond_val
                        sections[section].append(sous_ligne)
                    i += 1
                if matiere_nom.strip() != "Crédits par indulgence / Leniency credits":
                    organized.append({
                        "matiere": matiere_nom,
                        "coef": coef,
                        "sections": sections
                    })
                else:
                    break
            else:
                i += 1

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(organized, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur lors du parsing HTML: {e}")
        raise