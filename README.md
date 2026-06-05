# 🦟 DengueRadar — Monitoramento de Dengue em Recife

Projeto desenvolvido para a disciplina de **Projetos 5**.

**🌐 Acesse a aplicação:** [https://dengueradar.streamlit.app/](https://dengueradar.streamlit.app/)  
**📋 Trello:** [https://trello.com/b/5Lbk8YrU/projeto-5](https://trello.com/b/5Lbk8YrU/projeto-5)  

---

## 📌 Sobre o Projeto
O DengueRadar é uma aplicação web desenvolvida em Streamlit para monitoramento epidemiológico de dengue em Recife, utilizando microdados oficiais do SINAN / Prefeitura do Recife (2021–2025). A aplicação oferece inteligência geográfica, previsões de aprendizado de máquina e análise de correlações climáticas.

---

## 🚀 Funcionalidades

* **Visão Geral da Cidade (Gráficos Dinâmicos):** Curva de contágio municipal iterativa, alternável entre Semana Epidemiológica e Mês, com exibição em tempo real do total de notificações e identificação automática do epicentro.
* **Mapa e Análise por Bairro:** Núcleo analítico integrado ao GeoJSON oficial de Recife e ao Score de Risco Algorítmico (Baixo, Moderado, Alto e Crítico) baseado em carga, anomalia, tendência e severidade. Inclui painéis dinâmicos de ação operacional (alertas de UBS, força-tarefa de agentes e gatilho ambiental) e ranking dos bairros mais críticos.
* **Sistema de Predição:** Regressão linear enriquecida com componente harmônico sazonal (seno/cosseno) para prever a curva de contágio dos próximos 6 meses, incluindo backtest (2021-2023 vs 2024), métricas de desempenho (R², MAE, RMSE) e margem de segurança de ±10%.
* **Clima e Correlação:** Cruzamento de casos notificados com variáveis meteorológicas (Precipitação, Temperatura Média e Umidade Relativa) via API Open-Meteo. Permite aplicar defasagem temporal (lag) de 0 a 4 meses para investigar a correlação estatística com o ciclo biológico do mosquito.

---

## 💻 Como rodar o projeto

**1. Crie e ative o ambiente virtual**

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

**2. Instale as dependências**

```bash
pip install -r requirements.txt
```

**3. Execute a aplicação**

```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`.

---

## Integrantes

- Arthur Leal
- Beatriz Galindo
- Bruno Carvalho
- Guilheme Coutinho
- Guilherme Vinícius
- Igor Couto
- João Pedro ALbuquerque
- William Souza
