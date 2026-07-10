import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Sazonalidade Hospitalar",
    page_icon="🏥", layout="wide"
)

st.title("🏥 Análise Avançada de Sazonalidade Hospitalar")
st.caption("SIH/DATASUS Brasil 2016–2026 · 129 milhões de internações · 21 grupos CID-10")
st.markdown("---")

ORDER_MESES = ["Jan","Fev","Mar","Abr","Mai","Jun",
               "Jul","Ago","Set","Out","Nov","Dez"]
MESES_N = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
           7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

@st.cache_data
def carregar():
    df = pd.read_parquet("dados/tabnet_10anos.parquet")
    df["ano"] = df["ano"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["aih"] = pd.to_numeric(df["aih"], errors="coerce").fillna(0)
    return df

df = carregar()

# Listas de opções
GRUPOS = sorted(df["grupo_cid"].unique().tolist())
ANOS   = sorted(df["ano"].unique().tolist())

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configurações")
    st.markdown("---")

    grupo_sel = st.selectbox(
        "Grupo CID-10 principal",
        options=GRUPOS,
        index=GRUPOS.index("Respiratório") if "Respiratório" in GRUPOS else 0,
        key="grupo_principal"
    )

    grupos_comp = st.multiselect(
        "Comparar com",
        options=[g for g in GRUPOS if g != grupo_sel],
        default=["Cardiovascular","Infeccioso/Parasitário"],
        key="grupos_comp"
    )

    st.markdown("---")
    excluir_covid = st.checkbox("Excluir 2020 da tendência", value=True, key="excl_covid")
    excluir_2026  = st.checkbox("Excluir 2026 (incompleto)", value=True, key="excl_2026")

    st.markdown("---")
    st.caption("Fonte: SIH/SUS — TabNet/DATASUS")

# Anos excluídos
anos_excluir = []
if excluir_covid: anos_excluir.append(2020)
if excluir_2026:  anos_excluir.append(2026)
anos_tend = [a for a in ANOS if a not in anos_excluir]

# ════════════════════════════════════════════════════════════════
# SEÇÃO 1 — DECOMPOSIÇÃO DE SAZONALIDADE
# ════════════════════════════════════════════════════════════════
st.subheader(f"📊 Decomposição de Sazonalidade — {grupo_sel}")

df_grupo = df[df["grupo_cid"] == grupo_sel].copy()
serie = df_grupo.groupby(["ano","mes"])["aih"].sum().reset_index()
serie = serie.sort_values(["ano","mes"]).reset_index(drop=True)
serie["periodo"] = serie["ano"].astype(str) + "-" + serie["mes"].astype(str).str.zfill(2)
serie["tendencia"] = serie["aih"].rolling(12, center=True).mean()
serie["fator_saz"] = serie["aih"] / serie["tendencia"]

# Índice sazonal por mês
idx_saz = serie[serie["tendencia"].notna()].groupby("mes")["fator_saz"].mean()
idx_pct  = (idx_saz * 100).round(1)

fig_dec = make_subplots(
    rows=3, cols=1,
    subplot_titles=(
        "Série Original + Tendência (Média Móvel 12 meses)",
        "Fator Sazonal mensal (1.0 = média)",
        "Índice de Sazonalidade por Mês (100 = média anual)"
    ),
    vertical_spacing=0.1
)

fig_dec.add_trace(go.Scatter(
    x=serie["periodo"], y=serie["aih"],
    name="AIH observada", mode="lines",
    line=dict(color="#90CAF9", width=1),
    fill="tozeroy", fillcolor="rgba(144,202,249,0.1)"
), row=1, col=1)

fig_dec.add_trace(go.Scatter(
    x=serie["periodo"], y=serie["tendencia"],
    name="Tendência MM12", mode="lines",
    line=dict(color="#E53935", width=2.5)
), row=1, col=1)

cores_fator = ["#E53935" if v > 1.05 else "#4CAF50" if v < 0.95 else "#FB8C00"
               for v in serie["fator_saz"].fillna(1)]
fig_dec.add_trace(go.Bar(
    x=serie["periodo"], y=serie["fator_saz"],
    name="Fator sazonal", marker_color=cores_fator, opacity=0.7
), row=2, col=1)
fig_dec.add_hline(y=1.0, line_dash="dash", line_color="gray", row=2, col=1)

cores_idx = ["#E53935" if v > 105 else "#4CAF50" if v < 95 else "#FB8C00"
             for v in idx_pct.values]
fig_dec.add_trace(go.Bar(
    x=[MESES_N[m] for m in idx_pct.index],
    y=idx_pct.values,
    name="Índice sazonal",
    marker_color=cores_idx,
    text=[f"{v:.1f}" for v in idx_pct.values],
    textposition="outside"
), row=3, col=1)
fig_dec.add_hline(y=100, line_dash="dash", line_color="gray", row=3, col=1)

fig_dec.update_layout(height=750, hovermode="x unified", showlegend=True)
fig_dec.update_xaxes(tickangle=-45, row=1, col=1)
fig_dec.update_xaxes(tickangle=-45, row=2, col=1)
st.plotly_chart(fig_dec, use_container_width=True)

pico = idx_pct.idxmax()
vale = idx_pct.idxmin()
amp  = idx_pct.max() - idx_pct.min()
st.info(
    f"📌 **{grupo_sel}** · Pico: **{MESES_N[pico]}** ({idx_pct[pico]:.1f}%) · "
    f"Vale: **{MESES_N[vale]}** ({idx_pct[vale]:.1f}%) · "
    f"Amplitude sazonal: **{amp:.1f} pp**"
)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 2 — RADAR + HEATMAP COMPARATIVO
# ════════════════════════════════════════════════════════════════
st.subheader("🌊 Comparativo de Sazonalidade entre Grupos")

grupos_analisar = [grupo_sel] + grupos_comp
df_filt_covid   = df[~df["ano"].isin([2020,2026])]

idx_todos = []
for g in grupos_analisar:
    sub = df_filt_covid[df_filt_covid["grupo_cid"] == g]
    mm  = sub.groupby("mes")["aih"].mean()
    mt  = mm.mean()
    for mes, val in mm.items():
        idx_todos.append({"grupo_cid":g,"mes":mes,
                          "mes_nome":MESES_N[mes],
                          "indice":round(val/mt*100,1)})

df_idx = pd.DataFrame(idx_todos)

col_r, col_h = st.columns(2)

with col_r:
    fig_radar = go.Figure()
    cores_r = ["#E53935","#2196F3","#4CAF50","#FF9800","#9C27B0"]
    for i, g in enumerate(grupos_analisar):
        sub = df_idx[df_idx["grupo_cid"]==g].sort_values("mes")
        vals = sub["indice"].tolist() + [sub["indice"].iloc[0]]
        meses_r = [MESES_N[m] for m in sub["mes"]] + [MESES_N[sub["mes"].iloc[0]]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=meses_r,
            fill="toself", name=g,
            line=dict(color=cores_r[i % len(cores_r)], width=2),
            fillcolor=cores_r[i % len(cores_r)],
            opacity=0.15
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[60,145])),
        title="Radar de sazonalidade por grupo",
        height=420, showlegend=True
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_h:
    # Heatmap todos grupos
    idx_heat = []
    for g in GRUPOS:
        sub = df_filt_covid[df_filt_covid["grupo_cid"]==g]
        mm  = sub.groupby("mes")["aih"].mean()
        mt  = mm.mean()
        for mes, val in mm.items():
            idx_heat.append({"grupo_cid":g,"mes_nome":MESES_N[mes],
                             "mes":mes,"indice":round(val/mt*100,1)})
    df_heat = pd.DataFrame(idx_heat)
    pivot   = df_heat.pivot(index="grupo_cid", columns="mes_nome", values="indice")
    pivot   = pivot[[m for m in ORDER_MESES if m in pivot.columns]]

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#1565C0"],[0.4,"#90CAF9"],[0.5,"#FFFFFF"],
                    [0.6,"#EF9A9A"],[1,"#B71C1C"]],
        zmid=100,
        text=np.round(pivot.values,1),
        texttemplate="%{text}", textfont={"size":8},
        colorbar=dict(title="Índice")
    ))
    fig_heat.update_layout(
        title="Índice sazonal: todos os grupos × mês",
        height=420, xaxis_title="Mês", yaxis_title=""
    )
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 3 — TENDÊNCIA E CAGR
# ════════════════════════════════════════════════════════════════
st.subheader("📈 Tendência e Taxa de Crescimento (CAGR 2016→2024)")

