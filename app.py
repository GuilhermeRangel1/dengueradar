import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import unicodedata
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

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
    2025: None,  # ISO com timestamp — pandas infere automaticamente
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
def calcular_score_risco(df_todos):
    anos = [2021, 2022, 2023, 2024, 2025]
    anos_arr = np.array(anos, dtype=float)
    anos_c = anos_arr - anos_arr.mean() 

    pivot = (
        df_todos.groupby(['NM_BAIRRO', 'ANO'])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=anos, fill_value=0)
    )

    carga = pivot[2025].astype(float)
    hist = pivot[[2021, 2022, 2023, 2024]].astype(float)
    hist_mean = hist.mean(axis=1)
    hist_std  = hist.std(axis=1)
    hist_std = hist_std.where(hist_std > 0, 1.0)
    anomalia = ((pivot[2025] - hist_mean) / hist_std).clip(-3, 5)

    def slope_linear(row):
        y = row.values.astype(float)
        if y.sum() == 0:
            return 0.0
        coef = np.polyfit(anos_c, y, 1)
        return float(coef[0]) 

    tendencia = pivot[anos].apply(slope_linear, axis=1)

    df_2025 = df_todos[df_todos['ANO'] == 2025].copy()
    df_2025['grave'] = pd.to_numeric(df_2025['CLASSI_FIN'], errors='coerce').isin([11, 12])
    sev = df_2025.groupby('NM_BAIRRO').agg(total=('grave', 'count'), graves=('grave', 'sum'))
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
        'IC_inf':   np.maximum(y_fut - 1.96 * resid_std, 0),
        'IC_sup':   y_fut + 1.96 * resid_std,
    })

with st.spinner('Sincronizando microdados e mapas locais...'):
    geojson_bairros = carregar_geojson_bairros()
    try:
        df_todos = carregar_todos_dados()
        df_completo = df_todos[df_todos['ANO'] == 2025].copy() if not df_todos.empty else pd.DataFrame()
        df_score = calcular_score_risco(df_todos) if not df_todos.empty else pd.DataFrame()
        carregado_com_sucesso = not df_todos.empty
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        carregado_com_sucesso = False

