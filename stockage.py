import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIVRES_PATH = os.path.join(BASE_DIR, "livres.json")
PARAMETRES_PATH = os.path.join(BASE_DIR, "parametres.json")
CLE_PATH = os.path.join(BASE_DIR, "cle_google.txt")

TRIS = [
    "Titre (A → Z)",
    "Titre (Z → A)",
    "Auteur (A → Z)",
    "Ajoutés récemment",
]

PARAMETRES_PAR_DEFAUT = {
    "francais_seulement": True,
    "nb_resultats": 10,
}


# ---------- Outils JSON ----------

def _lire_json(chemin, defaut):
    if not os.path.exists(chemin):
        return defaut
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defaut


def _ecrire_json(chemin, data):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- Livres ----------

def charger_livres():
    livres = _lire_json(LIVRES_PATH, {})
    return livres if isinstance(livres, dict) else {}


def sauvegarder_livres(livres):
    _ecrire_json(LIVRES_PATH, livres)


def ajouter_livre(livre):
    """Ajoute un livre (résultat Google Books) à la bibliothèque."""
    livres = charger_livres()
    livres[livre["titre"]] = {
        "auteur": livre["auteur"],
        "pages": livre["pages"],
        "image": livre["image"],
        "resume": livre["resume"],
        "ajoute_le": datetime.now().isoformat(timespec="seconds"),
        "nouveau": True,
    }
    sauvegarder_livres(livres)


def supprimer_livres(titres):
    livres = charger_livres()
    for titre in titres:
        livres.pop(titre, None)
    sauvegarder_livres(livres)


def tout_supprimer():
    sauvegarder_livres({})


def reinitialiser_nouveaux():
    """Retire l'étiquette « récemment publié » de tous les livres."""
    livres = charger_livres()
    for livre in livres.values():
        if isinstance(livre, dict):
            livre["nouveau"] = False
    sauvegarder_livres(livres)


def importer_livres(contenu):
    """Fusionne un livres.json (octets) dans la bibliothèque. Retourne le nombre de nouveaux livres."""
    data = json.loads(contenu.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Format invalide")

    livres = charger_livres()
    nouveaux = 0
    for titre, infos in data.items():
        if isinstance(infos, dict):
            if titre not in livres:
                nouveaux += 1
            livres[titre] = infos

    sauvegarder_livres(livres)
    return nouveaux


def trier_titres(livres, tri):
    titres = list(livres)
    if tri == "Titre (Z → A)":
        return sorted(titres, key=str.lower, reverse=True)
    if tri == "Auteur (A → Z)":
        return sorted(titres, key=lambda t: (livres[t].get("auteur") or "").lower())
    if tri == "Ajoutés récemment":
        return sorted(titres, key=lambda t: livres[t].get("ajoute_le") or "", reverse=True)
    return sorted(titres, key=str.lower)


# ---------- Paramètres ----------

def charger_parametres():
    params = dict(PARAMETRES_PAR_DEFAUT)
    enregistres = _lire_json(PARAMETRES_PATH, {})
    if isinstance(enregistres, dict):
        params.update(enregistres)
    return params


def sauvegarder_parametres(params):
    _ecrire_json(PARAMETRES_PATH, params)


# ---------- Clé API Google Books ----------

def lire_cle():
    if os.path.exists(CLE_PATH):
        with open(CLE_PATH, "r", encoding="utf-8") as f:
            cle = f.read().strip()
        if cle:
            return cle
    return os.getenv("GOOGLE_BOOKS_API_KEY")


def enregistrer_cle(cle):
    with open(CLE_PATH, "w", encoding="utf-8") as f:
        f.write(cle.strip())


def supprimer_cle():
    if os.path.exists(CLE_PATH):
        os.remove(CLE_PATH)