cagr_data = []
for g in GRUPOS:
    sub = df[df["grupo_cid"]==g]
    a16 = sub[sub["ano"]==2016]["aih"].sum()
    a24 = sub[sub["ano"]==2024]["aih"].sum()
    if a16 > 0 and a24 > 0:
        cagr = ((a24/a16)**(1/8)-1)*100
        cagr_data.append({
            "grupo_cid":g,
            "aih_2016":a16,"aih_2024":a24,
            "cagr":round(cagr,1),
            "var_total":round((a24/a16-1)*100,1)
        })

df_cagr = pd.DataFrame(cagr_data).sort_values("cagr")

col_c1, col_c2 = st.columns([3,2])

with col_c1:
    cores_c = ["#E53935" if v<0 else "#4CAF50" if v>5 else "#FB8C00"
               for v in df_cagr["cagr"]]
    fig_cagr = go.Figure(go.Bar(
        x=df_cagr["cagr"], y=df_cagr["grupo_cid"],
        orientation="h", marker_color=cores_c,
        text=[f"{v:+.1f}% aa" for v in df_cagr["cagr"]],
        textposition="outside"
    ))
    fig_cagr.add_vline(x=0, line_color="gray", line_dash="dash")
    fig_cagr.add_vline(
        x=df_cagr["cagr"].mean(), line_color="#FF9800", line_dash="dot",
        annotation_text=f"Média: {df_cagr['cagr'].mean():.1f}%"
    )
    fig_cagr.update_layout(
        title="CAGR por grupo CID-10 (excl. COVID 2020)",
        xaxis_title="Taxa de crescimento anual (%)",
        height=500, showlegend=False
    )
    st.plotly_chart(fig_cagr, use_container_width=True)

