import streamlit as st
import requests
import json
import os
from datetime import datetime

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="ERP Copilot · Textile",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded"
)

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/erp-assistant"

LOG_FILE = os.path.join(os.path.dirname(__file__), "../logs/ask_history.json")

# ── Session state ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ── Theme colors ──────────────────────────────────────────────
if st.session_state.dark_mode:
    BG          = "#0f1117"
    BG_SIDEBAR  = "#161b27"
    BG_CARD     = "#1a2235"
    BG_INPUT    = "#1a2235"
    BORDER      = "#1e2d40"
    TEXT_MAIN   = "#e2e8f0"
    TEXT_SUB    = "#64748b"
    TEXT_MUTED  = "#475569"
    TEXT_MSG    = "#cbd5e1"
    BADGE_BG    = "#0c2a1a"
    BADGE_COLOR = "#4ade80"
    BADGE_BORDER= "#166534"
    SQL_BG      = "#0d1117"
    SQL_COLOR   = "#a5b4fc"
    SQL_BORDER  = "#1e2d40"
    HEADER_BG   = "linear-gradient(135deg, #0d1f35 0%, #112240 100%)"
    HEADER_BORDER= "#1e3a5f"
    ONLINE_BG   = "#0a3d2e"
    ONLINE_COLOR= "#34d399"
    ONLINE_BORDER="#065f46"
    MSG_USER_BG = "linear-gradient(135deg,#1d4ed8,#1e40af)"
    BTN_SIDEBAR = "#1a2235"
    BTN_SIDEBAR_COLOR = "#94a3b8"
    BTN_SIDEBAR_BORDER= "#1e2d40"
    SCROLLBAR   = "#1e2d40"
    HIST_BG     = "#0f1a2e"
    HIST_BORDER = "#1e3a5f"
    HIST_SUCCESS= "#0c2a1a"
    HIST_FAIL   = "#2a0c0c"
else:
    BG          = "#f8fafc"
    BG_SIDEBAR  = "#ffffff"
    BG_CARD     = "#ffffff"
    BG_INPUT    = "#f1f5f9"
    BORDER      = "#e2e8f0"
    TEXT_MAIN   = "#0f172a"
    TEXT_SUB    = "#64748b"
    TEXT_MUTED  = "#94a3b8"
    TEXT_MSG    = "#1e293b"
    BADGE_BG    = "#dcfce7"
    BADGE_COLOR = "#15803d"
    BADGE_BORDER= "#86efac"
    SQL_BG      = "#f8fafc"
    SQL_COLOR   = "#4f46e5"
    SQL_BORDER  = "#e2e8f0"
    HEADER_BG   = "linear-gradient(135deg, #dbeafe 0%, #ede9fe 100%)"
    HEADER_BORDER= "#bfdbfe"
    ONLINE_BG   = "#dcfce7"
    ONLINE_COLOR= "#15803d"
    ONLINE_BORDER="#86efac"
    MSG_USER_BG = "linear-gradient(135deg,#2563eb,#1d4ed8)"
    BTN_SIDEBAR = "#f1f5f9"
    BTN_SIDEBAR_COLOR = "#475569"
    BTN_SIDEBAR_BORDER= "#e2e8f0"
    SCROLLBAR   = "#cbd5e1"
    HIST_BG     = "#f0f9ff"
    HIST_BORDER = "#bae6fd"
    HIST_SUCCESS= "#f0fdf4"
    HIST_FAIL   = "#fef2f2"

