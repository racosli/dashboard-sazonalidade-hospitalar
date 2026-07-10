# ============================================================
# DASHBOARD DE SAZONALIDADE HOSPITALAR — VERSÃO AVANÇADA
# Análise estatística real: decomposição, CAGR, anomalias
# SIH/DATASUS Brasil 2016–2026 — 129M de AIH aprovadas
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Sazonalidade Hospitalar — Análise Avançada",
    page_icon="🏥", layout="wide"
)

st.title("🏥 Análise Avançada de Sazonalidade Hospitalar")
st.caption("SIH/DATASUS Brasil 2016–2026 · 129 milhões de internações · 21 grupos CID-10")
st.markdown("---")

ORDER_MESES = ["Jan","Fev","Mar","Abr","Mai","Jun",
               "Jul","Ago","Set","Out","Nov","Dez"]
MESES_N = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
           7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

# ── Carregar dados ────────────────────────────────────────────
@st.cache_data
def carregar():
    df = pd.read_csv("dados/tabnet_10anos.csv", encoding="utf-8")
    return df

df = carregar()

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.title("🔍 Configurações")
st.sidebar.markdown("---")

grupos_disp = sorted(df["grupo_cid"].unique())
grupo_sel = st.sidebar.selectbox(
    "Grupo CID-10 principal", grupos_disp,
    index=grupos_disp.index("Respiratorio")
)

grupos_comp = st.sidebar.multiselect(
    "Comparar com outros grupos",
    [g for g in grupos_disp if g != grupo_sel],
    default=["Cardiovascular","Infeccioso/Parasitario"]
)

excluir_covid = st.sidebar.checkbox(
    "Excluir 2020 das análises de tendência", value=True
)
excluir_2026 = st.sidebar.checkbox(
    "Excluir 2026 (ano incompleto)", value=True
)

st.sidebar.markdown("---")
st.sidebar.caption("Fonte: SIH/SUS — TabNet/DATASUS")

# Anos para análise
anos_excluir = []
if excluir_covid: anos_excluir.append(2020)
if excluir_2026: anos_excluir.append(2026)
anos_tend = [a for a in sorted(df["ano"].unique()) if a not in anos_excluir]

# ════════════════════════════════════════════════════════════════
# SEÇÃO 1 — DECOMPOSIÇÃO DE SAZONALIDADE
# ════════════════════════════════════════════════════════════════
st.subheader("📊 Decomposição de Sazonalidade — Tendência + Ciclo Sazonal")
st.markdown(f"Análise do grupo **{grupo_sel}** com decomposição estatística da série temporal")

# Preparar série temporal mensal
df_grupo = df[df["grupo_cid"]==grupo_sel].copy()
serie = df_grupo.groupby(["ano","mes"])["aih"].sum().reset_index()
serie = serie.sort_values(["ano","mes"]).reset_index(drop=True)
serie["periodo"] = serie["ano"].astype(str) + "-" + serie["mes"].astype(str).str.zfill(2)
serie["t"] = range(len(serie))

# Médias móveis 12 meses (tendência)
serie["tendencia"] = serie["aih"].rolling(12, center=True).mean()

# Componente sazonal = valor / tendência
serie["sazonalidade"] = serie["aih"] / serie["tendencia"]

# Índice sazonal médio por mês
idx_saz = serie[~serie["tendencia"].isna()].groupby("mes")["sazonalidade"].mean()
idx_saz_pct = (idx_saz * 100).round(1)

fig_decomp = make_subplots(
    rows=3, cols=1,
    subplot_titles=(
        "Série Original + Tendência (Média Móvel 12 meses)",
        "Componente Sazonal (desvio da tendência)",
        "Índice de Sazonalidade por Mês (100 = média)"
    ),
    vertical_spacing=0.1
)