with col_c2:
    st.markdown("**Ranking de crescimento**")
    df_rank = df_cagr[["grupo_cid","cagr","var_total"]].sort_values(
        "cagr", ascending=False
    ).reset_index(drop=True)
    df_rank.index += 1
    df_rank.columns = ["Grupo CID-10","CAGR (% aa)","Var. Total (%)"]
    st.dataframe(df_rank, use_container_width=True, height=450)

# Regressão do grupo selecionado
st.markdown(f"**Regressão linear de tendência — {grupo_sel}**")
df_reg = df[df["grupo_cid"]==grupo_sel].groupby("ano")["aih"].sum().reset_index()
df_reg_filt = df_reg[~df_reg["ano"].isin(anos_excluir)]

z   = np.polyfit(df_reg_filt["ano"], df_reg_filt["aih"], 1)
p   = np.poly1d(z)
res = df_reg_filt["aih"] - p(df_reg_filt["ano"])
r2  = 1 - np.sum(res**2) / np.sum((df_reg_filt["aih"] - df_reg_filt["aih"].mean())**2)
std = np.std(res)
anos_proj = list(range(2016, 2027))

fig_reg = go.Figure()
fig_reg.add_trace(go.Bar(
    x=df_reg["ano"], y=df_reg["aih"],
    name="AIH observada",
    marker_color=["#F44336" if a in anos_excluir else "#2196F3"
                  for a in df_reg["ano"]],
    opacity=0.7
))
fig_reg.add_trace(go.Scatter(
    x=anos_proj, y=[p(a) for a in anos_proj],
    mode="lines+markers", name="Tendência linear",
    line=dict(color="#FF9800", width=2.5, dash="dash")
))
fig_reg.add_trace(go.Scatter(
    x=anos_proj+anos_proj[::-1],
    y=[p(a)+1.96*std for a in anos_proj]+[p(a)-1.96*std for a in anos_proj[::-1]],
    fill="toself", fillcolor="rgba(255,152,0,0.1)",
    line=dict(color="rgba(0,0,0,0)"), name="IC 95%"
))
fig_reg.update_layout(
    title=f"{grupo_sel} · R²={r2:.3f} · Crescimento: {z[0]:+,.0f} AIH/ano",
    xaxis_title="Ano", yaxis_title="AIH",
    hovermode="x unified", height=400
)
st.plotly_chart(fig_reg, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 4 — DETECÇÃO DE ANOMALIAS
# ════════════════════════════════════════════════════════════════
st.subheader(f"🔍 Detecção de Anomalias — {grupo_sel}")

baseline  = df[(df["grupo_cid"]==grupo_sel) & (df["ano"].between(2016,2019))]
stats_mes = baseline.groupby("mes")["aih"].agg(["mean","std"]).reset_index()
stats_mes.columns = ["mes","media","std"]

df_anom = df[df["grupo_cid"]==grupo_sel].groupby(["ano","mes"])["aih"].sum().reset_index()
df_anom = df_anom.merge(stats_mes, on="mes")
df_anom["z"] = (df_anom["aih"] - df_anom["media"]) / df_anom["std"].replace(0, np.nan)
df_anom["anomalia"] = df_anom["z"].abs() > 2
df_anom["periodo"] = df_anom["ano"].astype(str) + "-" + df_anom["mes"].astype(str).str.zfill(2)

fig_anom = go.Figure()
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"],
    y=df_anom["media"] + 2*df_anom["std"],
    mode="lines", name="+2σ",
    line=dict(color="rgba(244,67,54,0.3)", width=1, dash="dot")
))
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"],
    y=df_anom["media"] - 2*df_anom["std"],
    mode="lines", name="-2σ",
    fill="tonexty", fillcolor="rgba(76,175,80,0.07)",
    line=dict(color="rgba(76,175,80,0.3)", width=1, dash="dot")
))
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"], y=df_anom["media"],
    mode="lines", name="Média histórica",
    line=dict(color="#4CAF50", width=1.5, dash="dash")
))
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"], y=df_anom["aih"],
    mode="lines+markers", name="AIH observada",
    line=dict(color="#2196F3", width=2), marker=dict(size=4)
))
anom = df_anom[df_anom["anomalia"]]
if not anom.empty:
    fig_anom.add_trace(go.Scatter(
        x=anom["periodo"], y=anom["aih"],
        mode="markers", name="⚠️ Anomalia",
        marker=dict(color="#F44336", size=12, symbol="star",
                    line=dict(width=2, color="#B71C1C"))
    ))
