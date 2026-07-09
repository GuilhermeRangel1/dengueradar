import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import unicodedata
import os
import requests
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

st.set_page_config(page_title="DengueRadar | Recife", layout="wide", page_icon="🦟")

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    *, *::before, *::after { box-sizing: border-box; }

    html, body,
    [class*="css"],
    .stApp,
    .stApp > div,
    section[data-testid="stSidebar"],
    div[data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #090d12 !important;
        color: #e6edf3 !important;
    }

    #MainMenu,
    footer,
    header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .reportview-container .main .block-container > div:first-child > div:first-child > div > img,
    button[title="View fullscreen"],
    .stDeployButton { 
        display: none !important; 
        visibility: hidden !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: clamp(1rem, 4vw, 4.5rem) !important;
        padding-right: clamp(1rem, 4vw, 4.5rem) !important;
        max-width: 1480px !important;
    }

    div[data-testid="stAppViewContainer"] > section.main {
        padding-top: 0 !important;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="element-container"],
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"],
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        padding-left: clamp(0rem, 1vw, 1rem);
        padding-right: clamp(0rem, 1vw, 1rem);
    }

    h1 {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #f0f6fc !important;
        letter-spacing: 0 !important;
        line-height: 1.25 !important;
        margin: 0 0 0.25rem !important;
    }
    h2 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #f0f6fc !important;
        letter-spacing: 0 !important;
        margin: 1.75rem 0 0.75rem !important;
    }
    h3 {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #c9d1d9 !important;
        margin: 1.25rem 0 0.5rem !important;
    }
    p, .stMarkdown p {
        color: #8b949e !important;
        line-height: 1.65 !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stCaptionContainer"] p,
    small, .stCaption {
        font-size: 0.78rem !important;
        color: #6e7681 !important;
        font-weight: 400 !important;
    }

    hr {
        border: none !important;
        border-top: 1px solid rgba(139, 148, 158, 0.16) !important;
        margin: 1.35rem 0 !important;
    }

    div[data-testid="metric-container"] {
        background:
            linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015)),
            #111821 !important;
        border: 1px solid rgba(139, 148, 158, 0.18) !important;
        border-radius: 8px !important;
        padding: 1.15rem 1.25rem !important;
        position: relative !important;
        overflow: hidden !important;
        min-height: 126px !important;
        box-shadow: 0 14px 36px rgba(0,0,0,0.18) !important;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        border-color: rgba(63,185,80,0.38) !important;
        box-shadow: 0 18px 44px rgba(0,0,0,0.28) !important;
    }
    div[data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        width: 3px;
        height: 100%;
        right: auto;
        background: linear-gradient(180deg, #3fb950, #388bfd);
        opacity: 0.85;
        transition: opacity 0.2s;
    }
    div[data-testid="metric-container"]:hover::before { opacity: 1; }

    div[data-testid="metric-container"] label,
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] p {
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        color: #6e7681 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        margin-bottom: 0.35rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.55rem !important;
        font-weight: 500 !important;
        color: #f0f6fc !important;
        line-height: 1.2 !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.78rem !important;
        color: #6e7681 !important;
        margin-top: 0.2rem !important;
    }

    .stTabs {
        margin-top: 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(13, 17, 23, 0.72) !important;
        border: 1px solid rgba(139, 148, 158, 0.14) !important;
        border-radius: 8px !important;
        gap: 0.25rem !important;
        padding: 0.35rem !important;
        backdrop-filter: blur(14px);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        border-radius: 6px !important;
        color: #6e7681 !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.65rem 1rem !important;
        margin-right: 0 !important;
        transition: color 0.15s ease, background 0.15s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #c9d1d9 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #f0f6fc !important;
        background: #161f2b !important;
        box-shadow: inset 0 0 0 1px rgba(139, 148, 158, 0.12) !important;
    }
    div[data-testid="stTabContent"] {
        padding: 1.65rem 0 0 !important;
    }

    div[data-baseweb="select"] > div {
        background: #111821 !important;
        border: 1px solid rgba(139, 148, 158, 0.2) !important;
        border-radius: 6px !important;
        color: #e6edf3 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #8b949e !important;
    }
    div[data-baseweb="select"] > div:focus-within {
        border-color: #3fb950 !important;
        box-shadow: 0 0 0 1px #3fb950 !important;
    }
    div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
        color: #e6edf3 !important;
        font-weight: 500 !important;
    }

    [data-baseweb="popover"] [data-baseweb="menu"] {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
    }
    [data-baseweb="popover"] [role="option"] {
        color: #c9d1d9 !important;
        font-size: 0.875rem !important;
        padding: 10px 16px !important;
        transition: background 0.1s ease !important;
    }
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="popover"] [aria-selected="true"] {
        background: #21262d !important;
        color: #f0f6fc !important;
        font-weight: 500 !important;
    }

    div[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
        background: #3fb950 !important;
        border-color: #3fb950 !important;
        box-shadow: 0 0 0 2px #0d1117 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background: #3fb950 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child {
        background: #30363d !important;
    }

    div[data-testid="stRadio"] > label {
        color: #c9d1d9 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.4rem !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        background: #111821;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid rgba(139, 148, 158, 0.18);
        width: fit-content;
        gap: 0;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        padding: 6px 16px;
        border-radius: 6px;
        background: transparent;
        cursor: pointer;
        transition: all 0.2s ease;
        margin: 0;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: #21262d;
        color: #f0f6fc !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
        background: #21262d;
        color: #f0f6fc !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    div[data-testid="stRadio"] [data-baseweb="radio"] div {
        margin: 0 !important;
    }
    div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
        color: inherit !important;
        margin: 0 !important;
    }
    div[data-testid="stRadio"] [data-baseweb="radio"] svg {
        display: none !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 8px !important;
        padding: 0.875rem 1rem !important;
        font-size: 0.875rem !important;
        line-height: 1.5 !important;
        border-left: 3px solid !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
    }
    div[data-testid="stAlert"][data-baseweb="notification"][kind="negative"],
    div[data-testid="stAlert"] > div[class*="error"],
    .element-container div[data-testid="stAlert"]:has([data-testid="stMarkdownContainer"] [class*="error"]) {
        background: rgba(248,81,73,0.08) !important;
        border-left-color: #f85149 !important;
        color: #ffa19b !important;
    }
    div[data-testid="stAlert"][kind="warning"] {
        background: rgba(210,153,34,0.08) !important;
        border-left-color: #d29922 !important;
        color: #e3b341 !important;
    }
    div[data-testid="stAlert"][kind="success"] {
        background: rgba(63,185,80,0.08) !important;
        border-left-color: #3fb950 !important;
        color: #56d364 !important;
    }
    div[data-testid="stAlert"][kind="info"] {
        background: rgba(56,139,253,0.08) !important;
        border-left-color: #388bfd !important;
        color: #79c0ff !important;
    }
    div[data-testid="stAlert"] {
        background-color: #111821 !important;
    }

    details[data-testid="stExpander"] {
        background: #111821 !important;
        border: 1px solid rgba(139, 148, 158, 0.16) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    details[data-testid="stExpander"] summary {
        background: transparent !important;
        color: #c9d1d9 !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
        cursor: pointer !important;
        transition: background 0.15s ease !important;
    }
    details[data-testid="stExpander"] summary:hover {
        background: rgba(255,255,255,0.03) !important;
    }
    details[data-testid="stExpander"] summary svg {
        color: #6e7681 !important;
    }

    div[data-testid="stSpinner"] > div {
        border-color: #3fb950 transparent transparent !important;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 1rem !important;
        align-items: stretch !important;
    }

    div[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] {
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: #8b949e !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 0.4rem !important;
    }

    code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82em !important;
        background: #21262d !important;
        color: #79c0ff !important;
        padding: 0.1em 0.4em !important;
        border-radius: 4px !important;
        border: 1px solid #30363d !important;
    }

    strong, b {
        color: #f0f6fc !important;
        font-weight: 600 !important;
    }

    .dr-hero {
        background:
            linear-gradient(135deg, rgba(35, 134, 54, 0.14), rgba(56, 139, 253, 0.08) 42%, rgba(248, 81, 73, 0.08)),
            #0f1721;
        border: 1px solid rgba(139, 148, 158, 0.16);
        border-radius: 8px;
        padding: clamp(1.2rem, 2vw, 1.9rem);
        margin-bottom: 1.25rem;
        box-shadow: 0 22px 55px rgba(0,0,0,0.22);
        position: relative;
        overflow: hidden;
    }
    .dr-hero::after {
        content: '';
        position: absolute;
        inset: auto 0 0 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(63,185,80,0.7), rgba(56,139,253,0.7), transparent);
    }
    .dr-kicker {
        color: #56d364 !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        line-height: 1.2 !important;
        margin: 0 0 0.45rem !important;
        text-transform: uppercase;
    }
    .dr-hero-title {
        color: #f0f6fc !important;
        font-size: 2.15rem !important;
        font-weight: 750 !important;
        letter-spacing: 0 !important;
        line-height: 1.08 !important;
        margin: 0 0 0.65rem !important;
    }
    .dr-hero-copy {
        color: #aeb8c4 !important;
        font-size: 0.95rem !important;
        line-height: 1.65 !important;
        max-width: 780px;
        margin: 0 !important;
    }
    .dr-hero-grid {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: end;
        gap: 1.25rem;
    }
    .dr-status-stack {
        display: grid;
        gap: 0.5rem;
        min-width: 210px;
    }
    .dr-status-pill {
        border: 1px solid rgba(139, 148, 158, 0.17);
        background: rgba(9, 13, 18, 0.45);
        border-radius: 8px;
        padding: 0.65rem 0.8rem;
        color: #c9d1d9;
        font-size: 0.78rem;
        line-height: 1.3;
    }
    .dr-status-pill span {
        display: block;
        color: #6e7681;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }

    @media (max-width: 900px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        .dr-hero-grid { grid-template-columns: 1fr; }
        .dr-status-stack { grid-template-columns: 1fr 1fr; min-width: 0; }
        .stTabs [data-baseweb="tab-list"] { overflow-x: auto; }
        .stTabs [data-baseweb="tab"] { white-space: nowrap; }
        .dr-hero-title { font-size: 1.8rem !important; }
    }

    @media (max-width: 640px) {
        div[data-testid="metric-container"] { min-height: 108px !important; }
        div[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
        .dr-status-stack { grid-template-columns: 1fr; }
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #484f58; }

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.markdown("""
<style>
.dr-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem clamp(1rem, 4vw, 4.5rem);
    background: rgba(9, 13, 18, 0.88);
    border-bottom: 1px solid rgba(139, 148, 158, 0.14);
    position: sticky;
    top: 0;
    z-index: 999;
    backdrop-filter: blur(16px);
}
.dr-navbar-brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
}
.dr-navbar-icon {
    width: 34px;
    height: 34px;
    background: linear-gradient(135deg, rgba(63,185,80,0.95), rgba(56,139,253,0.78));
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    box-shadow: 0 10px 26px rgba(35, 134, 54, 0.24);
}
.dr-navbar-title {
    font-size: 1rem;
    font-weight: 700;
    color: #f0f6fc;
    letter-spacing: 0;
    font-family: 'Inter', sans-serif;
}
.dr-navbar-title span { color: #3fb950; }
.dr-navbar-meta {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.dr-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(17, 24, 33, 0.82);
    border: 1px solid rgba(139, 148, 158, 0.16);
    border-radius: 9999px;
    padding: 0.22rem 0.65rem;
    font-size: 0.72rem;
    font-weight: 500;
    color: #8b949e;
    font-family: 'Inter', sans-serif;
    white-space: nowrap;
}
.dr-badge-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #3fb950;
    animation: pulseDot 2s infinite;
}
@keyframes pulseDot {
    0%,100% { opacity: 1; }
    50% { opacity: 0.35; }
}
@media (max-width: 720px) {
    .dr-navbar { align-items: flex-start; gap: 0.75rem; flex-direction: column; }
    .dr-navbar-meta { flex-wrap: wrap; }
}
</style>

<nav class="dr-navbar">
  <div class="dr-navbar-brand">
    <div class="dr-navbar-icon">🦟</div>
    <span class="dr-navbar-title">Dengue<span>Radar</span></span>
  </div>
  <div class="dr-navbar-meta">
    <span class="dr-badge"><span class="dr-badge-dot"></span>Recife · 2021–2025</span>
    <span class="dr-badge">SINAN · Prefeitura</span>
  </div>
</nav>
""", unsafe_allow_html=True)

_MAPA_CLASSI = {
    5: 'Descartado', 8: 'Inconclusivo',
    10: 'Dengue', 11: 'Dengue c/ Alarme',
    12: 'Dengue Grave', 13: 'Chikungunya',
}

_COR_RISCO = {
    'Baixo':    '#22c55e',
    'Moderado': '#eab308',
    'Alto':     '#f97316',
    'Crítico':  '#ef4444',
}

_PLOTLY_THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Inter", color="#c9d1d9"),
    xaxis=dict(gridcolor='#21262d', zerolinecolor='#30363d', linecolor='#30363d'),
    yaxis=dict(gridcolor='#21262d', zerolinecolor='#30363d', linecolor='#30363d'),
    legend=dict(font=dict(color="#c9d1d9")),
)

def aplicar_tema_plotly(fig, height=None):
    fig.update_layout(**_PLOTLY_THEME)
    fig.update_xaxes(showline=False, tickfont=dict(color="#8b949e"), title_font=dict(color="#8b949e"))
    fig.update_yaxes(showline=False, tickfont=dict(color="#8b949e"), title_font=dict(color="#8b949e"))
    if height:
        fig.update_layout(height=height)
    return fig

def calcular_resumo_ano(df_todos, ano_atual=2025, ano_base=2024):
    df_atual = df_todos[df_todos['ANO'] == ano_atual].copy()
    df_base = df_todos[df_todos['ANO'] == ano_base].copy()
    if df_atual.empty:
        return {}

    data_max = df_atual['DT_NOTIFIC'].max()
    if pd.notna(data_max):
        corte_base = data_max.replace(year=ano_base)
        df_base_comp = df_base[df_base['DT_NOTIFIC'].notna() & (df_base['DT_NOTIFIC'] <= corte_base)]
    else:
        df_base_comp = df_base

    casos_atual = len(df_atual)
    casos_base = len(df_base_comp)
    delta_casos = None if casos_base == 0 else ((casos_atual - casos_base) / casos_base) * 100

    graves = pd.to_numeric(df_atual.get('CLASSI_FIN'), errors='coerce').isin([11, 12])
    pct_graves = float(graves.mean() * 100) if len(df_atual) else 0.0

    bairros_com_casos = int(df_atual['NM_BAIRRO'].nunique()) if 'NM_BAIRRO' in df_atual else 0
    ultima_data = data_max.strftime('%d/%m/%Y') if pd.notna(data_max) else "N/D"

    return {
        'casos_atual': casos_atual,
        'casos_base': casos_base,
        'delta_casos': delta_casos,
        'pct_graves': pct_graves,
        'bairros_com_casos': bairros_com_casos,
        'ultima_data': ultima_data,
    }

@st.cache_data
def carregar_geojson_bairros():
    try:
        with open('dados/maparecife.geojson', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo 'maparecife.geojson' na pasta dados: {e}")
        return None

_FORMATO_DATA = {
    2021: '%d/%m/%Y',
    2022: '%Y-%m-%d',
    2023: '%Y-%m-%d',
    2024: '%d/%m/%Y',
    2025: None,  
}

def _ler_csv_ano(ano):
    if ano == 2025:
        path = 'dados/dados_2025.csv'
        df = pd.read_csv(path, sep=',', encoding='latin-1', on_bad_lines='skip', low_memory=False)
    else:
        path = f'dados/dados_{ano}.csv'
        df = pd.read_csv(path, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
    
    df.columns = [c.upper() for c in df.columns]
    df['ANO'] = ano
    fmt = _FORMATO_DATA.get(ano)
    if fmt:
        df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], format=fmt, errors='coerce')
    else:
        df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    return df

@st.cache_data
def carregar_todos_dados():
    frames = []
    for ano in [2021, 2022, 2023, 2024, 2025]:
        try:
            frames.append(_ler_csv_ano(ano))
        except Exception as e:
            st.warning(f"Não foi possível carregar dados de {ano} na pasta dados: {e}")
    
    if not frames:
        return pd.DataFrame()
        
    df = pd.concat(frames, ignore_index=True)
    df['Semana_Epi'] = (pd.to_numeric(df['SEM_NOT'], errors='coerce').round(0) % 100).astype('Int64')
    
    if 'NM_BAIRRO' in df.columns:
        df['NM_BAIRRO'] = df['NM_BAIRRO'].fillna('NAO INFORMADO').astype(str)
        def limpar_texto(txt):
            txt = txt.strip().upper()
            return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('utf-8')
        df['NM_BAIRRO'] = df['NM_BAIRRO'].apply(limpar_texto)
    return df

@st.cache_data
def calcular_score_risco_dinamico(df_todos, ano_alvo):
    anos = [2021, 2022, 2023, 2024, 2025]
    anos_arr = np.array(anos, dtype=float)
    anos_c = anos_arr - anos_arr.mean() 

    pivot = (
        df_todos.groupby(['NM_BAIRRO', 'ANO'])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=anos, fill_value=0)
    )

    if ano_alvo == "Todos os Anos":
        carga = pivot.sum(axis=1)
        anomalia = pd.Series(0.0, index=pivot.index)
        
        def slope_linear_total(row):
            y = row.values.astype(float)
            if y.sum() == 0: return 0.0
            coef = np.polyfit(anos_c, y, 1)
            return float(coef[0])
        tendencia = pivot.apply(slope_linear_total, axis=1)
        
        df_massa = df_todos.copy()
        df_massa['grave'] = pd.to_numeric(df_massa['CLASSI_FIN'], errors='coerce').isin([11, 12])
        sev = df_massa.groupby('NM_BAIRRO').agg(total=('grave', 'count'), graves=('grave', 'sum'))
        sev['pct_grave'] = sev['graves'] / sev['total']
        severidade = sev['pct_grave'].reindex(pivot.index).fillna(0)
    else:
        ano_val = int(ano_alvo)
        carga = pivot[ano_val].astype(float)
        
        anos_hist = [a for a in anos if a < ano_val]
        if anos_hist:
            hist = pivot[anos_hist].astype(float)
            hist_mean = hist.mean(axis=1)
            hist_std = hist.std(axis=1).where(lambda x: x > 0, 1.0)
            anomalia = ((pivot[ano_val] - hist_mean) / hist_std).clip(-3, 5)
        else:
            anomalia = pd.Series(0.0, index=pivot.index)
            
        anos_tend = [a for a in anos if a <= ano_val]
        if len(anos_tend) >= 2:
            anos_tend_arr = np.array(anos_tend, dtype=float)
            anos_tend_c = anos_tend_arr - anos_tend_arr.mean()
            def slope_linear_parcial(row):
                y = row[anos_tend].values.astype(float)
                if y.sum() == 0: return 0.0
                coef = np.polyfit(anos_tend_c, y, 1)
                return float(coef[0])
            tendencia = pivot.apply(slope_linear_parcial, axis=1)
        else:
            tendencia = pd.Series(0.0, index=pivot.index)
            
        df_ano = df_todos[df_todos['ANO'] == ano_val].copy()
        df_ano['grave'] = pd.to_numeric(df_ano['CLASSI_FIN'], errors='coerce').isin([11, 12])
        sev = df_ano.groupby('NM_BAIRRO').agg(total=('grave', 'count'), graves=('grave', 'sum'))
        sev['pct_grave'] = sev['graves'] / sev['total']
        severidade = sev['pct_grave'].reindex(pivot.index).fillna(0)

    def norm(s):
        mn, mx = s.min(), s.max()
        if mx == mn:
            return pd.Series(0.5, index=s.index)
        return (s - mn) / (mx - mn)

    c_norm = norm(carga)
    a_norm = norm(anomalia)
    t_norm = norm(tendencia)
    s_norm = norm(severidade)

    score = (0.30 * c_norm + 0.35 * a_norm + 0.20 * t_norm + 0.15 * s_norm) * 100

    score_df = pd.DataFrame({
        'Bairro':        pivot.index,
        'Casos':         carga.values.astype(int),
        'Anomalia (σ)':  anomalia.round(2).values,
        'Tendência':     tendencia.round(1).values,
        'Graves (%)':    (severidade * 100).round(1).values,
        'Score':         score.round(1).values,
    })

    score_df['Risco'] = score_df['Score'].apply(
        lambda v: 'Baixo' if v < 25 else 'Moderado' if v < 50 else 'Alto' if v < 75 else 'Crítico'
    )

    return score_df

@st.cache_data
def preparar_serie_mensal(df_todos, bairro="Recife — Total"):
    df = df_todos[df_todos['DT_NOTIFIC'].notna()].copy()
    if bairro != "Recife — Total":
        df = df[df['NM_BAIRRO'] == bairro]
    df['Ano_Mes'] = df['DT_NOTIFIC'].dt.to_period('M').dt.to_timestamp()
    serie = df.groupby('Ano_Mes').size().reset_index(name='Casos')
    serie = serie.sort_values('Ano_Mes').reset_index(drop=True)
    serie['t'] = np.arange(len(serie))
    serie['mes'] = serie['Ano_Mes'].dt.month
    serie['sin_t'] = np.sin(2 * np.pi * serie['mes'] / 12)
    serie['cos_t'] = np.cos(2 * np.pi * serie['mes'] / 12)
    return serie

def _treinar_modelo_producao(serie):
    X = serie[['t', 'sin_t', 'cos_t']].values
    y = serie['Casos'].values
    model = LinearRegression().fit(X, y)
    resid_std = float(np.std(y - model.predict(X)))
    return model, resid_std

def _backtest_2024(serie):
    treino = serie[serie['Ano_Mes'].dt.year <= 2023]
    teste  = serie[serie['Ano_Mes'].dt.year == 2024]
    if len(treino) < 10 or len(teste) < 3:
        return None, None, None
    X_tr = treino[['t', 'sin_t', 'cos_t']].values
    y_tr = treino['Casos'].values
    X_te = teste[['t', 'sin_t', 'cos_t']].values
    y_te = teste['Casos'].values
    m = LinearRegression().fit(X_tr, y_tr)
    y_pred = np.maximum(m.predict(X_te), 0)
    residuos_tr = float(np.std(y_tr - m.predict(X_tr)))
    return (
        float(r2_score(y_te, y_pred)),
        float(mean_absolute_error(y_te, y_pred)),
        float(np.sqrt(mean_squared_error(y_te, y_pred))),
        m, residuos_tr,
        treino, teste, y_pred,
    )

@st.cache_data(ttl=86400 * 7)
def buscar_dados_climaticos():
    cache_path = 'dados/clima_recife.csv'

    if os.path.exists(cache_path):
        idade_dias = (datetime.now().timestamp() - os.path.getmtime(cache_path)) / 86400
        if idade_dias < 7:
            return pd.read_csv(cache_path, parse_dates=['date'])

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        "?latitude=-8.0476&longitude=-34.8770"
        "&start_date=2021-01-01"
        f"&end_date={datetime.now().strftime('%Y-%m-%d')}"
        "&daily=precipitation_sum,temperature_2m_mean,relative_humidity_2m_mean"
        "&timezone=America%2FRecife"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame({
            'date': pd.to_datetime(data['daily']['time']),
            'precipitacao_mm': data['daily']['precipitation_sum'],
            'temp_media_c': data['daily']['temperature_2m_mean'],
            'umidade_pct': data['daily']['relative_humidity_2m_mean'],
        })
        df.to_csv(cache_path, index=False)
        return df
    except Exception:
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path, parse_dates=['date'])
        return None

