import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json
import unicodedata


st.set_page_config(page_title="DengueRadar | Recife", layout="wide", page_icon="🦟")
st.title("🦟 DengueRadar: Monitoramento Recife")
st.caption("📌 Fonte: Microdados Oficiais (SINAN/Prefeitura do Recife) | Anos: 2021–2025")

_MAPA_CLASSI = {
    5: 'Descartado', 8: 'Inconclusivo',
    10: 'Dengue', 11: 'Dengue c/ Alarme',
    12: 'Dengue Grave', 13: 'Chikungunya',
}

_COR_RISCO = {
    'Baixo':    '#2ca02c',
    'Moderado': '#f9c74f',
    'Alto':     '#ff7f0e',
    'Crítico':  '#d62728',
}

@st.cache_data
def carregar_geojson_bairros():
    try:
        with open('maparecife.geojson', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo 'maparecife.geojson': {e}")
        return None

def _ler_csv_ano(ano):
    if ano == 2025:
        df = pd.read_csv('dados_2025.csv', sep=',', encoding='latin-1', on_bad_lines='skip', low_memory=False)
    else:
        df = pd.read_csv(f'dados_{ano}.csv', sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    df['ANO'] = ano
    return df

@st.cache_data
def carregar_todos_dados():
    frames = []
    for ano in [2021, 2022, 2023, 2024, 2025]:
        try:
            frames.append(_ler_csv_ano(ano))
        except Exception as e:
            st.warning(f"Não foi possível carregar dados de {ano}: {e}")
    df = pd.concat(frames, ignore_index=True)
    df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    df['Semana_Epi'] = (pd.to_numeric(df['SEM_NOT'], errors='coerce').round(0) % 100).astype('Int64')
    if 'NM_BAIRRO' in df.columns:
        df['NM_BAIRRO'] = df['NM_BAIRRO'].fillna('NAO INFORMADO').astype(str)
        def limpar_texto(txt):
            txt = txt.strip().upper()
            return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('utf-8')
        df['NM_BAIRRO'] = df['NM_BAIRRO'].apply(limpar_texto)
    return df

@st.cache_data
def calcular_score_risco(df_todos):
    anos = [2021, 2022, 2023, 2024, 2025]
    anos_arr = np.array(anos, dtype=float)
    anos_c = anos_arr - anos_arr.mean()  # centralizado para regressão estável

    # Pivot: bairro × ano (casos totais)
    pivot = (
        df_todos.groupby(['NM_BAIRRO', 'ANO'])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=anos, fill_value=0)
    )

    # --- Componente 1: Carga atual (casos 2025) ---
    carga = pivot[2025].astype(float)

    # --- Componente 2: Anomalia histórica ---
    # Z-score de 2025 em relação à média e desvio padrão dos 4 anos anteriores
    hist = pivot[[2021, 2022, 2023, 2024]].astype(float)
    hist_mean = hist.mean(axis=1)
    hist_std  = hist.std(axis=1)
    # Bairros com std=0 (histórico constante): usar std mínimo de 1 caso para evitar inflação
    hist_std = hist_std.where(hist_std > 0, 1.0)
    anomalia = ((pivot[2025] - hist_mean) / hist_std).clip(-3, 5)

    # --- Componente 3: Tendência estrutural (slope de regressão linear 2021–2025) ---
    def slope_linear(row):
        y = row.values.astype(float)
        if y.sum() == 0:
            return 0.0
        coef = np.polyfit(anos_c, y, 1)
        return float(coef[0])  # casos/ano

    tendencia = pivot[anos].apply(slope_linear, axis=1)

    # --- Componente 4: Severidade clínica (% casos graves ou com alarme em 2025) ---
    df_2025 = df_todos[df_todos['ANO'] == 2025].copy()
    df_2025['grave'] = pd.to_numeric(df_2025['CLASSI_FIN'], errors='coerce').isin([11, 12])
    sev = df_2025.groupby('NM_BAIRRO').agg(total=('grave', 'count'), graves=('grave', 'sum'))
    sev['pct_grave'] = sev['graves'] / sev['total']
    severidade = sev['pct_grave'].reindex(pivot.index).fillna(0)

    # --- Normalização min-max 0→1 para cada componente ---
    def norm(s):
        mn, mx = s.min(), s.max()
        if mx == mn:
            return pd.Series(0.5, index=s.index)
        return (s - mn) / (mx - mn)

    score = (
        0.30 * norm(carga)      +
        0.35 * norm(anomalia)   +
        0.20 * norm(tendencia)  +
        0.15 * norm(severidade)
    ) * 100

    score_df = pd.DataFrame({
        'Bairro':        pivot.index,
        'Casos 2025':    carga.values.astype(int),
        'Anomalia (σ)':  anomalia.round(2).values,
        'Tendência':     tendencia.round(1).values,
        'Graves (%)':    (severidade * 100).round(1).values,
        'Score':         score.round(1).values,
    })

    score_df['Risco'] = score_df['Score'].apply(
        lambda v: 'Baixo' if v < 25 else 'Moderado' if v < 50 else 'Alto' if v < 75 else 'Crítico'
    )

    return score_df


with st.spinner('Sincronizando microdados e mapas locais...'):
    geojson_bairros = carregar_geojson_bairros()
    try:
        df_todos = carregar_todos_dados()
        df_completo = df_todos[df_todos['ANO'] == 2025].copy()
        df_score = calcular_score_risco(df_todos)
        carregado_com_sucesso = True
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        carregado_com_sucesso = False

if carregado_com_sucesso and not df_completo.empty:

    total_casos = len(df_completo)
    bairro_critico = df_completo['NM_BAIRRO'].value_counts().index[0]

    aba_geral, aba_analitica = st.tabs(["🟢 Visão Geral da Cidade", "📍 Mapa e Análise por Bairro"])

    with aba_geral:
        st.subheader("Cenário Epidemiológico: Recife 2025")

        col1, col2 = st.columns(2)
        col1.metric("Total de Notificações (2025)", f"{total_casos:,}")
        col2.metric("Epicentro (Bairro com mais casos)", bairro_critico)

        st.divider()

        st.markdown("### Histórico de Casos por Semana Epidemiológica (2021–2025)")

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
        )
        fig_area.update_layout(
            xaxis=dict(dtick=1), margin=dict(t=10),
            legend=dict(title='Ano', orientation='h', y=1.05),
        )
        st.plotly_chart(fig_area, use_container_width=True)

    with aba_analitica:
        st.subheader("Inteligência Geográfica dos Bairros")

        col_mapa, col_rank = st.columns([1.6, 1])

        with col_mapa:
            st.markdown("**Score de Risco por Bairro**")
            st.caption(
                "Score 0–100: carga atual 2025 (30%) · anomalia histórica Z-score vs 2021–2024 (35%) · "
                "tendência de longo prazo por regressão linear (20%) · % casos graves/alarme (15%)."
            )
            if geojson_bairros:
                fig_mapa = px.choropleth_mapbox(
                    df_score, geojson=geojson_bairros,
                    locations='Bairro', featureidkey='properties.EBAIRRNOME',
                    color='Risco',
                    color_discrete_map=_COR_RISCO,
                    category_orders={'Risco': ['Baixo', 'Moderado', 'Alto', 'Crítico']},
                    mapbox_style="carto-positron", zoom=10.5,
                    center={"lat": -8.058, "lon": -34.91},
                    opacity=0.75, hover_name='Bairro',
                    hover_data={
                        'Score': True,
                        'Casos 2025': True,
                        'Anomalia (σ)': True,
                        'Tendência': True,
                        'Graves (%)': True,
                        'Risco': False,
                    },
                )
                fig_mapa.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
                st.plotly_chart(fig_mapa, use_container_width=True)
            else:
                st.warning("Arquivo 'maparecife.geojson' não encontrado.")

        with col_rank:
            ano_rank = st.selectbox(
                "Ano:",
                ["Todos os Anos", 2021, 2022, 2023, 2024, 2025],
                index=0,
                key="sel_rank",
            )
            df_rank_base = df_todos if ano_rank == "Todos os Anos" else df_todos[df_todos['ANO'] == ano_rank]
            df_bairros = df_rank_base['NM_BAIRRO'].value_counts().reset_index()
            df_bairros.columns = ['Bairro', 'Notificações']

            st.markdown(f"**Top 10 Bairros — {ano_rank}**")
            fig_rank = px.bar(
                df_bairros.head(10).sort_values('Notificações', ascending=True),
                x='Notificações', y='Bairro', orientation='h',
                color_discrete_sequence=["#ff7f0e"],
            )
            fig_rank.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=400)
            st.plotly_chart(fig_rank, use_container_width=True)

        st.divider()
        col_selecao, col_gravidade = st.columns([1.5, 1])

        with col_selecao:
            st.markdown("**Análise Individual por Bairro**")
            todos_bairros = sorted(df_todos['NM_BAIRRO'].unique())
            escolha = st.selectbox("Selecione um bairro para ver o histórico:", todos_bairros)

            historico_bairro = (
                df_todos[df_todos['NM_BAIRRO'] == escolha]
                .groupby('ANO').size().reset_index(name='Casos')
            )
            historico_bairro['ANO'] = historico_bairro['ANO'].astype(str)
            fig_individual = px.bar(
                historico_bairro, x='ANO', y='Casos',
                color_discrete_sequence=["#1f77b4"],
            )
            fig_individual.update_layout(height=300)
            st.plotly_chart(fig_individual, use_container_width=True)

        with col_gravidade:
            ano_grav = st.selectbox(
                "Ano (gravidade):",
                ["Todos os Anos", 2021, 2022, 2023, 2024, 2025],
                index=5,
                key="sel_gravidade",
            )
            st.markdown(f"**Gravidade das Notificações — {ano_grav}**")
            df_grav_base = df_todos if ano_grav == "Todos os Anos" else df_todos[df_todos['ANO'] == ano_grav]
            if 'CLASSI_FIN' in df_grav_base.columns:
                classi = pd.to_numeric(df_grav_base['CLASSI_FIN'], errors='coerce')
                labels = classi.map(_MAPA_CLASSI).fillna('Em Investigação')
                resumo_gravidade = labels.value_counts().reset_index()
                resumo_gravidade.columns = ['Classificação', 'Total']
                resumo_gravidade = resumo_gravidade.sort_values('Total', ascending=False)

                fig_gravidade = px.bar(
                    resumo_gravidade,
                    x='Total', y='Classificação', orientation='h',
                    color='Classificação',
                    color_discrete_map={
                        'Dengue Grave':    '#d62728',
                        'Dengue c/ Alarme': '#ff7f0e',
                        'Dengue':          '#e15759',
                        'Chikungunya':     '#9467bd',
                        'Inconclusivo':    '#8c564b',
                        'Descartado':      '#7f7f7f',
                        'Em Investigação': '#bcbd22',
                    },
                    labels={'Total': 'Notificações', 'Classificação': ''},
                )
                fig_gravidade.update_layout(
                    margin=dict(t=10, b=0, l=0, r=10),
                    height=300,
                    yaxis=dict(autorange='reversed'),
                    showlegend=False,
                )
                st.plotly_chart(fig_gravidade, use_container_width=True)

else:
    st.info("Certifique-se de que os arquivos CSV de cada ano e 'maparecife.geojson' estão na pasta do projeto.")
