# DengueRadar - Monitoramento Epidemiológico em Recife

**Aplicação em produção:** [https://dengueradar.streamlit.app/](https://dengueradar.streamlit.app/)

**Organização do time:** [Trello](https://trello.com/b/5Lbk8YrU/projeto-5)

---

## Sobre o projeto

O **DengueRadar** é uma aplicação web em Streamlit para monitoramento, análise territorial e apoio à tomada de decisão sobre dengue na cidade do Recife. O painel combina microdados do SINAN, malha geográfica dos bairros, análise de risco, previsão sazonal e correlação climática.

O objetivo é transformar dados epidemiológicos em visualizações úteis para acompanhamento de casos, identificação de áreas prioritárias e apoio a ações de vigilância em saúde.

---

## Funcionalidades principais

- **Filtros globais:** recorte por ano, bairro foco e classificação do caso, com botão para limpar filtros.
- **Visão geral:** métricas consolidadas e série histórica por semana epidemiológica ou mês.
- **Mapa de risco:** mapa coroplético por bairro com destaque visual para o bairro escolhido no filtro global.
- **Ranking de prioridade de ação:** gráfico dos bairros com maior Score de Risco, considerando score, casos, tendência e gravidade.
- **Score de Risco:** indicador de 0 a 100 baseado em carga acumulada, anomalia histórica, tendência temporal e severidade clínica.
- **Insights de gestão:** recomendações operacionais para UBS, agentes de endemias e ações ambientais.
- **Previsão de casos:** regressão linear com componentes sazonais, backtest e indicador de confiabilidade.
- **Clima e correlação:** análise de precipitação, temperatura e umidade com defasagem temporal.
- **Sobre os dados:** aba de transparência com origem, limitações e orientação de interpretação.

---

## Como o Score de Risco funciona

O score é calculado por bairro e combina quatro dimensões:

- **Carga acumulada de casos (30%)**
- **Anomalia histórica (35%)**
- **Tendência temporal (20%)**
- **Severidade clínica (15%)**

Faixas de classificação:

- **Baixo:** abaixo de 25
- **Moderado:** de 25 a 49,9
- **Alto:** de 50 a 74,9
- **Crítico:** 75 ou mais

---

## Tecnologias

- Python 3
- Streamlit
- Pandas e NumPy
- Plotly Express e Plotly Graph Objects
- Scikit-learn
- Requests

---

## Estrutura do projeto

```text
app.py
requirements.txt
dados/
  maparecife.geojson
  clima_recife.csv
  dados_2021.csv
  dados_2022.csv
  dados_2023.csv
  dados_2024.csv
  dados_2025.csv
```

---

## Como rodar localmente

Crie e ative um ambiente virtual:

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

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute a aplicação:

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`.

---

## Observações

Notificações não são necessariamente casos confirmados. Os resultados dependem da qualidade do preenchimento dos dados e da atualização dos arquivos. As previsões devem ser interpretadas como apoio à decisão, não como valores definitivos.

---

## Integrantes

- Arthur Leal
- Beatriz Galindo
- Bruno Carvalho
- Guilheme Coutinho
- Guilherme Vinícius
- Igor Couto
- João Pedro Albuquerque
- William Souza
