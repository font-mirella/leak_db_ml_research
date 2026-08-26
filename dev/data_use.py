import os 
import pandas as pd 
import wntr 
import networkx as nx
from pathlib import Path

# função de normalização de resíduo com base no desvio-padrão
def normalizar_residuo(df, start):
    baseline = df[df.index < start]['error_movel']

    mean_baseline = baseline.mean()
    std_baseline = baseline.std()

    df['error_normalizado'] = (df['error_movel'] - mean_baseline) / (std_baseline + 1e-8)
    return df

# função de conferência de excesso de erro em unidades de desvio padrão
def taxa_exceedance(df, start, end, limiar=3):
    dentro = df[(df.index >= start) & (df.index <= end)]
    fora = df[(df.index < start) | (df.index > end)]

    pct_dentro = (dentro['error_normalizado'].abs() > limiar).mean() * 100
    pct_fora = (fora['error_normalizado'].abs() > limiar).mean() * 100

    return pct_dentro, pct_fora

# função de cálculo de excesso de pressão por média móvel
def calcular_residuo(node, pressures_path,  janela_dias):
    caminho = os.path.join(pressures_path, f'Node_{node}.csv')
    df = pd.read_csv(caminho)
    df['momento'] = df.index % 48

    esperado_movel = pd.Series(index=df.index, dtype=float) 

    for h in range(48):
        idx_h = df.index[df['momento'] == h] # lista de idx de momentos de mesmo mod 48
        serie_h = df.loc[idx_h, 'Value'] # lista de valores de pressão de cada idx_h
        media_movel_h = serie_h.rolling(window=janela_dias, min_periods=3).mean()
        esperado_movel.loc[idx_h] = media_movel_h.values # pega resultado de media_movel e coloca na série grande em cada posição idx_h

    df['esperado_movel'] = esperado_movel
    df['error_movel'] = df['Value'] - df['esperado_movel']

    df['error_movel'] = df['error_movel'].fillna(0)

    return df

# função que monta dict com TODOS os nós de uma rede rotulados pela distância até o nó de vazamento
def nodes_distance(item): 
    wn = wntr.network.WaterNetworkModel(item['inp'])
    G = wn.to_graph().to_undirected()

    nodes = {}
    for node in wn.junction_name_list: 
        try: 
            distance = nx.shortest_path_length(G, source=str(item['leak']), target=str(node))
        except nx.NetworkXNoPath:
            print("Sem caminho até:", node)
            continue
        nodes[node] = f'{node}: Distância {distance}'
        
    return nodes