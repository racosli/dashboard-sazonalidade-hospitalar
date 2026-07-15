# Dashboard de Sazonalidade Hospitalar — SIH/DATASUS 2016–2026

Análise estatística avançada de padrões sazonais de internações hospitalares
no Brasil usando dados reais do SIH/DATASUS — 129 milhões de AIH aprovadas
ao longo de 11 anos e 21 capítulos CID-10.

## Demo ao vivo

👉 [Acessar o dashboard](https://dashboard-sazonalidade-hospitalar-knesxvgih3sd8bryrudehf.streamlit.app/)

## Funcionalidades

- **Decomposição de sazonalidade** — separação estatística entre tendência
  (média móvel 12 meses) e componente sazonal com índice mensal
- **Detecção automática de anomalias** — Z-score ±2σ com baseline 2016–2019,
  identificando automaticamente o impacto da COVID-19
- **CAGR por grupo CID-10** — taxa de crescimento anual composta 2016→2024
  com regressão linear e intervalo de confiança de 95%
- **Radar comparativo** — visualização do perfil sazonal de múltiplos grupos
  CID-10 simultaneamente
- **Matriz de correlação sazonal** — identifica quais grupos têm picos nos
  mesmos meses e quais têm sazonalidade oposta
- **Perfil sazonal por ano** — comparativo de cada ano contra a média histórica
  com destaque para anos anômalos (2020)

## Dados

| Fonte | SIH/SUS — TabNet/DATASUS |
|---|---|
| Período | 2016 a 2026 (2026 parcial) |
| Total de AIH | 129 milhões |
| Grupos CID-10 | 21 capítulos |
| Anos analisados | 11 |

Dados baixados diretamente do portal TabNet do Ministério da Saúde:
```
http://tabnet.datasus.gov.br/cgi/tabcgi.exe?sih/cnv/niuf.def
```

## Tecnologias

- **Python** — linguagem principal
- **Streamlit** — framework do dashboard web
- **pandas** — manipulação e análise dos dados
- **Plotly** — gráficos interativos
- **NumPy** — cálculos estatísticos (médias móveis, regressão, Z-score)

## Como executar localmente

```bash
# Clonar o repositório
git clone https://github.com/racosli/dashboard-sazonalidade-hospitalar.git
cd dashboard-sazonalidade-hospitalar

# Instalar dependências
pip install -r requirements.txt

# Rodar o dashboard
streamlit run app.py
```

## Estrutura do projeto

```
dashboard-sazonalidade-hospitalar/
├── app.py                    ← código principal do dashboard
├── requirements.txt          ← dependências
├── dados/
│   └── tabnet_10anos.csv     ← dados consolidados 2016–2026
└── README.md
```

## Principais achados

- Doenças **respiratórias** apresentam pico no inverno (Jun–Ago) com
  amplitude sazonal superior a 40 pontos percentuais
- O ano de **2020** foi detectado automaticamente como anomalia em todos
  os grupos, com queda média de 14% nas internações
- Grupos **Materno/Perinatal** e **Congênito** apresentam menor variação
  sazonal — padrão esperado clinicamente
- **Cardiovascular** e **Respiratório** têm alta correlação sazonal —
  ambos com picos no período frio
- A série 2022–2025 mostra **recuperação acelerada** pós-pandemia com
  CAGR acima da tendência histórica

## Autor

**Rafael** — Farmacêutico em transição para Ciência de Dados em Saúde

[![GitHub](https://img.shields.io/badge/GitHub-racosli-black?logo=github)](https://github.com/racosli)