# Série original
fig_decomp.add_trace(go.Scatter(
    x=serie["periodo"], y=serie["aih"],
    name="AIH observada", mode="lines",
    line=dict(color="#90CAF9", width=1),
    fill="tozeroy", fillcolor="rgba(144,202,249,0.1)"
), row=1, col=1)

# Tendência
fig_decomp.add_trace(go.Scatter(
    x=serie["periodo"], y=serie["tendencia"],
    name="Tendência (MM12)", mode="lines",
    line=dict(color="#E53935", width=2.5)
), row=1, col=1)

# Sazonalidade
cores_saz = ["#E53935" if v > 1.05 else "#4CAF50" if v < 0.95 else "#FB8C00"
             for v in serie["sazonalidade"].fillna(1)]
fig_decomp.add_trace(go.Bar(
    x=serie["periodo"], y=serie["sazonalidade"],
    name="Fator sazonal", marker_color=cores_saz,
    opacity=0.7
), row=2, col=1)
fig_decomp.add_hline(y=1.0, line_dash="dash", line_color="gray", row=2, col=1)

# Índice por mês
cores_idx = ["#E53935" if v > 105 else "#4CAF50" if v < 95 else "#FB8C00"
             for v in idx_saz_pct.values]
fig_decomp.add_trace(go.Bar(
    x=[MESES_N[m] for m in idx_saz_pct.index],
    y=idx_saz_pct.values,
    name="Índice sazonal",
    marker_color=cores_idx,
    text=[f"{v:.1f}" for v in idx_saz_pct.values],
    textposition="outside"
), row=3, col=1)
fig_decomp.add_hline(y=100, line_dash="dash", line_color="gray", row=3, col=1)

fig_decomp.update_layout(height=750, showlegend=True,
                          hovermode="x unified")
fig_decomp.update_xaxes(tickangle=-45, row=1, col=1)
fig_decomp.update_xaxes(tickangle=-45, row=2, col=1)
st.plotly_chart(fig_decomp, use_container_width=True)

# Insight automático
pico_mes = idx_saz_pct.idxmax()
vale_mes = idx_saz_pct.idxmin()
amplitude = idx_saz_pct.max() - idx_saz_pct.min()
st.info(
    f"📌 **{grupo_sel}**: pico em **{MESES_N[pico_mes]}** "
    f"({idx_saz_pct[pico_mes]:.1f}% da média) | "
    f"vale em **{MESES_N[vale_mes]}** ({idx_saz_pct[vale_mes]:.1f}% da média) | "
    f"amplitude sazonal: **{amplitude:.1f} pontos percentuais**"
)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 2 — COMPARATIVO DE SAZONALIDADE ENTRE GRUPOS
# ════════════════════════════════════════════════════════════════
st.subheader("🌊 Comparativo de Sazonalidade entre Grupos CID-10")

grupos_analisar = [grupo_sel] + grupos_comp
df_comp = df[df["grupo_cid"].isin(grupos_analisar)].copy()
df_comp_filt = df_comp[~df_comp["ano"].isin([2020,2026])]

# Calcular índice sazonal para cada grupo
idx_por_grupo = []
for g in grupos_analisar:
    sub = df_comp_filt[df_comp_filt["grupo_cid"]==g]
    med_mes = sub.groupby("mes")["aih"].mean()
    med_tot = med_mes.mean()
    for mes, val in med_mes.items():
        idx_por_grupo.append({
            "grupo_cid": g,
            "mes": mes,
            "mes_nome": MESES_N[mes],
            "indice": round(val / med_tot * 100, 1)
        })

df_idx = pd.DataFrame(idx_por_grupo)

