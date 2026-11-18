import streamlit as st


def setup_page():
    st.set_page_config(
        page_title="SmartStock | Inventory Intelligence",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; color: #172B4D; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #082F49 0%, #0B3D5C 58%, #0A344D 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
        padding: 1.15rem 0.85rem 1.4rem 0.85rem;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label { color: #E6F0F5 !important; }

    [data-testid="stSidebarNav"] { 
        display: none !important;
    }

    .smartstock-navigation-label {
        color: #8FB5C8;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        margin: 0 0.25rem 0.5rem 0.55rem;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] {
        border-radius: 10px;
        padding: 0.12rem 0.25rem;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
        background: rgba(255,255,255,0.09);
    }
    [data-testid="stSidebarNav"]::before {
        content: "NAVIGATION";
        display: block;
        color: #8FB5C8;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        padding: 0 0.65rem 0.45rem 0.65rem;
    }
    [data-testid="stSidebarNav"] ul { gap: 0.28rem; }
    [data-testid="stSidebarNav"] li { border-radius: 10px; }
    [data-testid="stSidebarNav"] a {
        border-radius: 10px !important;
        padding: 0.58rem 0.72rem !important;
        min-height: 42px;
        transition: background 0.15s ease, transform 0.15s ease;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,255,255,0.09) !important;
        transform: translateX(2px);
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: rgba(255,255,255,0.14) !important;
        box-shadow: inset 3px 0 0 #63C3E5;
    }
    [data-testid="stSidebarNav"] a span { font-weight: 650; }

    h1 { color: #0B3D5C !important; font-size: 2rem !important; font-weight: 800 !important; }
    h2 { color: #0B3D5C !important; font-size: 1.35rem !important; font-weight: 700 !important; }
    h3, h4 { color: #173F5F !important; font-weight: 650 !important; }
    [data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E6ECF2; border-radius: 14px; padding: 18px 20px; box-shadow: 0 3px 12px rgba(11, 61, 92, 0.045); min-height: 115px; }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #0B3D5C !important; font-size: 1.85rem !important; font-weight: 800 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF; border: 1px solid #E6ECF2; border-radius: 13px; box-shadow: 0 3px 12px rgba(11, 61, 92, 0.035); }
    .stButton > button { background: #0B3D5C; color: #FFFFFF; border: 1px solid #0B3D5C; border-radius: 9px; font-weight: 600; padding: 0.55rem 1rem; }
    .stButton > button:hover { background: #145477; color: #FFFFFF; }
    hr { border-color: #E2E8F0; margin-top: 1.5rem; margin-bottom: 1.5rem; }

    .smartstock-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0 0.25rem 1.25rem 0.25rem;
        padding-bottom: 1.15rem;
        border-bottom: 1px solid rgba(255,255,255,0.10);
    }
    .smartstock-brand-icon {
        width: 46px;
        height: 46px;
        display: grid;
        place-items: center;
        border-radius: 12px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.12);
        font-size: 1.55rem;
        box-shadow: 0 8px 18px rgba(0,0,0,0.12);
    }
    .smartstock-brand-name { color: white; font-size: 1.28rem; font-weight: 800; line-height: 1.1; }
    .smartstock-brand-tag { color: #A8CBDC; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.11em; margin-top: 5px; }
    .smartstock-status {
        margin: 1.25rem 0.25rem 0 0.25rem;
        padding: 0.72rem 0.78rem;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        background: rgba(255,255,255,0.06);
        color: #CFE4EF;
        font-size: 0.76rem;
    }
    .smartstock-status-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #65D6A6;
        margin-right: 7px;
        box-shadow: 0 0 8px rgba(101,214,166,0.7);
    }
    .smartstock-footer {
        text-align: center;
        color: #94A3B8;
        font-size: 0.78rem;
        padding: 24px 0 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div class="smartstock-brand">
            <div class="smartstock-brand-icon">📦</div>
            <div>
                <div class="smartstock-brand-name">SmartStock</div>
                <div class="smartstock-brand-tag">INVENTORY INTELLIGENCE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="smartstock-navigation-label">NAVIGATION</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="Accueil", icon="🏠")
        st.page_link("pages/1_Vue_densemble.py", label="Vue d’ensemble", icon="📊")
        st.page_link("pages/2_Gestion_des_alertes.py", label="Gestion des alertes", icon="🚨")
        st.page_link("pages/3_Analyse_produit.py", label="Analyse produit", icon="📈")
        st.page_link("pages/4_Administration.py", label="Administration", icon="🔧")

        st.markdown("""
        """, unsafe_allow_html=True)


def afficher_entete(titre: str, description: str):
    st.title(titre)
    st.markdown(f"<p style='color:#64748B; font-size:0.96rem; margin-top:-8px;'>{description}</p>", unsafe_allow_html=True)


def afficher_footer():
    st.markdown("<div class='smartstock-footer'>SmartStock — Inventory Intelligence<br>Système intelligent de suivi des stocks et de réapprovisionnement</div>", unsafe_allow_html=True)
