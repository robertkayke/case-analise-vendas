# Análise de Dados de Vendas
Projeto de análise descritiva de dados de vendas de uma empresa fictícia, com foco em geração de insights de negócio a partir de dados transacionais.

## Objetivo
O objetivo deste projeto é analisar o desempenho de vendas e responder perguntas como:

* Quais são os produtos mais vendidos
* Qual o faturamento ao longo do tempo
* Qual o ticket médio por cliente
* Como se comportam categorias, canais e devoluções

## Estrutura do Projeto

case-analise-vendas/
├── src/
│   └── analise_vendas.py
├── notebooks/
│   └── CaseVendas.ipynb
├── data/
│   └── CASE_Vaga_SR.csv (não versionado)
├── .gitignore
└── README.md

## Como Executar

1. Clone o repositório

```
git clone https://github.com/robertkayke/case-analise-vendas.git
cd case-analise-vendas
```

2. Instale as dependências

```
pip install pandas
```

3. Adicione o dataset

Coloque o arquivo `CASE_Vaga_SR.csv` dentro da pasta `data/`.

Observação: o dataset não está versionado no repositório.

4. Execute o script

```
python src/analise_vendas.py
```

## Análises Realizadas

Validação de Dados
Verificação de sobreposição entre Receita_faturada e Receita_vendida, garantindo consistência e evitando dupla contagem.

Ranking de Produtos
Identificação dos principais produtos considerando três perspectivas: receita total, quantidade vendida e ticket médio.

Faturamento Mensal
Análise da evolução da receita ao longo do tempo, incluindo número de transações e identificação de sazonalidade.

Ticket Médio por Cliente
Análise em dois níveis: cliente_filho (visão operacional por filial) e cpf_cnpj (visão consolidada por empresa), considerando receita total, número de pedidos e ticket médio.

Top 10 Produtos por Categoria
Segmentação por categoria (Metais, Louças e Cerâmica) e identificação dos produtos com maior receita dentro de cada grupo.

Análises Extras
Faturamento por canal de venda, receita por empresa, cálculo da taxa de devolução e identificação de meses com maior e menor faturamento.

## Principais Decisões Técnicas

Tratamento de Receita
O dataset possui duas colunas de receita. Foi utilizada lógica condicional baseada no status da ordem para evitar dupla contagem.

Filtro de Dados
Foram considerados apenas registros com status FATURAMENTO ou VENDA e com valores positivos.

Devoluções
As devoluções foram excluídas da receita principal e analisadas separadamente para cálculo da taxa de devolução.

Leitura de Dados
Implementada lógica dinâmica para localizar a pasta data no projeto, permitindo execução em diferentes ambientes.

Formatação
Os valores monetários, quantidades e datas foram formatados para facilitar a interpretação dos resultados.

## Tecnologias Utilizadas

Python
pandas


## Versionamento

A branch main contém a versão base da análise.
A branch develop inclui evoluções adicionais, como análise por categoria.

Um Pull Request foi aberto da branch develop para a branch main conforme solicitado no case.

## Autor

Projeto desenvolvido por Robert Kayke como parte de processo seletivo para vaga de Analytics.
