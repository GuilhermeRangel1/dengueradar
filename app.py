import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from extrator import buscar_dados_dengue_elaborado

st.set_page_config(page_title="DengueRadar | Recife", layout="wide", page_icon="🦟")

st.title("🦟 DengueRadar")
st.caption("📌 Fonte dos Dados: InfoDengue (Fiocruz) | Município: Recife/PE (IBGE: 2611606)")

@st.cache_data(ttl=3600)
def carregar_dados():
    return buscar_dados_dengue_elaborado()

with st.spinner('Sincronizando com a base da Fiocruz...'):
    df_completo = carregar_dados()

if not df_completo.empty:
    ano_atual = df_completo['Ano'].max()
    df_ano_atual = df_completo[df_completo['Ano'] == ano_atual].copy()
    dados_ultima_semana = df_ano_atual.iloc[-1]
    
    aba_geral, aba_analitica = st.tabs(["🟢 Visão Geral", "📊 Visão Analítica"])
    
    with aba_geral:
        st.subheader(f"Status Atual: Semana {int(dados_ultima_semana['Semana_Epi'])} / {ano_atual}")
        
        col1, col2, col3 = st.columns(3)
        var_pct = dados_ultima_semana['Variacao_Semanal_Pct']
        
        with col1:
            st.metric(
                label="Casos Notificados (Semana)", 
                value=int(dados_ultima_semana['casos']), 
                delta=f"{var_pct}% vs Sem. Passada",
                delta_color="inverse"
            )
        with col2:
            st.metric(
                label="Tendência (Média Móvel 4S)", 
                value=int(dados_ultima_semana['Media_Movel_4S'])
            )
        with col3:
            st.metric(
                label="Nível de Alerta", 
                value=f"Nível {int(dados_ultima_semana['nivel'])}"
            )
            
        if var_pct > 25.0:
            st.error(f"🚨 **ALERTA:** Crescimento acelerado de {var_pct}% nos casos. Recomendada atenção nas ações de bloqueio.")
        elif var_pct > 0:
            st.warning("⚠️ **ATENÇÃO:** Curva de contágio apresenta tendência de alta.")
        else:
            st.success("✅ **ESTÁVEL:** Incidência da doença em estabilidade ou queda.")
            
        st.markdown("### Curva de Contágio Recente")
        
        fig_geral = px.area(
            df_ano_atual, 
            x='Semana_Epi', 
            y='casos',
            labels={'Semana_Epi': 'Semana Epidemiológica', 'casos': 'Número de Casos'},
            color_discrete_sequence=["#FF4B4B"]
        )
        fig_geral.update_layout(xaxis=dict(range=[1, 52], dtick=2), margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_geral, use_container_width=True)

    with aba_analitica:
        st.subheader("Inteligência Epidemiológica e Fatores de Risco")
        
        st.markdown("**1. Curva Sazonal: Comparativo Ano a Ano**")
        fig_analitica = px.line(
            df_completo, x='Semana_Epi', y='casos', color='Ano', markers=True,
            labels={'Semana_Epi': 'Semana Epidemiológica', 'casos': 'Casos Notificados'}
        )
        fig_analitica.update_layout(xaxis=dict(range=[1, 52], dtick=2), margin=dict(t=10)) 
        st.plotly_chart(fig_analitica, use_container_width=True)
        
        st.divider()
        
        st.markdown("**2. Análise de Subnotificação: Casos Confirmados vs. Estimados**")
        st.caption("Devido à latência inerente dos sistemas oficiais (ex: SINAN), a Fiocruz projeta o cenário real estimado para as últimas semanas.")
        
        fig_estimativa = px.line(
            df_ano_atual, x='Semana_Epi', y=['casos_est', 'casos'], markers=True,
            labels={'value': 'Quantidade de Casos', 'variable': 'Métrica', 'Semana_Epi': 'Semana'},
            color_discrete_map={'casos_est': '#d62728', 'casos': '#1f77b4'}
        )
        newnames = {'casos_est': 'Estimativa (Cenário Real)', 'casos': 'Notificados (Sistema Oficiais)'}
        fig_estimativa.for_each_trace(lambda t: t.update(name = newnames[t.name]))
        fig_estimativa.update_layout(xaxis=dict(range=[1, 52], dtick=2), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=10))
        st.plotly_chart(fig_estimativa, use_container_width=True)
        
        st.divider()
        
        col_risco, col_clima = st.columns(2)
        
        with col_risco:
            st.markdown("**3. Distribuição dos Níveis de Alerta (Ano Atual)**")
            contagem_niveis = df_ano_atual['nivel'].value_counts().reset_index()
            contagem_niveis.columns = ['Nível de Alerta', 'Semanas']
            
            cores_alerta = {1: '#2ca02c', 2: '#ff7f0e', 3: '#d62728', 4: '#8c564b'}
            fig_rosca = px.pie(contagem_niveis, values='Semanas', names='Nível de Alerta', hole=0.5, color='Nível de Alerta', color_discrete_map=cores_alerta)
            fig_rosca.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_rosca, use_container_width=True)
            
        with col_clima:
            st.markdown("**4. Impacto Climático: Casos vs. Temperatura**")
            
            fig_clima = go.Figure()
            fig_clima.add_trace(go.Bar(x=df_ano_atual['Semana_Epi'], y=df_ano_atual['casos'], name='Casos Notificados', marker_color='#1f77b4'))
            fig_clima.add_trace(go.Scatter(x=df_ano_atual['Semana_Epi'], y=df_ano_atual['tempmax'], name='Temp. Máxima (°C)', yaxis='y2', line=dict(color='#ff7f0e', width=3)))
            
            fig_clima.update_layout(
                xaxis=dict(range=[1, 52], dtick=4, title='Semana Epidemiológica'),
                yaxis=dict(title='Casos', side='left'),
                yaxis2=dict(title='Temperatura (°C)', side='right', overlaying='y', range=[20, 40]), 
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_clima, use_container_width=True)
        
        with st.expander("Visualizar e Exportar Base de Dados Bruta"):
            st.dataframe(df_completo.sort_values(by=['Ano', 'Semana_Epi'], ascending=False), use_container_width=True)
            csv = df_completo.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Baixar Base Completa (CSV)", data=csv, file_name=f"dengueradar_recife_historico.csv", mime="text/csv")
else:
    st.error("Falha ao comunicar com a API da Fiocruz. Tente novamente mais tarde.")