if carregado_com_sucesso and not df_completo.empty:

    total_casos = len(df_completo)
    bairro_critico = df_completo['NM_BAIRRO'].value_counts().index[0]

    aba_geral, aba_analitica, aba_tecnica, aba_previsao = st.tabs([
        "🟢 Visão Geral da Cidade",
        "📍 Mapa e Análise por Bairro",
        "🔍 Estudo Técnico & Insights",
        "🔮 Previsão",
    ])

    with aba_geral:
        st.subheader("Cenário Epidemiológico: Recife 2025")

        col1, col2 = st.columns(2)
        col1.metric("Total de Notificações (2025)", f"{total_casos:,}")
        col2.metric("Epicentro (Bairro com mais casos)", bairro_critico)

        st.divider()

        col_titulo_hist, col_filtro_hist = st.columns([3, 1])
        with col_titulo_hist:
            st.markdown("### Histórico de Casos (2021–2025)")
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
            )
            fig_area.update_layout(
                xaxis=dict(dtick=1), margin=dict(t=10),
                legend=dict(title='Ano', orientation='h', y=1.05),
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

            fig_area = px.area(
                casos_historico,
                x='Mês', y='Casos', color='ANO',
                category_orders={'Mês': list(_MESES.values())},
                labels={'Mês': 'Mês', 'Casos': 'Notificações', 'ANO': 'Ano'},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_area.update_layout(
                margin=dict(t=10),
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
                st.warning("Arquivo 'maparecife.geojson' não encontrado na pasta dados.")

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
            text='Casos',
        )
        fig_individual.update_traces(textposition='outside', textfont_size=12)
        fig_individual.update_layout(height=320, yaxis=dict(range=[0, historico_bairro['Casos'].max() * 1.2]))
        st.plotly_chart(fig_individual, use_container_width=True)

    with aba_tecnica:
        st.subheader("Estudo Técnico e Monitoramento Ativo")
        
        st.markdown("**📢 Central de Notificações e Alertas**")
        
        bairros_criticos = df_score[df_score['Risco'] == 'Crítico']
        bairros_alto = df_score[df_score['Risco'] == 'Alto']
        
        if not bairros_criticos.empty:
            st.error(f"🚨 **ALERTA EPIDEMIOLÓGICO:** {len(bairros_criticos)} bairros encontram-se em **Nível Crítico** de risco. Ação imediata recomendada.")
        elif not bairros_alto.empty:
            st.warning(f"⚠️ **ATENÇÃO:** O sistema detectou {len(bairros_alto)} bairros em **Risco Alto**. Recomenda-se monitoramento diário da curva.")
        else:
            st.success("✅ **MONITORAMENTO:** Nenhum bairro em nível crítico extremo no momento. Cenário sob controle.")

        c_notif1, c_notif2, c_notif3, c_notif4 = st.columns(4)
        c_notif1.metric("🔴 Risco Crítico", f"{len(bairros_criticos)} Bairros")
        c_notif2.metric("🟠 Risco Alto", f"{len(bairros_alto)} Bairros")
        c_notif3.metric("🟡 Risco Moderado", f"{len(df_score[df_score['Risco'] == 'Moderado'])} Bairros")
        c_notif4.metric("🟢 Risco Baixo", f"{len(df_score[df_score['Risco'] == 'Baixo'])} Bairros")

        st.divider()

        st.markdown("**📈 Predições e Tendências Estruturais**")
        try:
            row_score = df_score[df_score['Bairro'] == bairro_critico].iloc[0]
            tendencia_epicentro = row_score['Tendência']
            sinal = "+" if tendencia_epicentro > 0 else ""
            tendencia_arredondada = int(round(tendencia_epicentro))
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Foco da Análise", bairro_critico)
            m2.metric("Score Algorítmico", f"{row_score['Score']:.1f} / 100")
            m3.metric("Projeção do Modelo", f"{sinal}{tendencia_arredondada}", "Novos Casos Projetados", delta_color="inverse")
            
            st.info(f"**ANÁLISE PREDITIVA:** O cálculo de regressão linear da série histórica (2021-2025) aponta para o epicentro ({bairro_critico}) uma tendência de crescimento estrutural de **{sinal}{tendencia_arredondada} novos casos** por ano.")
        except:
            st.info("Predição não disponível para o bairro selecionado.")

        st.divider()

        st.markdown("### 📋 Insights de Gestão (Apoio à Tomada de Decisão)")
        col_st1, col_st2, col_st3 = st.columns(3)
        
        casos_epicentro = df_completo[df_completo['NM_BAIRRO'] == bairro_critico].shape[0]
        agentes_necessarios = max(1, casos_epicentro // 20) 
        
        col_st1.warning(f"**🏥 Pressão nas UBS:**\nEspera-se alta sobrecarga na rede de atenção básica de **{bairro_critico}**. É recomendável reforçar a triagem e direcionar insumos de hidratação para as unidades locais.")
        
        col_st2.error(f"**👷 Impacto Operacional:**\nPara conter o avanço neste epicentro, estima-se o deslocamento estratégico de **~{agentes_necessarios} agentes de endemias** para bloqueio de focos e eliminação de criadouros.")
        
        col_st3.info(f"**🦟 Gatilho Ambiental (Protocolo):**\nSolicitar à vigilância sanitária a vistoria de fatores exógenos em **{bairro_critico}**. Priorizar rotas com histórico de **canais a céu aberto, acúmulo de lixo irregular e intermitência hídrica**.")

    with aba_previsao:
        st.subheader("Previsão de Casos — Regressão Linear com Sazonalidade")
        st.caption(
            "Modelo: tendência linear + componente harmônico mensal (sin/cos). "
            "Treinado em 2021–2025 (completo). Métrica de qualidade: backtest treino 2021–2023 → teste 2024."
        )

        col_ctrl, _ = st.columns([1, 2])
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
                line=dict(color='#1f77b4', width=2),
                mode='lines',
            ))

            x_band = list(df_prev['Ano_Mes']) + list(df_prev['Ano_Mes'])[::-1]
            y_band = list(df_prev['IC_sup']) + list(df_prev['IC_inf'])[::-1]
            fig_prev.add_trace(go.Scatter(
                x=x_band, y=y_band,
                fill='toself',
                fillcolor='rgba(255,127,14,0.15)',
                line=dict(color='rgba(0,0,0,0)'),
                name='IC 95%',
            ))

            fig_prev.add_trace(go.Scatter(
                x=df_prev['Ano_Mes'], y=df_prev['Previsao'],
                name='Previsão (próximos 6 meses)',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                mode='lines+markers',
                marker=dict(size=7),
            ))

            fig_prev.update_layout(
                xaxis_title='Mês',
                yaxis_title='Notificações Mensais',
                yaxis=dict(rangemode='tozero'),
                legend=dict(orientation='h', y=1.08, x=0),
                margin=dict(t=10, b=0),
                height=420,
            )
            st.plotly_chart(fig_prev, use_container_width=True)

            with st.expander("📊 Ver backtest: modelo vs. real em 2024"):
                if resultado_bt[0] is not None:
                    _, _, _, m_bt, res_bt, treino_bt, teste_bt, y_pred_bt = resultado_bt
                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(
                        x=treino_bt['Ano_Mes'], y=treino_bt['Casos'],
                        name='Treino (2021–2023)', line=dict(color='#1f77b4', width=2),
                    ))
                    fig_bt.add_trace(go.Scatter(
                        x=teste_bt['Ano_Mes'], y=teste_bt['Casos'],
                        name='Real 2024', line=dict(color='#2ca02c', width=2),
                    ))
                    x_band_bt = list(teste_bt['Ano_Mes']) + list(teste_bt['Ano_Mes'])[::-1]
                    y_band_bt = (
                        list(y_pred_bt + 1.96 * res_bt)
                        + list(np.maximum(y_pred_bt - 1.96 * res_bt, 0))[::-1]
                    )
                    fig_bt.add_trace(go.Scatter(
                        x=x_band_bt, y=y_band_bt,
                        fill='toself', fillcolor='rgba(255,127,14,0.15)',
                        line=dict(color='rgba(0,0,0,0)'), name='IC 95%',
                    ))
                    fig_bt.add_trace(go.Scatter(
                        x=teste_bt['Ano_Mes'], y=y_pred_bt,
                        name='Previsto 2024',
                        line=dict(color='#ff7f0e', width=2, dash='dash'),
                        mode='lines+markers', marker=dict(size=7),
                    ))
                    fig_bt.update_layout(
                        xaxis_title='Mês', yaxis_title='Casos',
                        yaxis=dict(rangemode='tozero'),
                        legend=dict(orientation='h', y=1.12),
                        margin=dict(t=10), height=300,
                    )
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

else:
    st.info("Certifique-se de que a pasta 'dados/' contém os arquivos CSV e o GeoJSON.")