# Radar chart de sazonalidade
fig_radar = go.Figure()
cores_radar = ["#E53935","#2196F3","#4CAF50","#FF9800","#9C27B0"]
for i, grupo in enumerate(grupos_analisar):
    sub = df_idx[df_idx["grupo_cid"]==grupo].sort_values("mes")
    valores = sub["indice"].tolist()
    valores.append(valores[0])  # fechar o polígono
    meses_r = [MESES_N[m] for m in sub["mes"]] + [MESES_N[sub["mes"].iloc[0]]]
    fig_radar.add_trace(go.Scatterpolar(
        r=valores, theta=meses_r,
        fill="toself", name=grupo,
        line=dict(color=cores_radar[i % len(cores_radar)], width=2),
        fillcolor=cores_radar[i % len(cores_radar)],
        opacity=0.15
    ))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[60,140])),
    title="Radar de sazonalidade — índice mensal por grupo CID-10 (100 = média anual)",
    height=500, showlegend=True
)
st.plotly_chart(fig_radar, use_container_width=True)

# Heatmap grupo × mês com índice sazonal
st.markdown("**Mapa de calor: índice sazonal por grupo CID-10 e mês**")
todos_grupos_idx = []
for g in grupos_disp:
    sub = df[df["grupo_cid"]==g]
    sub_filt = sub[~sub["ano"].isin([2020,2026])]
    med_mes = sub_filt.groupby("mes")["aih"].mean()
    med_tot = med_mes.mean()
    for mes, val in med_mes.items():
        todos_grupos_idx.append({
            "grupo_cid": g,
            "mes_nome": MESES_N[mes],
            "mes": mes,
            "indice": round(val / med_tot * 100, 1)
        })

df_heat = pd.DataFrame(todos_grupos_idx)
pivot_heat = df_heat.pivot(index="grupo_cid", columns="mes_nome", values="indice")
pivot_heat = pivot_heat[[m for m in ORDER_MESES if m in pivot_heat.columns]]

fig_heat = go.Figure(data=go.Heatmap(
    z=pivot_heat.values,
    x=pivot_heat.columns.tolist(),
    y=pivot_heat.index.tolist(),
    colorscale=[
        [0.0, "#1565C0"], [0.35, "#42A5F5"],
        [0.5, "#FFFFFF"],
        [0.65, "#EF9A9A"], [1.0, "#B71C1C"]
    ],
    zmid=100,
    text=np.round(pivot_heat.values, 1),
    texttemplate="%{text}",
    textfont={"size":9},
    colorbar=dict(title="Índice<br>(100=média)")
))
fig_heat.update_layout(
    title="Índice de sazonalidade: todos os grupos CID-10 × mês (azul=abaixo, vermelho=acima da média)",
    height=600, xaxis_title="Mês", yaxis_title="Grupo CID-10"
)
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 3 — ANÁLISE DE TENDÊNCIA E CRESCIMENTO
# ════════════════════════════════════════════════════════════════
st.subheader("📈 Análise de Tendência e Taxa de Crescimento (CAGR)")

# Calcular CAGR por grupo
cagr_data = []
for g in grupos_disp:
    sub = df[df["grupo_cid"]==g]
    a16 = sub[sub["ano"]==2016]["aih"].sum()
    a24 = sub[sub["ano"]==2024]["aih"].sum()
    if a16 > 0 and a24 > 0:
        cagr = ((a24/a16)**(1/8)-1)*100
        cagr_data.append({
            "grupo_cid": g,
            "aih_2016": a16,
            "aih_2024": a24,
            "cagr": round(cagr, 1),
            "variacao_total": round((a24/a16-1)*100, 1)
        })

df_cagr = pd.DataFrame(cagr_data).sort_values("cagr", ascending=True)
df_cagr = df_cagr[df_cagr["cagr"] > -50]  # excluir anomalias

col_c1, col_c2 = st.columns([3,2])

