# 🦟 DengueRadar — Monitoramento Epidemiológico em Recife

> Projeto desenvolvido para a disciplina de **Projetos 5**.

**🌐 Aplicação em Produção:** [https://dengueradar.streamlit.app/](https://dengueradar.streamlit.app/)  
**📋 Organização do Time (Trello):** [https://trello.com/b/5Lbk8YrU/projeto-5](https://trello.com/b/5Lbk8YrU/projeto-5)  

---

## 📌 Sobre o Projeto
O **DengueRadar** é uma plataforma web para monitoramento, análise preditiva e suporte à tomada de decisão sobre o cenário epidemiológico da dengue na cidade do Recife. Utilizando os microdados oficiais do **SINAN (Sistema de Informação de Agravos de Notificação)** disponibilizados pela Prefeitura do Recife (2021–2025), a aplicação une inteligência geográfica, modelos matemáticos de sazonalidade e correlações climáticas para mapear os focos da doença e sugerir ações operacionais em tempo real.

---

## 🚀 Funcionalidades Principais

* **🟢 Visão Geral da Cidade:** Painel consolidado com a curva de contágio municipal iterativa, alternável entre Semana Epidemiológica e Mês. Identificação automática do epicentro atual e cálculo em tempo real do total de notificações do ano vigente.
* **📍 Central de Alertas e Inteligência Geográfica:** Mapa coroplético interativo integrado ao GeoJSON oficial de bairros do Recife. Calcula dinamicamente um **Score de Risco Algorítmico (Baixo, Moderado, Alto e Crítico)** baseado em 4 pilares: *carga acumulada, anomalia estatística ($\sigma$), tendência linear e severidade clínica* (% de casos graves).
* **📋 Insights de Gestão Automatizados:** Painel que gera recomendações automáticas para os gestores públicos de saúde ao selecionar um bairro, divididas em:
  * **UBS:** Alertas sobre capacidade de triagem, leitos de retaguarda e insumos venosos.
  * **Operacional:** Dimensionamento de força-tarefa (estimativa de agentes de endemias necessários) e bloqueio focal com fumacê.
  * **Ambiental:** Gatilhos para ações da Emlurb (limpeza de canais, remoção de pontos críticos de lixo).
* **🔮 Modelagem Preditiva Avançada:** Regressão Linear múltipla enriquecida com componentes harmônicos sazonais ($\sin$/$\cos$) treinada com o histórico de 2021 a 2025 para projetar os próximos 6 meses de contágio. Inclui aba de transparência com métricas de *backtest* de validação ($R^2$, MAE, RMSE) e intervalo de confiança de $\pm10\%$.
* **🌧️ Clima e Correlação Ambiental:** Integração via API histórica com o modelo de reanálise ERA5 (**Open-Meteo**) para cruzar notificações com Precipitação (mm), Temperatura Média (°C) e Umidade Relativa (%). Permite aplicar uma defasagem temporal (*lag*) de até 4 meses para analisar estatisticamente o ciclo biológico do mosquito *Aedes aegypti*.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Interface Web e Dashboard:** Streamlit
* **Manipulação e Análise de Dados:** Pandas, NumPy
* **Visualização Científica e Mapas:** Plotly Express, Plotly Graph Objects (Choroplethmapbox)
* **Machine Learning / Regressão:** Scikit-Learn (`LinearRegression`)
* **Consumo de APIs / Requisições:** Requests

---

## 📂 Estrutura de Arquivos Necessária

Para que a aplicação rode localmente, certifique-se de que a estrutura de dados está organizada da seguinte forma:

```text
├── app.py                  # Arquivo principal do Streamlit
├── requirements.txt        # Dependências do projeto
└── dados/
    ├── maparecife.geojson  # Malha geográfica dos bairros de Recife
    ├── dados_2021.csv      # Microdados SINAN 2021 (separador ';')
    ├── dados_2022.csv      # Microdados SINAN 2022 (separador ';')
    ├── dados_2023.csv      # Microdados SINAN 2023 (separador ';')
    ├── dados_2024.csv      # Microdados SINAN 2024 (separador ';')
    └── dados_2025.csv      # Microdados SINAN 2025 (separador ',')

```
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
