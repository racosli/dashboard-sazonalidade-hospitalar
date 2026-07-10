# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 18:07:03 2026

@author: rafae
"""

import re
import pandas as pd
import os

MESES_MAP = {
    "Janeiro":1,"Fevereiro":2,"Março":3,"Abril":4,"Maio":5,"Junho":6,
    "Julho":7,"Agosto":8,"Setembro":9,"Outubro":10,"Novembro":11,"Dezembro":12
}
MESES_CURTO = {
    1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
    7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"
}
CAPS_MAP = {
    "Cap 01":"Infeccioso/Parasitario","Cap 02":"Neoplasias",
    "Cap 03":"Sangue/Imunidade","Cap 04":"Endocrino/Metabolico",
    "Cap 05":"Mental/Comportamental","Cap 06":"Nervoso",
    "Cap 07":"Olho/Anexos","Cap 08":"Ouvido",
    "Cap 09":"Cardiovascular","Cap 10":"Respiratorio",
    "Cap 11":"Digestivo","Cap 12":"Pele/Subcutaneo",
    "Cap 13":"Osteomuscular","Cap 14":"Geniturinario",
    "Cap 15":"Materno/Perinatal","Cap 16":"Perinatal",
    "Cap 17":"Congenito","Cap 18":"Sintomas/Sinais",
    "Cap 19":"Lesoes/Traumas","Cap 20":"Causas Externas",
    "Cap 21":"Fatores de Saude"
}

def processar(caminho, ano_alvo):
    with open(caminho, "r", encoding="latin-1") as f:
        linhas = f.readlines()
    idx = next((i for i,l in enumerate(linhas) if "Cap 01" in l), None)
    if idx is None:
        return pd.DataFrame()
    cab = [c.strip('"').strip() for c in linhas[idx].strip().split(";")]
    rows = []
    for linha in linhas[idx+1:]:
        if not any(m in linha for m in MESES_MAP):
            continue
        p = linha.strip().split(";")
        per = p[0].strip('"').replace("..","").strip()
        match = re.match(r"(\w+)/(\d{4})", per)
        if not match:
            continue
        mn, ano = match.group(1), int(match.group(2))
        if ano != ano_alvo:
            continue
        mes = MESES_MAP.get(mn, 0)
        if mes == 0:
            continue
        for i, col in enumerate(cab[1:], 1):
            col = col.strip()
            if col == "Total" or col not in CAPS_MAP:
                continue
            if i >= len(p):
                continue
            val = p[i].strip()
            try:
                v = int(val.replace(".","").replace(",","")) if val != "-" else 0
            except:
                v = 0
            rows.append({
                "ano": ano, "mes": mes,
                "mes_nome": MESES_CURTO[mes],
                "capitulo": col,
                "grupo_cid": CAPS_MAP[col],
                "aih": v
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame()

todos = []
for ano in range(2016, 2027):
    cam = f"dados/{ano}.csv"
    if not os.path.exists(cam):
        print(f"  AVISO: {cam} nao encontrado")
        continue
    df = processar(cam, ano)
    if not df.empty:
        print(f"  {ano}: {df['mes'].nunique()} meses | {df['aih'].sum():,} AIH")
        todos.append(df)

if todos:
    df_final = pd.concat(todos, ignore_index=True)
    df_final.to_csv("dados/tabnet_10anos.csv", index=False, encoding="utf-8")
    print(f"\nSalvo: dados/tabnet_10anos.csv")
    print(f"Total: {len(df_final)} registros | {df_final['aih'].sum():,} AIH")
else:
    print("Nenhum arquivo encontrado em dados/")