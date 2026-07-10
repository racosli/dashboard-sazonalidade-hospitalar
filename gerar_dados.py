# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 18:29:42 2026

@author: rafae
"""

import pandas as pd
import numpy as np
import os

os.makedirs("dados", exist_ok=True)
np.random.seed(42)

regioes = {
    "Norte":        ["AC","AM","PA"],
    "Nordeste":     ["BA","CE","PE"],
    "Centro-Oeste": ["DF","GO","MT"],
    "Sudeste":      ["SP","MG","RJ"],
    "Sul":          ["RS","SC","PR"]
}

cids = {
    "J18":"Respiratorio","J44":"Respiratorio",
    "I10":"Cardiovascular","I50":"Cardiovascular",
    "E11":"Endocrino","E14":"Endocrino",
    "K29":"Digestivo","K57":"Digestivo",
    "A90":"Infeccioso","B34":"Infeccioso",
    "F32":"Mental","C50":"Neoplasia",
    "S72":"Trauma","N18":"Geniturinario",
    "O80":"Materno"
}

sazonalidade = {
    "Sul":          {6:1.9, 7:2.1, 8:1.8, 12:1.3, 1:1.4},
    "Norte":        {1:1.7, 2:1.8, 3:1.6, 11:1.4, 12:1.5},
    "Nordeste":     {3:1.6, 4:1.7, 5:1.5, 6:1.4},
    "Sudeste":      {1:1.4, 2:1.3, 7:1.3, 8:1.4},
    "Centro-Oeste": {3:1.5, 4:1.4, 10:1.3},
}

rows = []
for regiao, ufs in regioes.items():
    for mes in range(1, 13):
        for cid, grupo in cids.items():
            peso = sazonalidade.get(regiao, {}).get(mes, 1.0)
            if grupo == "Respiratorio" and regiao == "Sul" and mes in [6,7,8]:
                peso *= 1.5
            n = max(10, int(np.random.normal(80, 15) * peso))
            for _ in range(n):
                rows.append({
                    "regiao":         regiao,
                    "uf":             np.random.choice(ufs),
                    "mes":            mes,
                    "ano":            2023,
                    "cid":            cid,
                    "grupo_cid":      grupo,
                    "idade":          max(1, int(np.random.normal(55, 20))),
                    "sexo":           np.random.choice(["M","F"]),
                    "obito":          int(np.random.random() < 0.04),
                    "dias_internado": max(1, int(np.random.exponential(5))),
                    "valor_total":    round(np.random.exponential(2000), 2)
                })

df = pd.DataFrame(rows)
df.to_csv("dados/internacoes_2023.csv", index=False, encoding="utf-8")
print(f"Dataset gerado: {len(df)} registros")
print(df["grupo_cid"].value_counts().to_string())