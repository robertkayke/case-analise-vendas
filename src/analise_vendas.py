# Bibliotecas
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# LOCALIZAÇÃO DO DATASET (robusta e dinâmica)
# ─────────────────────────────────────────────
BASE_DIR = Path().resolve()

while not (BASE_DIR / "data").exists():
    if BASE_DIR == BASE_DIR.parent:
        raise FileNotFoundError("Pasta 'data/' não encontrada em nenhum diretório pai.")
    BASE_DIR = BASE_DIR.parent

DATA_PATH = BASE_DIR / "data" / "CASE_Vaga_SR.csv"

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Arquivo não encontrado: {DATA_PATH}")

# ─────────────────────────────────────────────
# LEITURA DOS DADOS
# ─────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, low_memory=False)

# Visualização das dimensões
print(f"\nDimensões do dataset: {df.shape[0]:,} linhas x {df.shape[1]} colunas")
print(f"Colunas: {list(df.columns)}\n")

# ─────────────────────────────────────────────
# TRATAMENTO DE DATAS (MANTER COMO DATETIME)
# ─────────────────────────────────────────────
df['mes_ref'] = pd.to_datetime(df['mes_ref'])
df['data_competencia'] = pd.to_datetime(df['data_competencia'])

# ─────────────────────────────────────────────
# VALIDAÇÃO DE SOBREPOSIÇÃO ENTRE RECEITAS
# ─────────────────────────────────────────────
print("=" * 60)
print("VALIDAÇÃO DE SOBREPOSIÇÃO ENTRE RECEITAS")
print("=" * 60)

validacao = (
    df.assign(
        fat_pos = df["Receita_faturada"] > 0,
        vend_pos = df["Receita_vendida"] > 0,
        ambas = (df["Receita_faturada"] > 0) & (df["Receita_vendida"] > 0)
    )
    .groupby("status_ordem_venda")
    .agg(
        fat=("fat_pos", "sum"),
        vend=("vend_pos", "sum"),
        ambas=("ambas", "sum")
    )
    .reindex(["FATURAMENTO", "VENDA", "DEVOLUÇÃO"])
    .fillna(0)
)

# Função para formatar números com separador de milhar
def fmt(n):
    return f"{int(n):,}".replace(",", ".")

print(f"\n{'Status':<15}{'Receita_faturada > 0':<28}{'Receita_vendida > 0':<28}{'Ambas > 0'}")
print("-" * 85)

for status, row in validacao.iterrows():
    fat = fmt(row["fat"])
    vend = fmt(row["vend"])
    ambas = fmt(row["ambas"])

    if status == "DEVOLUÇÃO" and row["ambas"] > 0:
        ambas = f"{ambas}  ← único overlap"

    print(f"{status:<15}{fat + ' linhas':<28}{vend + ' linhas':<28}{ambas}")

# ─────────────────────────────────────────────
# FILTRO DE FATURAMENTO + VENDA (EXCLUI DEVOLUÇÃO)
# ─────────────────────────────────────────────
df_fat = df[
    (df["status_ordem_venda"].isin(["FATURAMENTO", "VENDA"])) &
    (
        (df["Receita_faturada"] > 0) |
        (df["Receita_vendida"] > 0)
    )
].copy()

# ─────────────────────────────────────────────
# RECEITA E VOLUME CONSOLIDADOS (LÓGICA DEFENSIVA)
# ─────────────────────────────────────────────
# Receita_faturada e Receita_vendida são mutuamente exclusivas por status
df_fat["receita"] = df_fat["Receita_faturada"].where(
    df_fat["status_ordem_venda"] == "FATURAMENTO",
    df_fat["Receita_vendida"]
)

df_fat["volume"] = df_fat["Volume_faturado"].where(
    df_fat["status_ordem_venda"] == "FATURAMENTO",
    df_fat["Volume_vendido"]
)

print(f"\nLinhas após filtro de faturamento positivo: {df_fat.shape[0]:,}\n")

# ─────────────────────────────────────────────
# 2. RANKING DE PRODUTOS MAIS VENDIDOS
# ─────────────────────────────────────────────
# Objetivo: analisar os produtos sob três perspectivas:
# - Receita → impacto financeiro
# - Quantidade → demanda operacional
# - Ticket médio → valor agregado por unidade

print("=" * 60)
print("1. RANKING DE PRODUTOS MAIS VENDIDOS")
print("=" * 60)

# ─────────────────────────────────────────────
# FUNÇÕES DE FORMATAÇÃO (saída amigável)
# ─────────────────────────────────────────────
def fmt_moeda(n):
    return f"R$ {n:,.0f}".replace(",", ".")

def fmt_qtd(n):
    return f"{int(n):,}".replace(",", ".") + " un"

def fmt_ticket(n):
    return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ─────────────────────────────────────────────
# AGREGAÇÃO BASE
# ─────────────────────────────────────────────
ranking = (
    df_fat.groupby(["codigo_produto", "produto"])
    .agg(
        receita_total=("receita", "sum"),
        quantidade_total=("volume", "sum")
    )
    .reset_index()
)

# Ticket médio por produto
ranking["ticket_medio"] = ranking["receita_total"] / ranking["quantidade_total"]

print(f"Total de produtos únicos: {ranking.shape[0]:,}")

# ─────────────────────────────────────────────
# TOP PRODUTOS POR RECEITA (visão financeira)
# ─────────────────────────────────────────────
ranking_receita = (
    ranking
    .sort_values("receita_total", ascending=False)
    .reset_index(drop=True)
)

ranking_receita.index += 1

ranking_receita_fmt = ranking_receita.head(15).copy()
ranking_receita_fmt["receita_total"] = ranking_receita_fmt["receita_total"].apply(fmt_moeda)
ranking_receita_fmt["quantidade_total"] = ranking_receita_fmt["quantidade_total"].apply(fmt_qtd)
ranking_receita_fmt["ticket_medio"] = ranking_receita.head(15)["ticket_medio"].apply(fmt_ticket)

print("\n--- TOP 15 PRODUTOS POR RECEITA ---")
print(ranking_receita_fmt.to_string(index=True))

# ─────────────────────────────────────────────
# TOP PRODUTOS POR QUANTIDADE (visão operacional)
# ─────────────────────────────────────────────
ranking_quantidade = (
    ranking
    .sort_values("quantidade_total", ascending=False)
    .reset_index(drop=True)
)

ranking_quantidade.index += 1

ranking_quantidade_fmt = ranking_quantidade.head(15).copy()
ranking_quantidade_fmt["receita_total"] = ranking_quantidade_fmt["receita_total"].apply(fmt_moeda)
ranking_quantidade_fmt["quantidade_total"] = ranking_quantidade_fmt["quantidade_total"].apply(fmt_qtd)
ranking_quantidade_fmt["ticket_medio"] = ranking_quantidade.head(15)["ticket_medio"].apply(fmt_ticket)

print("\n--- TOP 15 PRODUTOS POR QUANTIDADE ---")
print(ranking_quantidade_fmt.to_string(index=True))