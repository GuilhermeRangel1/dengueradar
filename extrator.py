import pandas as pd
import requests

def buscar_dados_dengue():
    
    dados_simulados = {
        'Bairro': ['Boa Viagem', 'Pina', 'Várzea', 'Casa Amarela'],
        'Casos_Ultima_Semana': [320, 150, 45, 510],
        'Populacao': [122922, 27422, 70453, 29112]
    }
    
    df = pd.DataFrame(dados_simulados)
    df['Incidencia_100k'] = (df['Casos_Ultima_Semana'] / df['Populacao']) * 100000
    
    return df