with col_c1:
    cores_cagr = ["#E53935" if v < 0 else "#4CAF50" if v > 5 else "#FB8C00"
                  for v in df_cagr["cagr"]]
    fig_cagr = go.Figure(go.Bar(
        x=df_cagr["cagr"],
        y=df_cagr["grupo_cid"],
        orientation="h",
        marker_color=cores_cagr,
        text=[f"{v:+.1f}% aa" for v in df_cagr["cagr"]],
        textposition="outside"
    ))
    fig_cagr.add_vline(x=0, line_color="gray", line_dash="dash")
    fig_cagr.add_vline(x=df_cagr["cagr"].mean(), line_color="#FF9800",
                       line_dash="dot",
                       annotation_text=f"Média: {df_cagr['cagr'].mean():.1f}%",
                       annotation_position="top")
    fig_cagr.update_layout(
        title="CAGR por grupo CID-10 (2016→2024, excl. COVID 2020)",
        xaxis_title="Taxa de crescimento anual composta (%)",
        height=500, showlegend=False
    )
    st.plotly_chart(fig_cagr, use_container_width=True)

with col_c2:
    st.markdown("**Classificação por crescimento**")
    df_cagr_show = df_cagr[["grupo_cid","cagr","variacao_total"]].sort_values("cagr",ascending=False)
    df_cagr_show.columns = ["Grupo CID-10","CAGR (% aa)","Variação Total (%)"]

    def colorir_cagr(val):
        if isinstance(val, float):
            if val > 5: return "color: #4CAF50; font-weight: bold"
            if val < 0: return "color: #E53935; font-weight: bold"
            return "color: #FB8C00"
        return ""

    st.dataframe(
        df_cagr_show.style.applymap(colorir_cagr, subset=["CAGR (% aa)","Variação Total (%)"]),
        use_container_width=True, height=450
    )

# Gráfico de tendência com regressão por grupo selecionado
st.markdown(f"**Regressão linear de tendência — {grupo_sel}**")
df_tend = df[(df["grupo_cid"]==grupo_sel)].groupby("ano")["aih"].sum().reset_index()
df_tend_filt = df_tend[~df_tend["ano"].isin(anos_excluir)]

z = np.polyfit(df_tend_filt["ano"], df_tend_filt["aih"], 1)
p = np.poly1d(z)
anos_proj = list(range(2016, 2027))
proj = [p(a) for a in anos_proj]
residuos = df_tend_filt["aih"] - p(df_tend_filt["ano"])
r2 = 1 - np.sum(residuos**2) / np.sum((df_tend_filt["aih"] - df_tend_filt["aih"].mean())**2)

fig_reg = go.Figure()
cores_barras = ["#F44336" if a in anos_excluir else "#2196F3" for a in df_tend["ano"]]
fig_reg.add_trace(go.Bar(
    x=df_tend["ano"], y=df_tend["aih"],
    name="AIH observada",
    marker_color=cores_barras,
    opacity=0.7
))
fig_reg.add_trace(go.Scatter(
    x=anos_proj, y=proj,
    mode="lines+markers", name="Tendência linear",
    line=dict(color="#FF9800", width=2.5, dash="dash")
))

# Intervalo de confiança simples
std_res = np.std(residuos)
fig_reg.add_trace(go.Scatter(
    x=anos_proj, y=[v + 1.96*std_res for v in proj],
    mode="lines", name="IC 95% superior",
    line=dict(color="rgba(255,152,0,0.3)", width=1),
    showlegend=False
))
fig_reg.add_trace(go.Scatter(
    x=anos_proj, y=[v - 1.96*std_res for v in proj],
    mode="lines", name="IC 95%",
    fill="tonexty",
    fillcolor="rgba(255,152,0,0.1)",
    line=dict(color="rgba(255,152,0,0.3)", width=1)
))

crescimento_anual = z[0]
fig_reg.update_layout(
    title=f"{grupo_sel} — Tendência linear | R²={r2:.3f} | "
          f"Crescimento: {crescimento_anual:+,.0f} AIH/ano",
    xaxis_title="Ano", yaxis_title="AIH Aprovadas",
    hovermode="x unified", height=400
)
if 2020 in anos_excluir:
    fig_reg.add_annotation(x=2020, y=df_tend[df_tend["ano"]==2020]["aih"].values[0],
                           text="COVID-19\n(excluído)", showarrow=True,
                           font=dict(color="#F44336"), ay=-50)
