import json

import requests
import streamlit as st

import stockage
from google_books import rechercher_livres

NAV_MENU = "📚 Menu"
NAV_AJOUTER = "➕ Ajouter un livre"
NAV_PARAMETRES = "⚙️ Paramètres"
NAV_LIVRE = "📖 Fiche du livre"


# ---------- Outils de navigation ----------

def flash(message):
    """Message affiché (toast) au prochain affichage de la page."""
    st.session_state["flash"] = message


def ouvrir_livre(titre):
    st.session_state["livre_actuel"] = titre
    st.session_state["nav"] = NAV_LIVRE


def aller_ajouter():
    st.session_state["livre_actuel"] = None
    st.session_state["nav"] = NAV_AJOUTER


def retour_menu():
    st.session_state["livre_actuel"] = None
    st.session_state["nav"] = NAV_MENU


# ---------- Menu ----------

def vue_menu():
    livres = stockage.charger_livres()

    st.title("Bienvenue")
    st.write(
        "Bienvenue dans ta bibliothèque en ligne. Chaque livre a sa fiche avec "
        "sa couverture, son auteur, son nombre de pages et son résumé."
    )
    st.write(
        "Utilise le panneau de gauche pour rechercher un livre ou ouvrir les derniers "
        "ajouts, et la page « ➕ Ajouter un livre » pour en ajouter de nouveaux grâce "
        "à Google Books."
    )

    total_pages = sum(
        l["pages"] for l in livres.values() if isinstance(l.get("pages"), int)
    )
    st.write("**Nombre de livres disponibles :**", len(livres))
    if total_pages:
        st.write("**Nombre de pages au total :**", total_pages)

    if not livres:
        st.button("➕ Ajouter un livre", on_click=aller_ajouter)


# ---------- Ajouter un livre ----------

@st.cache_data(ttl=600, show_spinner=False)
def _chercher(requete, nb_resultats, francais):
    return rechercher_livres(requete, max_resultats=nb_resultats, francais=francais)


def _ajouter(livre):
    stockage.ajouter_livre(livre)
    flash(f"« {livre['titre']} » ajouté à la bibliothèque.")


def vue_ajouter():
    params = stockage.charger_parametres()

    st.title("➕ Ajouter un livre")

    with st.form("recherche"):
        requete = st.text_input("Titre du livre", placeholder="Ex : 1984")
        francais = st.checkbox(
            "Résultats en français uniquement", value=params["francais_seulement"]
        )
        envoyer = st.form_submit_button("Rechercher")

    if envoyer and requete.strip():
        try:
            with st.spinner("Recherche en cours ..."):
                st.session_state["resultats"] = _chercher(
                    requete.strip(), params["nb_resultats"], francais
                )
        except requests.HTTPError as e:
            st.session_state["resultats"] = None
            if e.response is not None and e.response.status_code == 429:
                st.error(
                    "Google a bloqué la recherche (quota dépassé). "
                    "Ajoute ta clé API dans ⚙️ Paramètres."
                )
            else:
                st.error(f"Erreur Google Books : {e}")
        except requests.RequestException as e:
            st.session_state["resultats"] = None
            st.error(f"Impossible de joindre Google Books : {e}")

    resultats = st.session_state.get("resultats")
    if resultats is None:
        return
    if not resultats:
        st.info("Aucun livre trouvé.")
        return

    livres = stockage.charger_livres()

    for i, livre in enumerate(resultats):
        _marge, col_img, col_txt, col_btn = st.columns([0.3, 1, 4, 2])

        with col_img:
            if livre["image"]:
                st.image(livre["image"], width=80)

        with col_txt:
            st.markdown(f"**{livre['titre']}**")

            details = [livre["auteur"]]
            if livre["pages"]:
                details.append(f"{livre['pages']} pages")
            if livre["annee"]:
                details.append(livre["annee"])
            st.caption(" · ".join(details))

            if livre["resume"]:
                with st.expander("Résumé"):
                    st.write(livre["resume"])

        with col_btn:
            if livre["titre"] in livres:
                st.success("Ajouté")
            else:
                st.button(
                    "Ajouter",
                    key=f"ajouter_{i}_{livre['id']}",
                    on_click=_ajouter,
                    args=(livre,),
                )

        st.divider()


