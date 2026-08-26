import os 
import wntr
import torch
import pandas as pd 
import networkx as nx
from pathlib import Path
from torch_geometric.data import Data

from data_use import (
    calcular_residuo, normalizar_residuo, taxa_exceedance
)

from data_access import (
    leak_info
)

def process_scenario_data(item, list_nodes, janela_dias):
    list_data = []

    leak_intervals = {}
    earliest_start = float('inf')
    if len(item['leaks']) > 0:
        for leak in item['leaks']:
            start, end, peak = leak_info(item['path'], leak)
            leak_intervals[leak] = (start, end)

            # guarda o menor start de todos
            if start < earliest_start:
                earliest_start = start

    # quantos instantes tem?
    ex_df = pd.read_csv(os.path.join(item['path'], 'Pressures', f'Node_{list_nodes[0]}.csv'))
    total_steps = len(ex_df)

    # normalização por nó
    # calc and norm toda a série de um nó uma única vez
    # resultado fica salvo em dfs_nodes
    dfs_nodes = {}
    for node in list_nodes:
        df_node = calcular_residuo(node, item['pressures'], janela_dias)

        if len(item['leaks']) > 0:
            df_node = normalizar_residuo(df_node, earliest_start)
        else:
            df_node = normalizar_residuo(df_node, start=janela_dias * 48)
        
        dfs_nodes[node] = df_node

    return dfs_nodes, leak_intervals, total_steps