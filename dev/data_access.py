import os 
import pandas as pd 
import wntr 
import networkx as nx
from pathlib import Path

from data_use import (
    calcular_residuo, normalizar_residuo, taxa_exceedance
)

def get_all(intention): # test ou train?
    pasta_object = rf"C:\Users\Mirella Fontinelle\Leakage Research\data\object\{intention}"

    scenarios_dict = {}

    for scenario in os.listdir(pasta_object):
        scenario_path = os.path.join(pasta_object, scenario)
        n_scenario = int(scenario.split("-")[-1])

        if os.path.isdir(scenario_path): # é pasta?
            pressures_path = os.path.join(scenario_path, "Pressures")

            leaks = [] # como uma lista -> [31, 18] ou [31] ou []
            leaks_path = os.path.join(scenario_path, "Leaks")

            if os.path.exists(leaks_path):
                for file in os.listdir(leaks_path):
                    if file.endswith("_info.csv"):
                        leaks.append(int(file.split("_")[1]))

            inp_path = os.path.join(scenario_path, f"Hanoi_CMH_Scenario-{n_scenario}.inp")

            scenario_info = os.path.join(scenario_path, f"Scenario-{n_scenario}_info.csv")

            scenarios_dict[n_scenario] = {
                "n_scenario": n_scenario,
                "path": scenario_path,
                "inp": inp_path,
                "info": scenario_info,
                "leaks": leaks,
                "pressures": pressures_path
            }

    return scenarios_dict

# função de acesso ao arquivo Leak_x_info.csv para qualquer cenário
def leak_info(scenario_path, leak):    
    # pega info do vazamento
    leak_file = os.path.join(scenario_path, 'Leaks',  f"Leak_{leak}_info.csv")

    # lê arquivo csv
    df_leak_info = pd.read_csv(leak_file)

    # formatação
    df_leak_info.columns = df_leak_info.columns.str.strip()
    df_leak_info['Description'] = df_leak_info['Description'].str.strip()

    # index
    df_leak_info.set_index('Description', inplace=True)

    # extract 
    start = int(df_leak_info.loc['Leak Start', 'Value'])
    end = int(df_leak_info.loc['Leak End', 'Value'])
    peak = int(df_leak_info.loc['Peak Time', 'Value'])

    return start, end, peak

# função útil apenas para experimento 01
def load_scenario(scenario, item, janela_dias, limiar, load_nodes=None):
    # puxa start e end do vazamento
    start, end, peak = leak_info(item['path'], item['leak'])

    # mapeamento dos nós
    if load_nodes is None:
        nodes = {
            item['leak']: 'Nó Vazamento',
            item['neigh']: 'Nó Vizinho',
            item['far']: 'Nó Distante'
        }
    else: 
        nodes = load_nodes(item)

    # cálculo de comparações
    resultados = {}
    linhas = []
    for node in nodes:
        df_node = calcular_residuo(node, item['path'], 14)
        df_node = normalizar_residuo(df_node, start)
        resultados[node] = df_node

        # referenciais numéricos
        pct_dentro, pct_fora = taxa_exceedance(df_node, start, end, limiar)
        linhas.append({
            'Cenário': scenario,
            'Nó': nodes[node],
            '% |z|>3 dentro do leak': round(pct_dentro, 2),
            '% |z|>3 fora do leak': round(pct_fora, 2)
        })
        
    return resultados, nodes, start, end, peak, linhas