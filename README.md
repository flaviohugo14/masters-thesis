# Digitalização Bancária e Assimetrias Regionais no Brasil

Dissertação de mestrado em Economia (CEDEPLAR/UFMG). Analisa a reconfiguração das redes de agências, qualidade do crédito e deslocamento espacial induzidos pela digitalização do sistema financeiro brasileiro entre 2009 e 2023.

- **Autor:** Flávio Hugo Pangracio Silva
- **Orientador:** Prof. Dr. Marco Aurélio Crocco Afonso
- **Defesa:** 03/08/2026

## Estrutura

```
.
├── thesis/              # Fontes da dissertação (Quarto + LaTeX)
│   ├── index.qmd        # Documento principal
│   ├── tex/             # Templates LaTeX (classe ABNT, capa)
│   ├── csl/abnt.csl     # Estilo de citação ABNT
│   ├── references/      # Bibliografia BibTeX
│   └── images/          # Figuras estáticas
├── presentation/        # Slides de defesa (Beamer)
├── R/                   # Pipeline reprodutível
│   ├── 01_construir_indicadores.R         # ESTBAN (Base dos Dados) + IBGE → indicadores
│   ├── 02_mediacao.R                      # Mediação causal (Imai-Keele-Tingley)
│   ├── 03_robustez.R                      # Placebo, DiD sintético, W alternativos
│   └── 04_quantilica.R                    # Quantílica espacial (Canay 2011)
├── data/
│   ├── raw/             # Fontes originais (PIB IBGE, FEBRABAN)
│   ├── processed/       # Indicadores municipais (saída de R/01_*)
│   └── cache/           # Resultados intermediários (.rds)
└── renv.lock            # Versões pinadas das dependências R
```

## Replicação

### Pré-requisitos

- R ≥ 4.3 (testado em 4.5.2)
- Quarto ≥ 1.4
- Conta no Google Cloud com acesso a BigQuery (apenas para reconstruir indicadores do zero)

### Setup

```bash
# Restaurar dependências R (a partir de renv.lock)
Rscript -e "renv::restore()"
```

### Renderização

```bash
# A partir da raiz do projeto:
quarto render thesis/index.qmd
# Saída: thesis/index.pdf
```

> `_quarto.yml` define `execute-dir: project`, então paths em chunks R são relativos à raiz do repositório.

### Pipeline de dados

Os arquivos em `data/processed/` e `data/cache/` já vêm gerados (não versionados) para permitir renderização imediata. Para reconstruir:

```bash
# 1. Indicadores municipais (PLP, PLB, ICO, ICB, IRC, IRE, IRF, IRD, IRL, IRR)
Rscript R/01_construir_indicadores.R

# 2-4. Caches de análise (rodar após indicadores prontos)
Rscript R/02_mediacao.R
Rscript R/03_robustez.R
Rscript R/04_quantilica.R
```

`R/01_construir_indicadores.R` consulta ESTBAN via Base dos Dados/OSF/BigQuery e cruza com PIB municipal do IBGE (planilhas em `data/raw/`). Requer autenticação `bigrquery`.

## Fontes de dados

- **ESTBAN** (estatística bancária por município) — Base dos Dados / OSF / BigQuery, 2009–2023
- **IBGE** — PIB municipal a preços correntes, deflacionado por IPCA (base 2021)
- **FEBRABAN** — Pesquisa anual de tecnologia bancária, 2009–2024 (`data/raw/febraban2009_2024.csv`)
- **geobr** — malha municipal IBGE 2020 para análise espacial

## Contato

Email: flaviohugo.14@gmail.com
GitHub: https://github.com/flaviohugo14
Orcid: https://orcid.org/0000-0003-4045-101X
Linkedin: https://www.linkedin.com/in/flaviopangracio/

## Licença

MIT — ver `LICENSE`.