fig_anom.update_layout(
    title=f"Anomalias — {grupo_sel} (baseline 2016-2019, ±2σ)",
    xaxis_title="Período", yaxis_title="AIH",
    hovermode="x unified", height=420
)
fig_anom.update_xaxes(tickangle=-45)
st.plotly_chart(fig_anom, use_container_width=True)

if not anom.empty:
    tab_anom = anom[["ano","mes","aih","media","z"]].copy()
    tab_anom["mes"] = tab_anom["mes"].map(MESES_N)
    tab_anom.columns = ["Ano","Mês","AIH observada","Média histórica","Z-score"]
    tab_anom["AIH observada"]    = tab_anom["AIH observada"].apply(lambda x: f"{int(x):,}")
    tab_anom["Média histórica"]  = tab_anom["Média histórica"].apply(lambda x: f"{int(x):,}")
    tab_anom["Z-score"]          = tab_anom["Z-score"].apply(lambda x: f"{x:+.2f}σ")
    st.dataframe(tab_anom.sort_values("Z-score",ascending=False), use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 5 — PERFIL SAZONAL POR ANO
# ════════════════════════════════════════════════════════════════
st.subheader(f"🎯 Perfil Sazonal por Ano — {grupo_sel}")

df_perf   = df[df["grupo_cid"]==grupo_sel].groupby(["ano","mes"])["aih"].sum().reset_index()
med_hist  = df_perf[df_perf["ano"].between(2016,2019)].groupby("mes")["aih"].mean()
cores_ano = {2016:"#90CAF9",2017:"#80CBC4",2018:"#A5D6A7",2019:"#C5E1A5",
             2020:"#EF9A9A",2021:"#FFCC80",2022:"#CE93D8",2023:"#80DEEA",
             2024:"#F48FB1",2025:"#BCAAA4",2026:"#B0BEC5"}

fig_perf = go.Figure()
fig_perf.add_trace(go.Scatter(
    x=[MESES_N[m] for m in sorted(med_hist.index)],
    y=med_hist.values,
    mode="lines", name="Média 2016–2019",
    line=dict(color="#000000", width=3, dash="dash")
))
for ano in sorted(df_perf["ano"].unique()):
    sub = df_perf[df_perf["ano"]==ano].sort_values("mes")
    fig_perf.add_trace(go.Scatter(
        x=[MESES_N[m] for m in sub["mes"]], y=sub["aih"],
        mode="lines+markers", name=str(ano),
        line=dict(color=cores_ano.get(ano,"#999"), width=2),
        marker=dict(size=6),
        visible=True if ano >= 2019 else "legendonly"
    ))
fig_perf.update_layout(
    title=f"Perfil sazonal por ano — {grupo_sel}",
    xaxis=dict(categoryorder="array", categoryarray=ORDER_MESES),
    xaxis_title="Mês", yaxis_title="AIH",
    hovermode="x unified", height=480
)
st.plotly_chart(fig_perf, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 6 — CORRELAÇÃO ENTRE GRUPOS
# ════════════════════════════════════════════════════════════════
st.subheader("🔗 Matriz de Correlação Sazonal entre Grupos")

pivot_corr = df_filt_covid.groupby(["mes","grupo_cid"])["aih"].mean().unstack("grupo_cid")
corr = pivot_corr.corr().round(2)

fig_corr = go.Figure(data=go.Heatmap(
    z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
    colorscale=[[0,"#1565C0"],[0.5,"#FFFFFF"],[1,"#B71C1C"]],
    zmid=0,
    text=corr.values, texttemplate="%{text:.2f}", textfont={"size":8},
    colorbar=dict(title="Corr.")
))
fig_corr.update_layout(
    title="Correlação sazonal entre grupos CID-10 (azul=oposto, vermelho=similar)",
    height=580, xaxis=dict(tickangle=-45)
)
st.plotly_chart(fig_corr, use_container_width=True)

corr_g = corr[grupo_sel].drop(grupo_sel).sort_values(ascending=False)
c1, c2 = st.columns(2)
with c1:
    st.success(
        f"**{grupo_sel}** tem sazonalidade similar a:\n\n" +
        "\n".join([f"- **{g}**: {v:.2f}" for g,v in corr_g.head(3).items()])
    )
with c2:
    st.warning(
        f"**{grupo_sel}** tem sazonalidade oposta a:\n\n" +
        "\n".join([f"- **{g}**: {v:.2f}" for g,v in corr_g.tail(3).items()])
    )

# Download
csv = df.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    "⬇️ Baixar dados completos (.csv)",
    data=csv, file_name="sazonalidade_2016_2026.csv", mime="text/csv"
)