st.plotly_chart(fig_reg, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 4 — ANOMALIAS E EVENTOS
# ════════════════════════════════════════════════════════════════
st.subheader("🔍 Detecção de Anomalias e Eventos")

st.markdown(f"Detecção de meses com comportamento anômalo em **{grupo_sel}** "
            f"(desvio > 2 desvios padrão da média histórica)")

# Calcular média e desvio por mês (histórico 2016-2019 como baseline)
baseline = df[(df["grupo_cid"]==grupo_sel) & (df["ano"].between(2016,2019))]
stats_mes = baseline.groupby("mes")["aih"].agg(["mean","std"]).reset_index()
stats_mes.columns = ["mes","media","std"]

# Aplicar ao série completa
df_anom = df[df["grupo_cid"]==grupo_sel].groupby(["ano","mes"])["aih"].sum().reset_index()
df_anom = df_anom.merge(stats_mes, on="mes")
df_anom["z_score"] = (df_anom["aih"] - df_anom["media"]) / df_anom["std"]
df_anom["anomalia"] = df_anom["z_score"].abs() > 2
df_anom["periodo"] = df_anom["ano"].astype(str) + "-" + df_anom["mes"].astype(str).str.zfill(2)
df_anom["mes_nome"] = df_anom["mes"].map(MESES_N)

fig_anom = go.Figure()
# Faixa normal
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"],
    y=df_anom["media"] + 2*df_anom["std"],
    mode="lines", name="Limite superior (+2σ)",
    line=dict(color="rgba(244,67,54,0.4)", width=1, dash="dot"),
    showlegend=True
))
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"],
    y=df_anom["media"] - 2*df_anom["std"],
    mode="lines", name="Limite inferior (-2σ)",
    fill="tonexty",
    fillcolor="rgba(76,175,80,0.08)",
    line=dict(color="rgba(76,175,80,0.4)", width=1, dash="dot")
))
# Média histórica
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"], y=df_anom["media"],
    mode="lines", name="Média histórica (2016-2019)",
    line=dict(color="#4CAF50", width=1.5, dash="dash")
))
# Série real
fig_anom.add_trace(go.Scatter(
    x=df_anom["periodo"], y=df_anom["aih"],
    mode="lines+markers", name="AIH observada",
    line=dict(color="#2196F3", width=2),
    marker=dict(size=5)
))
# Anomalias
anom = df_anom[df_anom["anomalia"]]
fig_anom.add_trace(go.Scatter(
    x=anom["periodo"], y=anom["aih"],
    mode="markers", name="Anomalia detectada",
    marker=dict(color="#F44336", size=12, symbol="star",
                line=dict(width=2, color="#B71C1C"))
))
fig_anom.update_layout(
    title=f"Detecção de anomalias — {grupo_sel} (baseline: 2016-2019, ±2σ)",
    xaxis_title="Período", yaxis_title="AIH Aprovadas",
    hovermode="x unified", height=450
)
fig_anom.update_xaxes(tickangle=-45)
st.plotly_chart(fig_anom, use_container_width=True)

