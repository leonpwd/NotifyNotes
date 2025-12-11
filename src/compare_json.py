import json
from parse import convert_notes_to_json
import os

def load_notes_json(filepath):
    if not os.path.exists(filepath):
        print(f"Le fichier {filepath} n'existe pas. Retourne une liste vide.")
        return []   
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Le fichier JSON doit contenir une liste")
            return data
    except json.JSONDecodeError as e:
        print(f"Erreur lors de la lecture du JSON {filepath}: {e}")
        return []
    except Exception as e:
        print(f"Erreur inattendue lors de la lecture de {filepath}: {e}")
        return []

def save_notes_json(data, filepath):
    data.replace('�', 'é').replace('Ã©', 'é').replace('Ã¨', 'è').replace('ï¿½', 'Á')
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Restreindre les permissions du fichier JSON (lecture/écriture propriétaire uniquement)
    os.chmod(filepath, 0o600)

def find_new_notes(old_notes, new_notes):
    changes = []
    old_map = {(m['matiere'], m['coef']): m for m in old_notes}
    for new_matiere in new_notes:
        key = (new_matiere['matiere'], new_matiere['coef'])
        old_matiere = old_map.get(key)
        if not old_matiere:
            continue
        for section in ["Projet", "Contrôle Continu", "Examen"]:
            old_section = old_matiere['sections'].get(section, [])
            new_section = new_matiere['sections'].get(section, [])
            for idx, new_block in enumerate(new_section):
                old_block = old_section[idx] if idx < len(old_section) else None
                new_notes_list = new_block.get("notes", [])
                old_notes_list = old_block.get("notes", []) if old_block else []
                for n_idx, new_note in enumerate(new_notes_list):
                    old_note = old_notes_list[n_idx] if n_idx < len(old_notes_list) else None
                    if old_note != new_note:
                        matiere_tronquee = new_matiere['matiere'].split('/')[0].strip()
                        note = new_note.get("note", "")
                        ponderation = new_note.get("pondération", "")
                        changes.append([matiere_tronquee, section, note, ponderation])
    return changes