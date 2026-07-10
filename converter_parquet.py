# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 16:41:14 2026

@author: rafae
"""

import pandas as pd

df = pd.read_csv("dados/tabnet_10anos.csv", encoding="utf-8-sig")
df.to_parquet("dados/tabnet_10anos.parquet", index=False)
print("Parquet salvo")
print(f"Tamanho do DataFrame: {df.shape}")