def abrir_clima_mensal(df_clima):
    df = df_clima.copy()
    df['Ano_Mes'] = df['date'].dt.to_period('M').dt.to_timestamp()
    return df.groupby('Ano_Mes').agg(
        precipitacao_mm=('precipitacao_mm', 'sum'),
        temp_media_c=('temp_media_c', 'mean'),
        umidade_pct=('umidade_pct', 'mean'),
    ).reset_index()

def _gerar_previsao_6m(serie, model, resid_std):
    t_last    = int(serie['t'].max())
    last_date = serie['Ano_Mes'].max()
    datas = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=6, freq='MS')
    t_fut = np.arange(t_last + 1, t_last + 7)
    mes   = datas.month
    X_fut = np.column_stack([t_fut, np.sin(2 * np.pi * mes / 12), np.cos(2 * np.pi * mes / 12)])
    y_fut = np.maximum(model.predict(X_fut), 0)
    return pd.DataFrame({
        'Ano_Mes':  datas,
        'Previsao': y_fut,
        'IC_inf':   np.maximum(y_fut * 0.90, 0),
        'IC_sup':   y_fut * 1.10,
    })

with st.spinner('Sincronizando microdados e mapas locais...'):
    geojson_bairros = carregar_geojson_bairros()
    try:
        df_todos = carregar_todos_dados()
        carregado_com_sucesso = not df_todos.empty
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        carregado_com_sucesso = False

