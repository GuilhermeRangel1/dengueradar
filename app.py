import streamlit as st
from extrator import buscar_dados_dengue

st.set_page_config(page_title="Monitoramento Dengue Recife", layout="wide")

st.title("🦟 Painel de Vigilância - Dengue Recife")
st.markdown("Monitoramento preditivo e alertas de surto.")

@st.cache_data(ttl=86400)
def carregar_dados():
    return buscar_dados_dengue()

df = carregar_dados()

st.subheader("🚨 Alertas Automáticos")
limite_critico = 300 

bairros_criticos = df[df['Incidencia_100k'] >= limite_critico]

if not bairros_criticos.empty:
    for index, row in bairros_criticos.iterrows():
        st.error(f"URGENTE: O bairro **{row['Bairro']}** ultrapassou o limite! Incidência atual: {row['Incidencia_100k']:.1f} / 100k hab.")
else:
    st.success("Nenhum bairro em estado crítico nesta semana.")

st.subheader("📊 Visão Geral por Bairro")

col1, col2 = st.columns(2)

with col1:
    st.dataframe(df.style.highlight_max(axis=0, color='red'))

with col2:
    st.bar_chart(data=df, x='Bairro', y='Incidencia_100k', color='#ff4b4b')