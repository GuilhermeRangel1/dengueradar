import streamlit as st
import pandas as pd
import plotly.express as px
import json
import unicodedata


st.set_page_config(page_title="DengueRadar | Recife 2025", layout="wide", page_icon="🦟")
st.title("🦟 DengueRadar: Monitoramento Recife")
st.caption("📌 Fonte: Microdados Oficiais (SINAN/Prefeitura do Recife) | Ano: 2025")

@st.cache_data
def carregar_geojson_bairros():
    try:
        with open('maparecife.geojson', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo 'maparecife.geojson': {e}")
        return None

@st.cache_data
def carregar_dados_2025():
    df = pd.read_csv('dados_2025.csv', sep=',', encoding='latin-1', on_bad_lines='skip')
    
    df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
    
    df['Semana_Epi'] = df['SEM_NOT'].astype(str).str[-2:].astype(int)
    
    if 'NM_BAIRRO' in df.columns:
        df['NM_BAIRRO'] = df['NM_BAIRRO'].fillna('NAO INFORMADO').astype(str)
        
        def limpar_texto(txt):
            txt = txt.strip().upper()
            return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('utf-8')
        
        df['NM_BAIRRO'] = df['NM_BAIRRO'].apply(limpar_texto)
        
    return df

with st.spinner('Sincronizando microdados e mapas locais...'):
    geojson_bairros = carregar_geojson_bairros()
    try:
        df_completo = carregar_dados_2025()
        carregado_com_sucesso = True
    except Exception as e:
        st.error(f"Erro ao carregar 'dados_2025.csv': {e}")
        carregado_com_sucesso = False

if carregado_com_sucesso and not df_completo.empty:
    
    total_casos = len(df_completo)
    bairro_critico = df_completo['NM_BAIRRO'].value_counts().index[0]
    
    aba_geral, aba_analitica = st.tabs(["🟢 Visão Geral da Cidade", "📍 Mapa e Análise por Bairro"])
    
    with aba_geral:
        st.subheader("Cenário Epidemiológico: Recife 2025")
        
        col1, col2 = st.columns(2)
        col1.metric("Total de Notificações", f"{total_casos:,}")
        col2.metric("Epicentro (Bairro com mais casos)", bairro_critico)
        
        st.divider()
        
        st.markdown("### Curva de Contágio Municipal (2025)")
        casos_por_semana = df_completo.groupby('Semana_Epi').size().reset_index(name='Casos')
        casos_por_semana = casos_por_semana[casos_por_semana['Semana_Epi'] <= 52] 

        fig_curva = px.area(
            casos_por_semana, x='Semana_Epi', y='Casos',
            labels={'Semana_Epi': 'Semana Epidemiológica', 'Casos': 'Notificações'},
            color_discrete_sequence=["#FF4B4B"], markers=True
        )
        fig_curva.update_layout(xaxis=dict(dtick=1), margin=dict(t=10))
        st.plotly_chart(fig_curva, use_container_width=True)

    with aba_analitica:
        st.subheader("Inteligência Geográfica dos Bairros")
        
        df_bairros = df_completo['NM_BAIRRO'].value_counts().reset_index()
        df_bairros.columns = ['Bairro', 'Notificações']
        
        col_mapa, col_rank = st.columns([1.6, 1])
        
        with col_mapa:
            st.markdown("**Distribuição Espacial (Mapa de Calor)**")
            if geojson_bairros:
                fig_mapa = px.choropleth_mapbox(
                    df_bairros,
                    geojson=geojson_bairros,
                    locations='Bairro',
                    featureidkey='properties.EBAIRRNOME', 
                    color='Notificações',
                    color_continuous_scale="Reds",
                    mapbox_style="carto-positron",
                    zoom=10.5,
                    center={"lat": -8.058, "lon": -34.91},
                    opacity=0.7,
                    hover_name='Bairro'
                )
                fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_mapa, use_container_width=True)
            else:
                st.warning("Arquivo 'maparecife.geojson' não encontrado. O mapa não pode ser exibido.")

        with col_rank:
            st.markdown("**Top 10 Bairros Críticos**")
            fig_rank = px.bar(
                df_bairros.head(10).sort_values('Notificações', ascending=True), 
                x='Notificações', y='Bairro', orientation='h',
                color_discrete_sequence=["#ff7f0e"]
            )
            fig_rank.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=400)
            st.plotly_chart(fig_rank, use_container_width=True)
            
        st.divider()
        col_selecao, col_pie = st.columns([1.5, 1])
        
        with col_selecao:
            st.markdown("**Análise Individual por Bairro**")
            lista_bairros = sorted(df_bairros['Bairro'].unique())
            escolha = st.selectbox("Selecione um bairro para ver o histórico:", lista_bairros)
            
            df_selecionado = df_completo[df_completo['NM_BAIRRO'] == escolha]
            historico_bairro = df_selecionado.groupby('Semana_Epi').size().reset_index(name='Casos')
            
            fig_individual = px.bar(historico_bairro, x='Semana_Epi', y='Casos', color_discrete_sequence=["#1f77b4"])
            fig_individual.update_layout(xaxis=dict(dtick=1), height=300)
            st.plotly_chart(fig_individual, use_container_width=True)
            
        with col_pie:
            st.markdown("**Gravidade das Notificações**")
            if 'CLASSI_FIN' in df_completo.columns:
                df_completo['CLASSI_FIN'] = df_completo['CLASSI_FIN'].fillna('Em Investigação')
                resumo_gravidade = df_completo['CLASSI_FIN'].value_counts().reset_index()
                resumo_gravidade.columns = ['Classificação', 'Total']
                
                fig_pie = px.pie(resumo_gravidade, values='Total', names='Classificação', hole=0.4)
                fig_pie.update_layout(margin=dict(t=0, b=0), height=300)
                st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("Certifique-se de que os arquivos 'dados_2025.csv' e 'maparecife.geojson' estão na pasta do projeto.")