if carregado_com_sucesso and not df_todos.empty:

    todos_bairros = sorted(df_todos['NM_BAIRRO'].unique())

    df_2025_global = df_todos[df_todos['ANO'] == 2025].copy()
    total_casos_global = len(df_2025_global)
    bairro_critico_global = df_2025_global['NM_BAIRRO'].value_counts().index[0] if not df_2025_global.empty else "N/D"

    aba_geral, aba_analitica, aba_previsao, aba_clima = st.tabs([
        "🟢 Visão Geral da Cidade",
        "📍 Mapa e Análise por Bairro",
        "🔮 Previsão",
        "🌧️ Clima e Correlação",
    ])

    with aba_geral:
        st.markdown(f"""
        <div class="dr-hero">
          <div class="dr-hero-grid">
            <div>
              <p class="dr-kicker">Cenário Epidemiológico</p>
              <h1 class="dr-hero-title">DengueRadar Recife</h1>
              <p class="dr-hero-copy">
                Painel de vigilância para acompanhar notificações, risco territorial,
                tendência temporal e sinais ambientais associados à dengue em Recife.
              </p>
            </div>
            <div class="dr-status-stack">
              <div class="dr-status-pill"><span>Período</span>2021 a 2025</div>
              <div class="dr-status-pill"><span>Fonte</span>SINAN Recife</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        resumo_2025 = calcular_resumo_ano(df_todos)
        delta_2025 = resumo_2025.get('delta_casos')
        delta_txt = None if delta_2025 is None else f"{delta_2025:+.1f}% vs. 2024 no mesmo período"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Notificações em 2025", f"{resumo_2025.get('casos_atual', total_casos_global):,}", delta_txt)
        col2.metric("Epicentro Atual", bairro_critico_global.title() if bairro_critico_global != "N/D" else "N/D")
        col3.metric("Bairros com Casos", f"{resumo_2025.get('bairros_com_casos', 0)}")
        col4.metric("Casos com Alarme/Graves", f"{resumo_2025.get('pct_graves', 0):.1f}%", f"Atualizado em {resumo_2025.get('ultima_data', 'N/D')}")

        st.divider()

        col_titulo_hist, col_filtro_hist = st.columns([3, 1])
        with col_titulo_hist:
            st.markdown("""
            <div style="padding-top:0.5rem">
                <p style="font-size:0.72rem;font-weight:500;text-transform:uppercase;
                          letter-spacing:0.08em;color:#6e7681;margin:0 0 0.2rem;">Série Histórica</p>
                <h2 style="font-size:1.1rem;font-weight:600;color:#f0f6fc;margin:0;letter-spacing:0;">
                    Casos de Dengue · 2021–2025
                </h2>
            </div>
            """, unsafe_allow_html=True)
        with col_filtro_hist:
            modo_hist = st.radio(
                "Visualizar por:",
                ["Semana Epidemiológica", "Mês"],
                horizontal=True,
                key="radio_hist",
            )

        if modo_hist == "Semana Epidemiológica":
            semana_valida = df_todos['Semana_Epi'].notna() & (df_todos['Semana_Epi'] >= 1) & (df_todos['Semana_Epi'] <= 52)
            casos_historico = (
                df_todos[semana_valida]
                .groupby(['ANO', 'Semana_Epi'])
                .size()
                .reset_index(name='Casos')
            )
            casos_historico['Semana_Epi'] = casos_historico['Semana_Epi'].astype(int)
            casos_historico['ANO'] = casos_historico['ANO'].astype(str)

            fig_area = px.area(
                casos_historico,
                x='Semana_Epi', y='Casos', color='ANO',
                labels={'Semana_Epi': 'Semana Epidemiológica', 'Casos': 'Notificações', 'ANO': 'Ano'},
                color_discrete_sequence=px.colors.qualitative.Set2,
                template="plotly_white"
            )
            fig_area.update_traces(line_shape='spline', mode='lines+markers', marker=dict(size=4))
            fig_area.update_layout(
                xaxis=dict(dtick=1, showgrid=False), margin=dict(t=10),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                legend=dict(title='Ano', orientation='h', y=1.05),
                hovermode="x unified",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
        else:
            _MESES = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                      7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
            df_com_data = df_todos[df_todos['DT_NOTIFIC'].notna()].copy()
            df_com_data['Mes'] = df_com_data['DT_NOTIFIC'].dt.month
            casos_historico = (
                df_com_data.groupby(['ANO', 'Mes'])
                .size()
                .reset_index(name='Casos')
            )
            casos_historico['Mês'] = casos_historico['Mes'].map(_MESES)
            casos_historico['ANO'] = casos_historico['ANO'].astype(str)
            casos_historico = casos_historico.sort_values(['ANO', 'Mes'])

            fig_area = px.line(
                casos_historico,
                x='Mês', y='Casos', color='ANO',
                category_orders={'Mês': list(_MESES.values())},
                labels={'Mês': 'Mês', 'Casos': 'Notificações', 'ANO': 'Ano'},
                color_discrete_sequence=px.colors.qualitative.Set2,
                template="plotly_white"
            )
            fig_area.update_traces(
                line_shape='linear',
                mode='lines+markers',
                line=dict(width=3),
                marker=dict(size=5, line=dict(width=0)),
            )
            fig_area.update_layout(
                margin=dict(t=28),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
                legend=dict(title=None, orientation='h', y=1.12, x=0),
                hovermode="x unified",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

        aplicar_tema_plotly(fig_area)
        st.plotly_chart(fig_area, use_container_width=True)

    with aba_analitica:
        col_filtro_aba2, _ = st.columns([1, 3])
        with col_filtro_aba2:
            ano_selecionado = st.selectbox(
                "Selecione o Ano de Análise:",
                ["Todos os Anos", 2025, 2024, 2023, 2022, 2021],
                index=1,
                key="filtro_ano_mapa"
            )

        df_score_aba2 = calcular_score_risco_dinamico(df_todos, ano_selecionado)

        if ano_selecionado == "Todos os Anos":
            df_aba2 = df_todos.copy()
        else:
            df_aba2 = df_todos[df_todos['ANO'] == int(ano_selecionado)].copy()

        st.markdown(f"""
        <div style="margin-bottom:1rem;">
            <p style="font-size:0.72rem;font-weight:500;text-transform:uppercase;
                      letter-spacing:0.08em;color:#3fb950;margin:0 0 0.25rem;">
                Inteligência Geográfica
            </p>
            <h1 style="font-size:1.4rem;font-weight:700;color:#f0f6fc;margin:0;letter-spacing:0;">
                Central de Alertas — {ano_selecionado}
            </h1>
        </div>
        """, unsafe_allow_html=True)

        bairros_criticos = df_score_aba2[df_score_aba2['Risco'] == 'Crítico']
        bairros_alto = df_score_aba2[df_score_aba2['Risco'] == 'Alto']

        if not bairros_criticos.empty:
            st.error(f"🚨 **ALERTA EPIDEMIOLÓGICO:** {len(bairros_criticos)} bairros encontram-se em **Nível Crítico** de risco. Selecione uma localidade para verificar as diretrizes.")
        elif not bairros_alto.empty:
            st.warning(f"⚠️ **ATENÇÃO:** O sistema detectou {len(bairros_alto)} bairros em **Risco Alto**. Recomenda-se acompanhamento preventivo.")
        else:
            st.success("✅ **MONITORAMENTO:** Nenhum bairro em nível crítico extremo detectado no momento.")

        c_notif1, c_notif2, c_notif3, c_notif4 = st.columns(4)
        c_notif1.metric("🔴 Risco Crítico", f"{len(bairros_criticos)} Bairros")
        c_notif2.metric("🟠 Risco Alto", f"{len(bairros_alto)} Bairros")
        c_notif3.metric("🟡 Risco Moderado", f"{len(df_score_aba2[df_score_aba2['Risco'] == 'Moderado'])} Bairros")
        c_notif4.metric("🟢 Risco Baixo", f"{len(df_score_aba2[df_score_aba2['Risco'] == 'Baixo'])} Bairros")

        st.divider()

        col_mapa, col_rank = st.columns([1.6, 1])
        bairro_clicado = None

        with col_mapa:
            st.markdown(f"**Score de Risco por Bairro ({ano_selecionado} - Clique para detalhar)**")
            if geojson_bairros:
                fig_mapa = px.choropleth_mapbox(
                    df_score_aba2, geojson=geojson_bairros,
                    locations='Bairro', featureidkey='properties.EBAIRRNOME',
                    color='Risco',
                    color_discrete_map=_COR_RISCO,
                    category_orders={'Risco': ['Baixo', 'Moderado', 'Alto', 'Crítico']},
                    mapbox_style="carto-positron", zoom=10.5,
                    center={"lat": -8.058, "lon": -34.91},
                    opacity=0.75, hover_name='Bairro',
                    hover_data={
                        'Score': True,
                        'Casos': True,
                        'Anomalia (σ)': True,
                        'Tendência': True,
                        'Graves (%)': True,
                        'Risco': False,
                    },
                )
                fig_mapa.update_layout(
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    paper_bgcolor='rgba(0,0,0,0)'
                )

                mapa_evento = st.plotly_chart(
                    fig_mapa,
                    use_container_width=True,
                    on_select="rerun",
                    selection_mode="points",
                    key="mapa_bairros",
                )

                if mapa_evento and len(mapa_evento.selection.points) > 0:
                    bairro_clicado = mapa_evento.selection.points[0]["location"]
            else:
                st.warning("Arquivo 'maparecife.geojson' não encontrado na pasta dados.")

        with col_rank:
            df_bairros = df_aba2['NM_BAIRRO'].value_counts().reset_index()
            df_bairros.columns = ['Bairro', 'Notificações']

            st.markdown(f"**Top 10 Bairros — {ano_selecionado}**")
            fig_rank = px.bar(
                df_bairros.head(10).sort_values('Notificações', ascending=True),
                x='Notificações', y='Bairro', orientation='h',
                color_discrete_sequence=["#2563eb"], 
                template="plotly_white"
            )
            fig_rank.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), 
                height=400,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            aplicar_tema_plotly(fig_rank, height=400)
            st.plotly_chart(fig_rank, use_container_width=True)

        st.divider()
        st.markdown("""
        <div style="padding: 0.5rem 0 0.75rem;">
            <p style="font-size:0.72rem;font-weight:500;text-transform:uppercase;
                      letter-spacing:0.08em;color:#6e7681;margin:0 0 0.2rem;">
                Por Localidade
            </p>
                <h2 style="font-size:1.1rem;font-weight:600;color:#f0f6fc;margin:0;letter-spacing:0;">
                Detalhamento Técnico e Insights de Gestão
            </h2>
        </div>
        """, unsafe_allow_html=True)

        col_selecao_bairro, _ = st.columns([1, 3])
        with col_selecao_bairro:
            index_padrao = 0
            if bairro_clicado and bairro_clicado in todos_bairros:
                index_padrao = todos_bairros.index(bairro_clicado)
                st.success(f"📍 Filtro ativo por clique no mapa: **{bairro_clicado}**")

            escolha = st.selectbox(
                "Selecione um bairro (ou clique diretamente no mapa acima):",
                todos_bairros,
                index=index_padrao,
            )

        row_score = df_score_aba2[df_score_aba2['Bairro'] == escolha].iloc[0]
        tendencia_bairro = row_score['Tendência']
        sinal = "+" if tendencia_bairro > 0 else ""
        tendencia_arredondada = int(round(tendencia_bairro))

        m1, m2, m3 = st.columns(3)
        m1.metric("Score Algorítmico", f"{row_score['Score']:.1f} / 100")
        m2.metric("Classificação de Risco Atual", row_score['Risco'])
        m3.metric("Projeção Temporal", f"{sinal}{tendencia_arredondada}", "Novos Casos/Ano (Tendência)")

        st.info(f"**ANÁLISE PREDITIVA E CONTEXTO ({escolha}):** O cálculo de regressão linear baseado na série histórica identifica um desvio de **{row_score['Anomalia (σ)']} σ** e uma taxa de gravidade clínica de **{row_score['Graves (%)']}%** dos casos.")

        col_grafico, col_insights = st.columns([1.5, 1])

        with col_grafico:
            historico_bairro = (
                df_todos[df_todos['NM_BAIRRO'] == escolha]
                .groupby('ANO').size().reset_index(name='Casos')
            )
            historico_bairro['ANO'] = historico_bairro['ANO'].astype(str)
            fig_individual = px.bar(
                historico_bairro, x='ANO', y='Casos',
                color_discrete_sequence=["#3b82f6"],
                text='Casos',
                template="plotly_white"
            )
            fig_individual.update_traces(textposition='outside', textfont_size=12, marker_line_width=0)
            fig_individual.update_layout(
                height=300, 
                yaxis=dict(range=[0, historico_bairro['Casos'].max() * 1.2], showgrid=True, gridcolor='#f1f5f9'), 
                xaxis=dict(showgrid=False),
                margin=dict(t=20, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            aplicar_tema_plotly(fig_individual, height=300)
            st.plotly_chart(fig_individual, use_container_width=True)

        with col_insights:
            casos_bairro = df_aba2[df_aba2['NM_BAIRRO'] == escolha].shape[0]
            risco_atual = row_score['Risco']
            pct_graves = row_score['Graves (%)']
            tendencia = row_score['Tendência']
            anomalia = row_score['Anomalia (σ)']

            if risco_atual == 'Crítico':
                agentes_necessarios = min(12, max(8, int(np.sqrt(casos_bairro) / 1.5)))
            elif risco_atual == 'Alto':
                agentes_necessarios = min(8, max(5, int(np.sqrt(casos_bairro) / 2)))
            elif risco_atual == 'Moderado':
                agentes_necessarios = min(4, max(3, int(np.sqrt(casos_bairro) / 3)))
            else:
                agentes_necessarios = 2 

            if risco_atual in ['Crítico', 'Alto']:
                st.error(f"**🚨 Risco de Colapso (Atenção Básica):**\nO volume atual de notificações em {escolha} exige acionamento do protocolo de contingência. A proporção de quadros clínicos severos (com alarme ou graves) está em **{pct_graves}%**. Recomenda-se reforço imediato de leitos de observação e insumos de hidratação venosa nas unidades da região.")
                
                st.error(f"**🔥 Força-Tarefa (Controle Vetorial):**\nA situação exige bloqueio de transmissão urgente. Sugestão: deslocar até **{agentes_necessarios} agentes** para realizar varredura intensiva e priorizar a aplicação de fumacê espacial (UBV) num raio de 300m dos focos confirmados.")
                
                anomalia_txt = f"(alerta de +{anomalia} desvios padrões)" if anomalia > 1.5 else ""
                st.error(f"**⚠️ Alerta Ambiental e Infraestrutura:**\nA curva de contágio está significativamente descolada do padrão histórico esperado para o bairro {anomalia_txt}. Acionar a Emlurb para mapeamento emergencial, desobstrução de canais de drenagem e remoção de lixo irregular.")

            elif risco_atual == 'Moderado':
                dinamica = "O viés de crescimento" if tendencia > 0 else "A trajetória atual"
                sinal_t = "+" if tendencia > 0 else ""
                
                st.warning(f"**🏥 Gargalo Primário (UBS):**\n{dinamica} de **{sinal_t}{tendencia:.1f} casos/ano** acende um alerta amarelo para a triagem em {escolha}. A gestão deve garantir estoques preventivos de Soro de Reidratação Oral (SRO) e monitorar o tempo de espera nos postos de saúde.")
                
                st.warning(f"**🚶‍♂️ Bloqueio Focal (Agentes de Endemias):**\nCenário requer reforço territorial de nível intermediário. Empregar **~{agentes_necessarios} agentes** para mutirões focados na eliminação de criadouros mecânicos (pneus, caixas d'água destampadas) e aplicação de larvicida biológico.")
                
                st.warning(f"**🌧️ Risco Ambiental Preventivo:**\nDirecionar equipes de zeladoria urbana para inspecionar pontos crônicos de alagamento e terrenos baldios mapeados em {escolha}, visando cortar o ciclo do vetor antes que o bairro entre em Risco Alto.")

            else:
                st.success(f"**✅ Estabilidade Clínica (Rede de Saúde):**\nO fluxo epidemiológico em {escolha} encontra-se estabilizado. A taxa atual de gravidade (**{pct_graves}%**) sugere que a rede consegue absorver a demanda e manter os atendimentos de rotina sem sobrecarga.")
                
                st.success(f"**🧹 Cobertura de Rotina (Vigilância Ambiental):**\nO volume de casos é compatível com o controle endêmico padrão. Manter o ciclo de visitas domiciliares de rotina com **~{agentes_necessarios} agentes** designados para a microárea.")
                
                st.success(f"**🌱 Ambiente Controlado:**\nSem detecção de anomalias estatísticas no momento. A estratégia recomendada é a manutenção de campanhas contínuas em escolas e redes sociais orientando a população sobre o acúmulo intradomiciliar de água.")

    with aba_previsao:
        st.markdown("""
        <div style="margin-bottom:1rem;">
            <p style="font-size:0.72rem;font-weight:500;text-transform:uppercase;
                      letter-spacing:0.08em;color:#3fb950;margin:0 0 0.25rem;">
                Modelagem Preditiva
            </p>
            <h1 style="font-size:1.4rem;font-weight:700;color:#f0f6fc;margin:0 0 0.3rem;letter-spacing:0;">
                Previsão de Casos
            </h1>
            <p style="font-size:0.8rem;color:#6e7681;margin:0;">
                Regressão linear com sazonalidade harmônica (sin/cos). Treinado em 2021–2025.
                Backtest: treino 2021–2023 → teste 2024.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_ctrl, _ = st.columns([1, 3])
        with col_ctrl:
            opcoes_escopo = ["Recife — Total"] + sorted(df_todos['NM_BAIRRO'].dropna().unique().tolist())
            escopo_prev = st.selectbox("Escopo geográfico:", opcoes_escopo, key="sel_prev_escopo")

        serie = preparar_serie_mensal(df_todos, escopo_prev)

        if len(serie) < 12:
            st.warning("Dados mensais insuficientes para modelagem neste bairro (mínimo: 12 meses).")
        else:
            model_prod, resid_std = _treinar_modelo_producao(serie)
            resultado_bt = _backtest_2024(serie)
            df_prev = _gerar_previsao_6m(serie, model_prod, resid_std)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Meses de histórico", f"{len(serie)}")
            if resultado_bt[0] is not None:
                r2_bt, mae_bt, rmse_bt = resultado_bt[0], resultado_bt[1], resultado_bt[2]
                c2.metric("R² — Backtest 2024", f"{max(r2_bt, 0.0):.3f}")
                c3.metric("MAE — Backtest 2024", f"{mae_bt:.0f} casos/mês")
                c4.metric("RMSE — Backtest 2024", f"{rmse_bt:.0f} casos/mês")
            else:
                c2.metric("R²", "N/D")
                c3.metric("MAE", "N/D")
                c4.metric("RMSE", "N/D")

            st.divider()

            fig_prev = go.Figure()

            fig_prev.add_trace(go.Scatter(
                x=serie['Ano_Mes'], y=serie['Casos'],
                name='Histórico Real',
                line=dict(color='#3b82f6', width=2, shape='spline'),
                mode='lines',
            ))

            x_band = list(df_prev['Ano_Mes']) + list(df_prev['Ano_Mes'])[::-1]
            y_band = list(df_prev['IC_sup']) + list(df_prev['IC_inf'])[::-1]
            fig_prev.add_trace(go.Scatter(
                x=x_band, y=y_band,
                fill='toself',
                fillcolor='rgba(59, 130, 246, 0.1)',
                line=dict(color='rgba(0,0,0,0)'),
                name='Margem ±10%',
            ))

            fig_prev.add_trace(go.Scatter(
                x=df_prev['Ano_Mes'], y=df_prev['Previsao'],
                name='Previsão (próximos 6 meses)',
                line=dict(color='#f97316', width=2, dash='dash', shape='spline'),
                mode='lines+markers',
                marker=dict(size=6),
            ))

            fig_prev.update_layout(
                xaxis_title='Mês',
                yaxis_title='Notificações Mensais',
                yaxis=dict(rangemode='tozero', showgrid=True, gridcolor='#f1f5f9'),
                xaxis=dict(showgrid=False),
                legend=dict(orientation='h', y=1.08, x=0),
                margin=dict(t=10, b=0),
                height=420,
                hovermode="x unified",
                template="plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            aplicar_tema_plotly(fig_prev, height=420)
            st.plotly_chart(fig_prev, use_container_width=True)

            with st.expander("📊 Ver backtest: modelo vs. real em 2024"):
                if resultado_bt[0] is not None:
                    _, _, _, m_bt, res_bt, treino_bt, teste_bt, y_pred_bt = resultado_bt
                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(
                        x=treino_bt['Ano_Mes'], y=treino_bt['Casos'],
                        name='Treino (2021–2023)', line=dict(color='#3b82f6', width=2, shape='spline'),
                    ))
                    fig_bt.add_trace(go.Scatter(
                        x=teste_bt['Ano_Mes'], y=teste_bt['Casos'],
                        name='Real 2024', line=dict(color='#22c55e', width=2, shape='spline'),
                    ))
                    x_band_bt = list(teste_bt['Ano_Mes']) + list(teste_bt['Ano_Mes'])[::-1]
                    y_band_bt = (
                        list(y_pred_bt * 1.10)
                        + list(np.maximum(y_pred_bt * 0.90, 0))[::-1]
                    )
                    fig_bt.add_trace(go.Scatter(
                        x=x_band_bt, y=y_band_bt,
                        fill='toself', fillcolor='rgba(249, 115, 22, 0.1)',
                        line=dict(color='rgba(0,0,0,0)'), name='Margem ±10%',
                    ))
                    fig_bt.add_trace(go.Scatter(
                        x=teste_bt['Ano_Mes'], y=y_pred_bt,
                        name='Previsto 2024',
                        line=dict(color='#f97316', width=2, dash='dash', shape='spline'),
                        mode='lines+markers', marker=dict(size=5),
                    ))
                    fig_bt.update_layout(
                        xaxis_title='Mês', yaxis_title='Casos',
                        yaxis=dict(rangemode='tozero', showgrid=True, gridcolor='#f1f5f9'),
                        xaxis=dict(showgrid=False),
                        legend=dict(orientation='h', y=1.12),
                        margin=dict(t=10), height=300,
                        hovermode="x unified",
                        template="plotly_white",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    aplicar_tema_plotly(fig_bt, height=300)
                    st.plotly_chart(fig_bt, use_container_width=True)
                else:
                    st.info("Dados insuficientes para exibir backtest deste bairro.")

            st.divider()
            _MESES_PT = {
                1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
                5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
                9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro',
            }
            coef_trend = model_prod.coef_[0]
            idx_pico   = df_prev['Previsao'].idxmax()
            pico_mes   = df_prev.loc[idx_pico, 'Ano_Mes']
            pico_val   = int(round(df_prev.loc[idx_pico, 'Previsao']))
            dir_trend  = "crescimento" if coef_trend > 0 else "queda"
            escopo_label = "Recife" if escopo_prev == "Recife — Total" else escopo_prev.title()

            st.info(
                f"**Interpretação do modelo — {escopo_label}:** "
                f"A série histórica apresenta tendência de **{dir_trend}** de "
                f"**{abs(coef_trend):.1f} casos/mês**. "
                f"Nos próximos 6 meses, o pico projetado é de "
                f"**{pico_val} notificações** em **{_MESES_PT[pico_mes.month]}/{pico_mes.year}**."
            )

    with aba_clima:
        st.markdown("""
        <div style="margin-bottom:1rem;">
            <p style="font-size:0.72rem;font-weight:500;text-transform:uppercase;
                      letter-spacing:0.08em;color:#3fb950;margin:0 0 0.25rem;">
                Análise Ambiental
            </p>
            <h1 style="font-size:1.4rem;font-weight:700;color:#f0f6fc;margin:0 0 0.3rem;letter-spacing:0;">
                Clima e Correlação
            </h1>
            <p style="font-size:0.8rem;color:#6e7681;margin:0;">
                Dados meteorológicos via Open-Meteo (ERA5 reanalysis). A defasagem captura o ciclo biológico
                do <em>Aedes aegypti</em> (~2–4 semanas após evento climático).
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("Carregando dados climáticos..."):
            df_clima = buscar_dados_climaticos()

        if df_clima is None:
            st.warning(
                "Não foi possível carregar dados climáticos. "
                "Verifique a conexão com a internet e tente novamente."
            )
        else:
            df_clima_mensal = abrir_clima_mensal(df_clima)
            serie_dengue = preparar_serie_mensal(df_todos, "Recife — Total")

            df_merged_base = pd.merge(
                serie_dengue[['Ano_Mes', 'Casos']],
                df_clima_mensal,
                on='Ano_Mes', how='inner',
            )

            clima_2025 = df_clima_mensal[df_clima_mensal['Ano_Mes'].dt.year == 2025]
            if not clima_2025.empty:
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Precipitação Acumulada 2025", f"{clima_2025['precipitacao_mm'].sum():.0f} mm")
                col_m2.metric("Temperatura Média 2025", f"{clima_2025['temp_media_c'].mean():.1f} °C")
                col_m3.metric("Umidade Média 2025", f"{clima_2025['umidade_pct'].mean():.0f}%")

            st.divider()

            col_lag, _ = st.columns([1, 3])
            with col_lag:
                lag_meses = st.slider(
                    "Defasagem temporal (meses):",
                    min_value=0, max_value=4, value=1,
                    help=(
                        "Desloca os dados climáticos N meses à frente para capturar o ciclo biológico "
                        "do mosquito (~2–4 semanas do ovo à fase adulta após evento de chuva/calor)."
                    ),
                )

            if lag_meses > 0:
                df_clima_lag = df_clima_mensal.copy()
                df_clima_lag['Ano_Mes'] = df_clima_lag['Ano_Mes'] + pd.DateOffset(months=lag_meses)
                df_plot = pd.merge(
                    serie_dengue[['Ano_Mes', 'Casos']],
                    df_clima_lag,
                    on='Ano_Mes', how='inner',
                )
            else:
                df_plot = df_merged_base.copy()

            if len(df_plot) >= 6:
                corr_precip = float(df_plot['Casos'].corr(df_plot['precipitacao_mm']))
                corr_temp   = float(df_plot['Casos'].corr(df_plot['temp_media_c']))
                corr_umid   = float(df_plot['Casos'].corr(df_plot['umidade_pct']))

                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Correlação Precipitação × Casos", f"{corr_precip:+.3f}")
                cc2.metric("Correlação Temperatura × Casos",  f"{corr_temp:+.3f}")
                cc3.metric("Correlação Umidade × Casos",      f"{corr_umid:+.3f}")
            else:
                corr_precip = corr_temp = corr_umid = None

            st.divider()

            lag_label = f"{lag_meses} {'mês' if lag_meses == 1 else 'meses'}" if lag_meses > 0 else "sem defasagem"
            st.markdown(f"**Casos Mensais vs. Precipitação Acumulada (defasagem: {lag_label})**")

            fig_dual = go.Figure()
            fig_dual.add_trace(go.Bar(
                x=df_plot['Ano_Mes'],
                y=df_plot['Casos'],
                name='Casos Dengue',
                marker_color='#ef4444',
                opacity=0.8,
                yaxis='y1',
            ))
            fig_dual.add_trace(go.Scatter(
                x=df_plot['Ano_Mes'],
                y=df_plot['precipitacao_mm'],
                name=f'Precipitação acumulada (lag {lag_meses}m)',
                line=dict(color='#3b82f6', width=2, shape='spline'),
                mode='lines+markers',
                marker=dict(size=4),
                yaxis='y2',
            ))
            fig_dual.update_layout(
                yaxis=dict(title=dict(text='Notificações Mensais', font=dict(color='#ef4444')), tickfont=dict(color='#ef4444'), showgrid=False),
                yaxis2=dict(title=dict(text='Precipitação (mm)', font=dict(color='#3b82f6')), tickfont=dict(color='#3b82f6'),
                            overlaying='y', side='right', showgrid=True, gridcolor='#f1f5f9'),
                xaxis=dict(showgrid=False),
                legend=dict(orientation='h', y=1.08, x=0),
                margin=dict(t=10, b=0),
                height=400,
                hovermode="x unified",
                template="plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter")
            )
            aplicar_tema_plotly(fig_dual, height=400)
            st.plotly_chart(fig_dual, use_container_width=True)

            st.divider()

            st.markdown("**Temperatura Média e Umidade Relativa do Ar — Recife (2021–2025)**")
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=df_clima_mensal['Ano_Mes'],
                y=df_clima_mensal['temp_media_c'],
                name='Temperatura Média (°C)',
                line=dict(color='#f97316', width=2, shape='spline'),
                mode='lines',
            ))
            fig_temp.add_trace(go.Scatter(
                x=df_clima_mensal['Ano_Mes'],
                y=df_clima_mensal['umidade_pct'],
                name='Umidade Relativa (%)',
                line=dict(color='#64748b', width=2, shape='spline'),
                mode='lines',
                yaxis='y2',
            ))
            fig_temp.update_layout(
                yaxis=dict(title=dict(text='Temperatura (°C)', font=dict(color='#f97316')), tickfont=dict(color='#f97316'), showgrid=False),
                yaxis2=dict(title=dict(text='Umidade (%)', font=dict(color='#64748b')), tickfont=dict(color='#64748b'),
                            overlaying='y', side='right', showgrid=True, gridcolor='#f1f5f9'),
                xaxis=dict(showgrid=False),
                legend=dict(orientation='h', y=1.08, x=0),
                margin=dict(t=10, b=0),
                height=350,
                hovermode="x unified",
                template="plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter")
            )
            aplicar_tema_plotly(fig_temp, height=350)
            st.plotly_chart(fig_temp, use_container_width=True)

            if corr_precip is not None:
                variaveis = [
                    ('precipitação', corr_precip),
                    ('temperatura', corr_temp),
                    ('umidade', corr_umid),
                ]
                nome_var, val_corr = max(variaveis, key=lambda x: abs(x[1]))
                forca   = "forte" if abs(val_corr) > 0.6 else "moderada" if abs(val_corr) > 0.3 else "fraca"
                direcao = "positiva" if val_corr > 0 else "negativa"
                precede = "precedem" if lag_meses > 0 else "acompanham"

                st.info(
                    f"**Análise de Correlação ({lag_label}):** "
                    f"A variável climática com maior influência sobre os casos é a **{nome_var}** "
                    f"(r = {val_corr:+.3f}), indicando correlação **{forca} e {direcao}**. "
                    f"Variações na {nome_var} tendem a {precede} mudanças no número de "
                    f"notificações de dengue em Recife."
                )

else:
    st.info("Certifique-se de que a pasta 'dados/' contém os arquivos CSV e o GeoJSON.")
