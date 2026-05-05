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

# ─────────────────────────────────────────────
# 3. FATURAMENTO MENSAL
# ─────────────────────────────────────────────
# Objetivo: analisar evolução da receita ao longo do tempo
# Inclui volume de transações para contexto operacional

print("\n" + "=" * 60)
print("2. FATURAMENTO MENSAL")
print("=" * 60)

# ─────────────────────────────────────────────
# AGREGAÇÃO
# ─────────────────────────────────────────────
fat_mensal = (
    df_fat.groupby("mes_ref")
    .agg(
        receita_mensal=("receita", "sum"),
        transacoes=("receita", "count")
    )
    .reset_index()
    .sort_values("mes_ref")
)

# ─────────────────────────────────────────────
# FORMATAÇÃO
# ─────────────────────────────────────────────
def fmt_moeda(n):
    return f"R$ {n:,.0f}".replace(",", ".")

def fmt_int(n):
    return f"{int(n):,}".replace(",", ".")

# Formato de mês amigável (Jan/2025)
fat_mensal["mes"] = fat_mensal["mes_ref"].dt.strftime("%b/%Y")

# Ajuste para PT-BR (opcional mas bonito)
fat_mensal["mes"] = (
    fat_mensal["mes"]
    .str.replace("Jan", "Jan")
    .str.replace("Feb", "Fev")
    .str.replace("Mar", "Mar")
    .str.replace("Apr", "Abr")
    .str.replace("May", "Mai")
    .str.replace("Jun", "Jun")
    .str.replace("Jul", "Jul")
    .str.replace("Aug", "Ago")
    .str.replace("Sep", "Set")
    .str.replace("Oct", "Out")
    .str.replace("Nov", "Nov")
    .str.replace("Dec", "Dez")
)

# Aplicar formatação
fat_mensal_fmt = fat_mensal.copy()
fat_mensal_fmt["receita_mensal"] = fat_mensal_fmt["receita_mensal"].apply(fmt_moeda)
fat_mensal_fmt["transacoes"] = fat_mensal_fmt["transacoes"].apply(fmt_int)

print(fat_mensal_fmt[["mes", "receita_mensal", "transacoes"]].to_string(index=False))

# ─────────────────────────────────────────────
# TOTAL GERAL
# ─────────────────────────────────────────────
total_geral = fat_mensal["receita_mensal"].sum()

print(f"\nReceita Total Geral: {fmt_moeda(total_geral)}")

# ─────────────────────────────────────────────
# 4. TICKET MÉDIO POR CLIENTE (FILIAL vs EMPRESA)
# ─────────────────────────────────────────────
# Objetivo:
# - Analisar comportamento de compra em dois níveis:
#   • cliente_filho → visão operacional (filial)
#   • cpf_cnpj → visão consolidada (empresa)

print("\n" + "=" * 60)
print("3. TICKET MÉDIO POR CLIENTE")
print("=" * 60)

# ─────────────────────────────────────────────
# FUNÇÕES DE FORMATAÇÃO
# ─────────────────────────────────────────────
def fmt_moeda(n):
    return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_int(n):
    return f"{int(n):,}".replace(",", ".")

def fmt_cnpj(n):
    return f"{int(n)}"

# ─────────────────────────────────────────────
# 1. ANÁLISE POR FILIAL (cliente_filho)
# ─────────────────────────────────────────────
ticket_filial = (
    df_fat.groupby("cliente_filho")
    .agg(
        receita_total=("receita", "sum"),
        num_pedidos=("receita", "count")
    )
    .reset_index()
)

ticket_filial["ticket_medio"] = (
    ticket_filial["receita_total"] / ticket_filial["num_pedidos"]
)

print("\n--- ANÁLISE POR FILIAL (cliente_filho) ---")

print(f"Total de clientes (filiais): {fmt_int(ticket_filial.shape[0])}")
print(f"Ticket médio geral: {fmt_moeda(ticket_filial['ticket_medio'].mean())}")
print(f"Ticket mediano: {fmt_moeda(ticket_filial['ticket_medio'].median())}")

top_filial = (
    ticket_filial
    .sort_values("receita_total", ascending=False)
    .head(10)
    .copy()
)

