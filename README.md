# Sistema de Pesquisa NPS

## Visão Geral
Aplicação web para coleta e análise de Net Promoter Score (NPS), com persistência em SQLite e preparação dos dados para análise via pandas.

## Arquitetura

- Backend: Flask
- Banco de Dados: SQLite
- Análise de Dados: pandas
- Dashboard: Plotly / Dash

## Modelo Relacional

Tabela identificacao
- id (PK)
- nome_completo
- cnpj
- nome_empresa
- created_at

Tabela respostas_nps
- id (PK)
- identificacao_id (FK)
- nps_nota
- qualidade_produto
- atendimento
- prazo_entrega
- custo_beneficio
- facilidade_negociacao
- satisfacao_geral
- created_at

## Como Executar

1. Criar ambiente virtual
2. Instalar dependências
3. Executar run.py