# Tabela de anomalias
if not anom.empty:
    anom_show = anom[["ano","mes_nome","aih","media","z_score"]].copy()
    anom_show.columns = ["Ano","Mês","AIH observada","Média histórica","Z-score"]
    anom_show["AIH observada"] = anom_show["AIH observada"].apply(lambda x: f"{int(x):,}")
    anom_show["Média histórica"] = anom_show["Média histórica"].apply(lambda x: f"{int(x):,}")
    anom_show["Z-score"] = anom_show["Z-score"].apply(lambda x: f"{x:+.2f}σ")
    st.dataframe(anom_show.sort_values("Z-score", ascending=False),
                 use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 5 — PERFIL SAZONAL INTERATIVO
# ════════════════════════════════════════════════════════════════
st.subheader("🎯 Perfil Sazonal Detalhado por Ano")
st.markdown("Visualize como o padrão sazonal de cada ano se compara com a média histórica")

df_perf = df[df["grupo_cid"]==grupo_sel].groupby(["ano","mes"])["aih"].sum().reset_index()
media_hist = df_perf[df_perf["ano"].between(2016,2019)].groupby("mes")["aih"].mean()

fig_perf = go.Figure()
anos_todos = sorted(df_perf["ano"].unique())
cores_perf = {
    2016:"#90CAF9",2017:"#80CBC4",2018:"#A5D6A7",2019:"#C5E1A5",
    2020:"#EF9A9A",2021:"#FFCC80",2022:"#CE93D8",2023:"#80DEEA",
    2024:"#F48FB1",2025:"#BCAAA4",2026:"#B0BEC5"
}

# Média histórica como referência
fig_perf.add_trace(go.Scatter(
    x=[MESES_N[m] for m in sorted(media_hist.index)],
    y=media_hist.values,
    mode="lines", name="Média 2016-2019",
    line=dict(color="#000000", width=3, dash="dash"),
))

for ano in anos_todos:
    sub = df_perf[df_perf["ano"]==ano].sort_values("mes")
    visivel = True if ano >= 2019 else "legendonly"
    fig_perf.add_trace(go.Scatter(
        x=[MESES_N[m] for m in sub["mes"]],
        y=sub["aih"],
        mode="lines+markers",
        name=str(ano),
        line=dict(color=cores_perf.get(ano,"#999"), width=2),
        marker=dict(size=6),
        visible=visivel
    ))

fig_perf.update_layout(
    title=f"Perfil sazonal por ano — {grupo_sel} (clique na legenda para ativar/desativar anos)",
    xaxis=dict(categoryorder="array", categoryarray=ORDER_MESES),
    xaxis_title="Mês", yaxis_title="AIH Aprovadas",
    hovermode="x unified", height=500
)
st.plotly_chart(fig_perf, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# SEÇÃO 6 — CORRELAÇÃO ENTRE GRUPOS
# ════════════════════════════════════════════════════════════════
st.subheader("🔗 Correlação Sazonal entre Grupos CID-10")
st.markdown("Grupos com alta correlação positiva têm picos nos mesmos meses; "
            "negativa, em meses opostos")

pivot_corr = df[~df["ano"].isin([2020,2026])].groupby(
    ["mes","grupo_cid"])["aih"].mean().unstack("grupo_cid")
corr = pivot_corr.corr().round(2)

fig_corr = go.Figure(data=go.Heatmap(
    z=corr.values,
    x=corr.columns.tolist(),
    y=corr.index.tolist(),
    colorscale=[
        [0.0,"#1565C0"],[0.5,"#FFFFFF"],[1.0,"#B71C1C"]
    ],
    zmid=0,
    text=corr.values,
    texttemplate="%{text:.2f}",
    textfont={"size":8},
    colorbar=dict(title="Correlação")
))
fig_corr.update_layout(
    title="Matriz de correlação sazonal entre grupos CID-10",
    height=600,
    xaxis=dict(tickangle=-45)
)
st.plotly_chart(fig_corr, use_container_width=True)

# Insight de correlação
corr_grupo = corr[grupo_sel].drop(grupo_sel).sort_values(ascending=False)
top_pos = corr_grupo.head(3)
top_neg = corr_grupo.tail(3)
col_i1, col_i2 = st.columns(2)
with col_i1:
    st.success(f"**{grupo_sel}** tem maior correlação sazonal com:\n\n" +
               "\n".join([f"- **{g}**: {v:.2f}" for g,v in top_pos.items()]))
with col_i2:
    st.warning(f"**{grupo_sel}** tem menor correlação (picos opostos) com:\n\n" +
               "\n".join([f"- **{g}**: {v:.2f}" for g,v in top_neg.items()]))
