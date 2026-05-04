import requests
import pandas as pd
from datetime import datetime

def buscar_dados_dengue_elaborado(geocode="2611606"):
    hoje = datetime.now()
    ano_atual = hoje.year
    ano_passado = ano_atual - 1
    semana_atual = hoje.isocalendar()[1]
    
    url = "https://info.dengue.mat.br/api/alertcity"
    
    parametros = {
        "geocode": geocode,
        "disease": "dengue",
        "format": "json",
        "ew_start": 1,
        "ey_start": ano_passado, 
        "ew_end": semana_atual,
        "ey_end": ano_atual
    }
    
    try:
        resposta = requests.get(url, params=parametros, timeout=10) 
        resposta.raise_for_status()
        
        dados_json = resposta.json()
        df = pd.DataFrame(dados_json)
        
        if df.empty:
            return pd.DataFrame()
            
        colunas_uteis = ['data_iniSE', 'SE', 'casos', 'casos_est', 'nivel', 'tempmin', 'tempmax']
        df = df[[c for c in colunas_uteis if c in df.columns]]
        
        df['data_iniSE'] = pd.to_datetime(df['data_iniSE'], unit='ms', errors='coerce')
        df = df.dropna(subset=['data_iniSE'])
        
        df['Ano'] = df['data_iniSE'].dt.year
        df['Semana_Epi'] = df['SE'].astype(str).str[-2:].astype(int)
        
        df = df.sort_values(['Ano', 'Semana_Epi']).reset_index(drop=True)
        
        df['Media_Movel_4S'] = df['casos'].rolling(window=4, min_periods=1).mean().round(1)
        
        df['Variacao_Semanal_Pct'] = df['casos'].pct_change() * 100
        df['Variacao_Semanal_Pct'] = df['Variacao_Semanal_Pct'].fillna(0).round(1)
            
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Erro de rede ou API: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro no processamento de dados: {e}")
        return pd.DataFrame()