# ---------- Fiche d'un livre ----------

def vue_livre(titre):
    livre = stockage.charger_livres()[titre]

    st.button("← Retour au menu", on_click=retour_menu)

    st.title(titre)

    if livre.get("image"):
        st.image(livre["image"], width=250)

    st.write("**Auteur :**", livre.get("auteur") or "Inconnu")
    st.write("**Nombre de pages :**", livre.get("pages") or "Non renseigné")

    st.subheader("Résumé")
    st.write(livre.get("resume") or "Aucun résumé disponible.")


# ---------- Paramètres ----------

def _reinitialiser_nouveaux():
    stockage.reinitialiser_nouveaux()
    flash("La catégorie « Récemment ajoutés » a été vidée.")


def _enregistrer_cle():
    cle = st.session_state.get("champ_cle", "").strip()
    if cle:
        stockage.enregistrer_cle(cle)
        st.session_state["champ_cle"] = ""
        flash("Clé API enregistrée.")
    else:
        flash("Aucune clé saisie.")


def _supprimer_cle():
    stockage.supprimer_cle()
    flash("Clé API supprimée.")


def _importer():
    fichier = st.session_state.get("fichier_import")
    if fichier is None:
        flash("Choisis d'abord un fichier .json.")
        return
    try:
        nouveaux = stockage.importer_livres(fichier.getvalue())
        flash(f"{nouveaux} nouveau(x) livre(s) importé(s).")
    except ValueError:
        flash("Fichier invalide : ce n'est pas un livres.json.")


def _supprimer_selection():
    titres = st.session_state.get("a_supprimer", [])
    if not titres:
        flash("Aucun livre sélectionné.")
        return
    stockage.supprimer_livres(titres)
    st.session_state["a_supprimer"] = []
    flash(f"{len(titres)} livre(s) supprimé(s).")


def vue_parametres():
    livres = stockage.charger_livres()

    st.title("⚙️ Paramètres")

    st.divider()

    # Récemment ajoutés
    st.subheader("Catégorie « Récemment ajoutés »")
    nb_nouveaux = sum(1 for l in livres.values() if l.get("nouveau"))
    st.caption(f"{nb_nouveaux} livre(s) dans cette catégorie (affichée dans le panneau de gauche).")
    st.button(
        "Vider « Récemment ajoutés »",
        on_click=_reinitialiser_nouveaux,
        disabled=nb_nouveaux == 0,
    )

    st.divider()

    # Clé API
    st.subheader("Clé API Google Books")
    if stockage.lire_cle():
        st.caption("✅ Une clé est enregistrée.")
    else:
        st.caption("Aucune clé : les recherches peuvent être bloquées (erreur 429).")

    with st.form("form_cle"):
        st.text_input("Clé API", type="password", key="champ_cle")
        st.form_submit_button("Enregistrer la clé", on_click=_enregistrer_cle)

    if stockage.lire_cle():
        st.button("Supprimer la clé", on_click=_supprimer_cle)

    with st.expander("Comment obtenir une clé gratuite ?"):
        st.markdown(
            "1. Va sur https://console.cloud.google.com et crée un projet.\n"
            "2. « API et services » → « Bibliothèque » → **Books API** → Activer.\n"
            "3. « API et services » → « Identifiants » → « Créer des identifiants » → **Clé API**.\n"
            "4. Colle la clé ci-dessus."
        )

    st.divider()

    # Données
    st.subheader("Sauvegarde")
    st.download_button(
        "⬇️ Exporter ma bibliothèque (livres.json)",
        data=json.dumps(livres, ensure_ascii=False, indent=2),
        file_name="livres.json",
        mime="application/json",
    )
    st.file_uploader("Importer un livres.json", type="json", key="fichier_import")
    st.button("Importer", on_click=_importer)

    st.divider()

    # Suppression
    st.subheader("Supprimer des livres")
    if livres:
        st.multiselect(
            "Livres à supprimer", sorted(livres, key=str.lower), key="a_supprimer"
        )
        st.button("Supprimer la sélection", on_click=_supprimer_selection)
    else:
        st.caption("Aucun livre dans la bibliothèque.")