top_filial["receita_total"] = top_filial["receita_total"].apply(fmt_moeda)
top_filial["num_pedidos"] = top_filial["num_pedidos"].apply(fmt_int)
top_filial["ticket_medio"] = top_filial["ticket_medio"].apply(fmt_moeda)

print("\nTop 10 filiais por receita:")
print(top_filial.to_string(index=False))

# ─────────────────────────────────────────────
# 2. ANÁLISE POR EMPRESA (cpf_cnpj)
# ─────────────────────────────────────────────
ticket_empresa = (
    df_fat.groupby("cpf_cnpj")
    .agg(
        receita_total=("receita", "sum"),
        num_pedidos=("receita", "count")
    )
    .reset_index()
)

ticket_empresa["ticket_medio"] = (
    ticket_empresa["receita_total"] / ticket_empresa["num_pedidos"]
)

print("\n--- ANÁLISE POR EMPRESA (cpf_cnpj) ---")

print(f"Total de clientes (empresas): {fmt_int(ticket_empresa.shape[0])}")
print(f"Ticket médio geral: {fmt_moeda(ticket_empresa['ticket_medio'].mean())}")
print(f"Ticket mediano: {fmt_moeda(ticket_empresa['ticket_medio'].median())}")

top_empresa = (
    ticket_empresa
    .sort_values("receita_total", ascending=False)
    .head(10)
    .copy()
)

top_empresa["cpf_cnpj"] = top_empresa["cpf_cnpj"].apply(fmt_cnpj)
top_empresa["receita_total"] = top_empresa["receita_total"].apply(fmt_moeda)
top_empresa["num_pedidos"] = top_empresa["num_pedidos"].apply(fmt_int)
top_empresa["ticket_medio"] = top_empresa["ticket_medio"].apply(fmt_moeda)

print("\nTop 10 empresas por receita:")
print(top_empresa.to_string(index=False))

# ─────────────────────────────────────────────
# 5. TOP 10 PRODUTOS POR CATEGORIA
# ─────────────────────────────────────────────
# Objetivo:
# - Analisar performance de produtos por categoria
# - Comparar comportamento entre Metais, Louças e Cerâmica

print("\n" + "=" * 60)
print("4. TOP 10 PRODUTOS POR CATEGORIA (METAIS / LOUÇAS / CERÂMICA)")
print("=" * 60)

# ─────────────────────────────────────────────
# FUNÇÕES DE FORMATAÇÃO
# ─────────────────────────────────────────────
def fmt_moeda(n):
    return f"R$ {n:,.0f}".replace(",", ".")

def fmt_qtd(n):
    return f"{int(n):,}".replace(",", ".") + " un"

# ─────────────────────────────────────────────
# MAPEAMENTO DE CATEGORIA
# ─────────────────────────────────────────────
categoria_map = {
    "METAIS": "Metais",
    "LOUÇAS": "Louças",
    "PORTINARI": "Cerâmica",
    "CEUSA": "Cerâmica",
}

df_fat["categoria"] = df_fat["fabrica"].map(categoria_map).fillna(df_fat["fabrica"])

# ─────────────────────────────────────────────
# AGREGAÇÃO
# ─────────────────────────────────────────────
top10_cat = (
    df_fat.groupby(["categoria", "codigo_produto", "produto"])
    .agg(
        receita_total=("receita", "sum"),
        volume_total=("volume", "sum")
    )
    .reset_index()
)

# ─────────────────────────────────────────────
# EXIBIÇÃO FORMATADA
# ─────────────────────────────────────────────
for cat in ["Metais", "Louças", "Cerâmica"]:
    sub = (
        top10_cat[top10_cat["categoria"] == cat]
        .sort_values("receita_total", ascending=False)
        .head(10)
        .reset_index(drop=True)
        .copy()
    )

    sub.index += 1

    # aplicar formatação
    sub["receita_total"] = sub["receita_total"].apply(fmt_moeda)
    sub["volume_total"] = sub["volume_total"].apply(fmt_qtd)

    print(f"\n--- {cat} ---")
    print(sub[["produto", "receita_total", "volume_total"]].to_string(index=True))
 