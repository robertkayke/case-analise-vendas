# Bibliotecas
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path().resolve()

while not (BASE_DIR / "data").exists():
    BASE_DIR = BASE_DIR.parent

DATA_PATH = BASE_DIR / "data" / "CASE_Vaga_SR.csv"

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Arquivo não encontrado: {DATA_PATH}")

df = pd.read_csv(DATA_PATH, low_memory=False)

# Visualização das Dimensões da base
print(f"\nDimensões do dataset: {df.shape[0]:,} linhas x {df.shape[1]} colunas")
print(f"Colunas: {list(df.columns)}\n")

# Converter datas
df['mes_ref'] = pd.to_datetime(df['mes_ref']).dt.strftime('%d/%m/%Y')
df['data_competencia'] = pd.to_datetime(df['data_competencia']).dt.strftime('%d/%m/%Y')
