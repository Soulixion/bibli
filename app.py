import streamlit as st

import stockage
import vues

st.set_page_config(
    page_title="Ma bibliothèque",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Liste « Récemment ajoutés » du panneau de gauche : simples lignes de texte cliquables
st.markdown("""
<style>
[data-testid="stSidebar"] .stButton > button {
    border: none;
    background: transparent;
    box-shadow: none;
    padding: 0 0 0 1rem;
    min-height: 0;
    justify-content: flex-start;
    text-align: left;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: transparent;
    text-decoration: underline;
}
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] .stButton > button p {
    text-align: left;
    justify-content: flex-start;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- État initial ----------
livres = stockage.charger_livres()

if st.session_state.get("livre_actuel") not in livres:
    st.session_state["livre_actuel"] = None

st.session_state.setdefault("nav", vues.NAV_MENU)

if st.session_state["livre_actuel"] is None and st.session_state["nav"] == vues.NAV_LIVRE:
    st.session_state["nav"] = vues.NAV_MENU


# ---------- Callbacks ----------
def _changer_page():
    if st.session_state["nav"] != vues.NAV_LIVRE:
        st.session_state["livre_actuel"] = None


def _ouvrir_depuis_recherche():
    titre = st.session_state.get("recherche_livre")
    if titre:
        vues.ouvrir_livre(titre)
        st.session_state["recherche_livre"] = None


# ---------- Barre latérale : navigation ----------
st.sidebar.title("Bibliothèque")

options = [vues.NAV_MENU, vues.NAV_AJOUTER, vues.NAV_PARAMETRES]
if st.session_state["livre_actuel"]:
    options.append(vues.NAV_LIVRE)

st.sidebar.radio(
    "Navigation",
    options,
    key="nav",
    on_change=_changer_page,
    label_visibility="collapsed",
)

st.sidebar.markdown("---")

st.sidebar.markdown(f"**📚 Tous les livres**")

# ---------- Barre latérale : recherche d'un livre ----------
st.sidebar.selectbox(
    "Rechercher un livre",
    options=sorted(livres, key=str.lower),
    index=None,
    placeholder="Rechercher un livre ...",
    key="recherche_livre",
    on_change=_ouvrir_depuis_recherche,
    label_visibility="collapsed",
)

# ---------- Barre latérale : récemment ajoutés ----------
nouveaux = [
    t for t in stockage.trier_titres(livres, "Ajoutés récemment")
    if livres[t].get("nouveau")
]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**🆕 Récemment ajoutés ({len(nouveaux)})**")
if nouveaux:
    for titre in nouveaux:
        st.sidebar.button(
            titre,
            key=f"nouveau_{titre}",
            on_click=vues.ouvrir_livre,
            args=(titre,),
        )
else:
    st.sidebar.caption("Aucun nouveau livre pour l'instant.")

# ---------- Messages ----------
if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"))

# ---------- Page affichée ----------
page = st.session_state["nav"]

if page == vues.NAV_LIVRE and st.session_state["livre_actuel"]:
    vues.vue_livre(st.session_state["livre_actuel"])
elif page == vues.NAV_AJOUTER:
    vues.vue_ajouter()
elif page == vues.NAV_PARAMETRES:
    vues.vue_parametres()
else:
    vues.vue_menu()