# ── CSS dynamique ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: {BG} !important;
    color: {TEXT_MAIN} !important;
    font-family: 'Inter', sans-serif !important;
}}
[data-testid="stSidebar"] {{
    background: {BG_SIDEBAR} !important;
    border-right: 1px solid {BORDER} !important;
}}
.erp-header {{
    display: flex; align-items: center; gap: 14px;
    padding: 20px 24px;
    background: {HEADER_BG};
    border: 1px solid {HEADER_BORDER};
    border-radius: 14px; margin-bottom: 24px;
}}
.erp-header-title {{ font-size: 20px; font-weight: 600; color: {TEXT_MAIN}; margin: 0; }}
.erp-header-sub   {{ font-size: 12px; color: {TEXT_SUB}; margin: 3px 0 0 0; }}
.erp-header-badge {{
    margin-left: auto;
    background: {ONLINE_BG}; color: {ONLINE_COLOR};
    font-size: 11px; font-weight: 500;
    padding: 4px 10px; border-radius: 20px;
    border: 1px solid {ONLINE_BORDER};
}}
.sidebar-section {{
    font-size: 11px; font-weight: 600; color: {TEXT_MUTED};
    letter-spacing: 1px; text-transform: uppercase;
    margin: 18px 0 8px 0;
}}
.status-item {{ display:flex; align-items:center; gap:8px; font-size:13px; color:{TEXT_SUB}; margin:5px 0; }}
.dot-active  {{ color: #34d399; }}
.dot-soon    {{ color: {TEXT_MUTED}; }}
.empty-state {{ text-align:center; padding:60px 20px; }}
.empty-icon  {{ font-size:48px; margin-bottom:12px; }}
.empty-title {{ font-size:18px; font-weight:500; color:{TEXT_SUB}; margin-bottom:6px; }}
.empty-sub   {{ font-size:13px; color:{TEXT_MUTED}; }}
.sql-block {{
    background: {SQL_BG}; border: 1px solid {SQL_BORDER};
    border-left: 3px solid #6366f1; border-radius: 8px;
    padding: 12px 14px; margin-top: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: {SQL_COLOR};
    white-space: pre-wrap; line-height: 1.6;
}}
.badge-view {{
    display:inline-block; font-size:11px; font-weight:500;
    padding:3px 9px; border-radius:20px;
    font-family:'JetBrains Mono',monospace;
    background:{BADGE_BG}; color:{BADGE_COLOR}; border:1px solid {BADGE_BORDER};
    margin-top:6px;
}}
/* History cards */
.hist-card {{
    background: {HIST_BG}; border: 1px solid {HIST_BORDER};
    border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;
}}
.hist-success {{ background: {HIST_SUCCESS}; border-color: {BADGE_BORDER}; }}
.hist-fail    {{ background: {HIST_FAIL}; border-color: #fca5a5; }}
.hist-ts      {{ font-size: 10px; color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; }}
.hist-q       {{ font-size: 13px; font-weight: 500; color: {TEXT_MAIN}; margin: 4px 0; }}
.hist-view    {{ font-size: 11px; color: {BADGE_COLOR}; }}
/* Inputs */
[data-testid="stTextInput"] input {{
    background: {BG_INPUT} !important; border: 1px solid {BORDER} !important;
    border-radius: 10px !important; color: {TEXT_MAIN} !important;
    font-size: 14px !important;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
}}
/* Buttons */
.stButton > button {{
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-size: 13px !important;
    font-weight: 500 !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: {BTN_SIDEBAR} !important; color: {BTN_SIDEBAR_COLOR} !important;
    border: 1px solid {BTN_SIDEBAR_BORDER} !important; border-radius: 8px !important;
    font-size: 12px !important; text-align: left !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: {BORDER} !important; color: {TEXT_MAIN} !important;
    border-color: #3b82f6 !important;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-thumb {{ background: {SCROLLBAR}; border-radius: 4px; }}
</style>
""", unsafe_allow_html=True)

# ── Log functions ─────────────────────────────────────────────
def load_history():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

# ── Send function ─────────────────────────────────────────────
def send_question(q: str):
    try:
        res = requests.post(N8N_WEBHOOK_URL, json={"question": q}, timeout=120)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.Timeout:
        return {"success": False, "response": "⏱️ Délai dépassé. Réessayez."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "response": "❌ Serveur inaccessible."}
    except Exception as e:
        return {"success": False, "response": f"❌ Erreur : {str(e)}"}

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:16px 0 8px 0;">
        <div style="font-size:20px;font-weight:600;color:{TEXT_MAIN};">🧵 ERP Copilot</div>
        <div style="font-size:12px;color:{TEXT_SUB};margin-top:3px;">Textile Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode toggle ──────────────────────────────────────────
    st.markdown(f'<div class="sidebar-section">⚙️ Apparence</div>', unsafe_allow_html=True)
    col_dark, col_light = st.columns(2)
    with col_dark:
        if st.button("🌙 Sombre", use_container_width=True, key="btn_dark"):
            st.session_state.dark_mode = True
            st.rerun()
    with col_light:
        if st.button("☀️ Clair", use_container_width=True, key="btn_light"):
            st.session_state.dark_mode = False
            st.rerun()

    st.markdown(f'<div class="sidebar-section">📺 Affichage</div>', unsafe_allow_html=True)
    show_sql  = st.toggle("Afficher le SQL",  value=False)
    show_view = st.toggle("Afficher la vue",  value=True)

    st.markdown(f'<div class="sidebar-section">💡 Suggestions</div>', unsafe_allow_html=True)
    exemples = [
        "Factures impayées ?",
        "CA total client AZUR ?",
        "Détail facture F-25/048",
        "Top 5 clients par CA",
        "Articles actifs famille Soutien Gorge ?",
        "Articles en taille 85B ?",
        "CA par famille d'articles 2025 ?",
    ]
    for ex in exemples:
        if st.button(ex, use_container_width=True, key=f"btn_{ex}"):
            st.session_state.pending_question = ex
            st.rerun()

    st.markdown(f'<div class="sidebar-section">📊 Périmètre</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="status-item"><span class="dot-active">●</span> Facturation</div>
    <div class="status-item"><span class="dot-active">●</span> Articles</div>
    <div class="status-item"><span class="dot-active">●</span> Achats</div>
    <div class="status-item"><span class="dot-active">●</span> RH / Production</div>
    <div class="status-item"><span class="dot-soon">●</span> Stock</div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Nouvelle conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = ""
        st.rerun()

# ── Header ────────────────────────────────────────────────────
st.markdown(f"""
<div class="erp-header">
    <div style="font-size:32px;">🧵</div>
    <div>
        <p class="erp-header-title">ERP Copilot · Textile</p>
        <p class="erp-header-sub">Posez vos questions en langage naturel — analyses métier en temps réel</p>
    </div>
    <div class="erp-header-badge">● En ligne</div>
</div>
""", unsafe_allow_html=True)

# ── Tabs : Chat / Historique ──────────────────────────────────
tab_chat, tab_history = st.tabs(["💬 Conversation", "📋 Historique"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ══════════════════════════════════════════════════════════════
with tab_chat:
    if not st.session_state.messages:
        st.markdown(f"""
        <div class="empty-state">
            <div class="empty-icon">💬</div>
            <div class="empty-title">Commencez une conversation</div>
            <div class="empty-sub">Posez une question sur la facturation, les articles, les achats ou la production</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                c1, c2 = st.columns([2, 5])
                with c2:
                    st.markdown(f"""
                    <div style="background:{MSG_USER_BG};
                        color:#fff; padding:11px 16px;
                        border-radius:18px 4px 18px 18px;
                        font-size:14px; line-height:1.6;
                        box-shadow:0 2px 12px rgba(29,78,216,0.3);
                        margin-bottom:4px;">
                        {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                c1, c2 = st.columns([5, 2])
                with c1:
                    a1, a2 = st.columns([0.3, 6])
                    with a1:
                        st.markdown("""
                        <div style="width:32px;height:32px;border-radius:50%;
                            background:linear-gradient(135deg,#0ea5e9,#6366f1);
                            display:flex;align-items:center;justify-content:center;
                            font-size:15px;margin-top:4px;">🤖</div>
                        """, unsafe_allow_html=True)
                    with a2:
                        if msg.get("nombre_reele") is not None and msg.get("nombre_reele") > 0:
                            st.markdown(f"""
                            <div style="background:{BG_CARD};border:1px solid {BORDER};
                                color:{TEXT_MSG};padding:13px 16px;
                                border-radius:4px 18px 18px 18px;
                                font-size:14px;line-height:1.7;
                                box-shadow:0 2px 8px rgba(0,0,0,0.1);
                                margin-bottom:4px;">
                                <strong>Nombre réel :</strong> {msg["nombre_reele"]}
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div style="background:{BG_CARD};border:1px solid {BORDER};
                            color:{TEXT_MSG};padding:13px 16px;
                            border-radius:4px 18px 18px 18px;
                            font-size:14px;line-height:1.7;
                            box-shadow:0 2px 8px rgba(0,0,0,0.1);
                            margin-bottom:4px;">
                            {msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if show_view and msg.get("view"):
                            st.markdown(f'<span class="badge-view">⬡ {msg["view"]}</span>',
                                        unsafe_allow_html=True)
                        if show_sql and msg.get("sql"):
                            st.markdown(f'<div class="sql-block">{msg["sql"]}</div>',
                                        unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns([6, 1])
    with col1:
        question = st.text_input(
            "question",
            value=st.session_state.pending_question,
            placeholder="Ex : Quelles sont les factures impayées ?",
            label_visibility="collapsed",
            key="chat_input"
        )
    with col2:
        send = st.button("Envoyer ↗", use_container_width=True)

    # Auto-envoyer suggestion
    if st.session_state.pending_question and st.session_state.pending_question == question:
        q = st.session_state.pending_question.strip()
        st.session_state.pending_question = ""
        st.session_state.messages.append({"role": "user", "content": q})
        with st.spinner("Analyse en cours..."):
            result = send_question(q)
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("response", "❌ Pas de réponse"),
            "view": result.get("view"),
            "sql":  result.get("sql")
        })
        st.rerun()
    
    if send and question.strip():
        q = question.strip()
        st.session_state.pending_question = ""
        st.session_state.messages.append({"role": "user", "content": q})
        with st.spinner("Analyse en cours..."):
            result = send_question(q)
            
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("response", "❌ Pas de réponse"),
            "view": result.get("view"),
            "sql":  result.get("sql"),
            "nombre_reele": result.get("nombre_reele")
        })
        st.rerun()

# ══════════════════════════════════════════════════════════════
# TAB 2 — HISTORIQUE
# ══════════════════════════════════════════════════════════════
with tab_history:
    history = load_history()

    if not history:
        st.markdown(f"""
        <div class="empty-state">
            <div class="empty-icon">📋</div>
            <div class="empty-title">Aucun historique disponible</div>
            <div class="empty-sub">Les questions posées apparaîtront ici automatiquement</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Stats globales
        total     = len(history)
        success   = sum(1 for h in history if h.get("success"))
        fail      = total - success

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total questions", total)
        with col2:
            st.metric("✅ Succès", success)
        with col3:
            st.metric("❌ Erreurs", fail)

        st.markdown("---")

        # Filtre
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            search = st.text_input("🔍 Rechercher dans l'historique",
                                   placeholder="Mot-clé...",
                                   label_visibility="collapsed")
        with col_f2:
            filter_status = st.selectbox("Statut", ["Tous", "Succès", "Erreurs"],
                                         label_visibility="collapsed")

        # Filtrer
        filtered = list(reversed(history))
        if search:
            filtered = [h for h in filtered
                       if search.lower() in (h.get("question") or "").lower()]
        if filter_status == "Succès":
            filtered = [h for h in filtered if h.get("success")]
        elif filter_status == "Erreurs":
            filtered = [h for h in filtered if not h.get("success")]

        st.markdown(f"**{len(filtered)} entrée(s) trouvée(s)**")
        st.markdown("")

        # Afficher l'historique
        for entry in filtered:
            success_class = "hist-success" if entry.get("success") else "hist-fail"
            icon          = "✅" if entry.get("success") else "❌"
            view_info     = f'<div class="hist-view">⬡ {entry.get("view")}</div>' \
                           if entry.get("view") else ""
            nb            = entry.get("nb_results", 0)
            nb_info       = f"· {nb} résultats" if nb else ""

            st.markdown(f"""
            <div class="hist-card {success_class}">
                <div class="hist-ts">{icon} {entry.get("timestamp", "")} {nb_info}</div>
                <div class="hist-q">❓ {entry.get("question", "")}</div>
                {view_info}
            </div>
            """, unsafe_allow_html=True)

            # Expandeur pour voir SQL et réponse
            with st.expander("Voir détails"):
                if entry.get("sql"):
                    st.markdown("**SQL généré :**")
                    st.code(entry.get("sql"), language="sql")
                st.markdown("**Réponse :**")
                st.markdown(entry.get("response", ""))

        # Bouton export
        st.markdown("---")
        if st.button("⬇️ Exporter l'historique JSON", use_container_width=True):
            st.download_button(
                label="📥 Télécharger ask_history.json",
                data=json.dumps(history, ensure_ascii=False, indent=2),
                file_name="ask_history.json",
                mime="application/json"
            )