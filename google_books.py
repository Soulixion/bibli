import html
import re

import requests

from stockage import lire_cle

API_URL = "https://www.googleapis.com/books/v1/volumes"


def _nettoyer(texte):
    """Retire le HTML que Google Books met parfois dans les descriptions."""
    texte = texte or ""
    texte = re.sub(r"<br\s*/?>|</p>", "\n", texte)
    texte = re.sub(r"<[^>]+>", "", texte)
    return html.unescape(texte).strip()


def _couverture(info):
    liens = info.get("imageLinks", {})
    url = liens.get("thumbnail") or liens.get("smallThumbnail")
    if not url:
        return None
    url = url.replace("http://", "https://").replace("&edge=curl", "")
    return url.replace("zoom=1", "zoom=2")


def rechercher_livres(requete, max_resultats=10, francais=True):
    params = {
        "q": requete,
        "maxResults": max_resultats,
        "printType": "books",
    }
    if francais:
        params["langRestrict"] = "fr"

    cle = lire_cle()
    if cle:
        params["key"] = cle

    reponse = requests.get(API_URL, params=params, timeout=10)
    reponse.raise_for_status()

    resultats = []
    deja_vus = set()

    for item in reponse.json().get("items", []):
        info = item.get("volumeInfo", {})
        titre = info.get("title")
        if not titre:
            continue

        auteur = ", ".join(info.get("authors", [])) or "Auteur inconnu"

        # Évite les doublons (plusieurs éditions du même livre)
        cle_unique = (titre.lower(), auteur.lower())
        if cle_unique in deja_vus:
            continue
        deja_vus.add(cle_unique)

        resultats.append({
            "id": item.get("id"),
            "titre": titre,
            "auteur": auteur,
            "pages": info.get("pageCount") or None,
            "annee": (info.get("publishedDate") or "")[:4],
            "image": _couverture(info),
            "resume": _nettoyer(info.get("description")),
        })

    return resultats
