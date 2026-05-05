# ==============================================================================
# Construção dos Indicadores Financeiros — via Base dos Dados (BigQuery)
# Dissertação: Digitalização do Sistema Financeiro Brasileiro
# Autor: Flávio Hugo Pangracio Silva
# ==============================================================================
# Versão alternativa do construir_indicadores.R que utiliza as tabelas públicas
# do Base dos Dados em vez da tabela customizada (estban_agencias_geolocalizadas).
#
# Tabelas utilizadas:
#   - basedosdados.br_bcb_estban.municipio  → indicadores agregados por município
#   - basedosdados.br_bcb_estban.agencia    → contagem de agências e ICB
#   - PIB municipal: data/raw/ (planilhas IBGE 2002-2009 e 2010-2023)
#
# Período: dezembro de 2009 a dezembro de 2024
# ==============================================================================

# --- Pacotes ------------------------------------------------------------------

pacotes_necessarios <- c("bigrquery", "readxl", "dplyr", "tidyr", "janitor")
pacotes_faltantes <- pacotes_necessarios[
  !pacotes_necessarios %in% installed.packages()[, "Package"]
]
if (length(pacotes_faltantes) > 0) {
  install.packages(pacotes_faltantes)
}

library(bigrquery)
library(readxl)
library(dplyr)
library(tidyr)
library(janitor)

# --- Configuração BigQuery ----------------------------------------------------

project_id <- "cloud-learning-doing"
bq_auth()

# --- 1. Leitura dos dados de PIB municipal ------------------------------------

cat(">>> Lendo dados de PIB municipal e VAB setorial...\n")

ler_pib <- function(arquivo) {
  read_excel(arquivo) |>
    janitor::clean_names() |>
    dplyr::transmute(
      cod_mun_ibge = as.character(codigo_do_municipio),
      ano          = as.integer(ano),
      pib          = as.double(produto_interno_bruto_a_precos_correntes_r_1_000),
      vab_total    = as.double(valor_adicionado_bruto_total_a_precos_correntes_r_1_000),
      vab_agro     = as.double(valor_adicionado_bruto_da_agropecuaria_a_precos_correntes_r_1_000),
      vab_ind      = as.double(valor_adicionado_bruto_da_industria_a_precos_correntes_r_1_000),
      vab_serv     = as.double(valor_adicionado_bruto_dos_servicos_a_precos_correntes_exceto_administracao_defesa_educacao_e_saude_publicas_e_seguridade_social_r_1_000),
      vab_apu      = as.double(valor_adicionado_bruto_da_administracao_defesa_educacao_e_saude_publicas_e_seguridade_social_a_precos_correntes_r_1_000),
      impostos     = as.double(impostos_liquidos_de_subsidios_sobre_produtos_a_precos_correntes_r_1_000)
    )
}

pib_antigo  <- ler_pib("data/raw/pib_municipios_2002-2009.xlsx")
pib_recente <- ler_pib("data/raw/pib_municipios_2010-2023.xlsx")

pib <- bind_rows(pib_antigo, pib_recente) |>
  distinct(cod_mun_ibge, ano, .keep_all = TRUE) |>
  filter(ano >= 2009)

classificacoes <- read_excel(
  "data/raw/pib_municipios_2010-2023.xlsx"
) |>
  janitor::clean_names() |>
  dplyr::transmute(
    cod_mun_ibge        = as.character(codigo_do_municipio),
    nome_municipio      = nome_do_municipio,
    sigla_uf            = sigla_da_unidade_da_federacao,
    cod_mesorregiao     = as.character(codigo_da_mesorregiao),
    cod_microrregiao    = as.character(codigo_da_microrregiao),
    regiao_metropolitana,
    hierarquia_urbana,
    semiarido,
    amazonia_legal
  ) |>
  distinct(cod_mun_ibge, .keep_all = TRUE)

cat(
  "   PIB:", nrow(pib), "registros, anos",
  min(pib$ano), "-", max(pib$ano), "\n",
  "  Classificações territoriais:", nrow(classificacoes), "municípios\n"
)

# --- 2. ESTBAN — Tabela de municípios (Base dos Dados) ------------------------

cat(">>> Consultando ESTBAN (tabela de municípios) no BigQuery...\n")

sql_municipio <- "
SELECT
  id_municipio,
  CAST(ano AS INT64) AS ano,
  CASE
    WHEN id_verbete = '401402403404411412413414415416417418419'
      THEN 'depositos'
    WHEN id_verbete = '420' THEN 'poupanca'
    WHEN id_verbete = '430' THEN 'depositos_inter'
    WHEN id_verbete = '160' THEN 'op_cred'
    WHEN id_verbete = '161' THEN 'emprestimos'
    WHEN id_verbete = '162' THEN 'fin'
    WHEN id_verbete = '163' THEN 'fin_agricultura_inv'
    WHEN id_verbete = '167' THEN 'fin_agroindustrial'
    WHEN id_verbete = '169' THEN 'fin_imobiliarios'
    WHEN id_verbete = '172' THEN 'outras_op_cred'
    WHEN id_verbete = '174' THEN 'provisao_de_credito'
    WHEN id_verbete = '180' THEN 'arr_mercantil'
    WHEN id_verbete = '184' THEN 'provisao_arr_mercantil'
    WHEN id_verbete = '399' THEN 'ativos'
    WHEN id_verbete = '444445446447456458'
      THEN 'relacoes_interfinanceiras'
    WHEN id_verbete = '710' THEN 'resultado'
    WHEN id_verbete = '110' THEN 'disponibilidades'
  END AS conta,
  SUM(valor) AS valor
FROM `basedosdados.br_bcb_estban.municipio`
WHERE mes = 12
  AND ano >= 2009
  AND id_municipio IS NOT NULL
  AND id_verbete IN (
    '110','160','161','162','163','167','169',
    '172','174','180','184','399',
    '401402403404411412413414415416417418419',
    '420','430','444445446447456458','710'
  )
GROUP BY id_municipio, ano, conta
"

estban_mun_long <- bq_project_query(project_id, sql_municipio) |>
  bq_table_download()

cat("   ESTBAN municípios:", nrow(estban_mun_long), "registros (long)\n")


# Pivotar para formato wide (uma coluna por conta)
estban_mun <- estban_mun_long |>
  pivot_wider(
    id_cols     = c(id_municipio, ano),
    names_from  = conta,
    values_from = valor,
    values_fill = 0
  ) |>
  dplyr::rename(cod_mun_ibge = id_municipio) |>
  dplyr::mutate(
    ano = as.integer(ano),
    DT  = depositos + depositos_inter + poupanca
  )

cat("   ESTBAN municípios:", nrow(estban_mun), "registros (wide)\n")

# --- 3. ESTBAN — Tabela de agências (contagem + ICB) -------------------------

cat(">>> Consultando ESTBAN (tabela de agências) no BigQuery...\n")

sql_agencias <- "
SELECT
  id_municipio,
  CAST(ano AS INT64) AS ano,
  cnpj_basico,
  COUNT(DISTINCT cnpj_agencia) AS n_agencias_banco,
  SUM(CASE WHEN id_verbete = '160' THEN valor ELSE 0 END) AS credito
FROM `basedosdados.br_bcb_estban.agencia`
WHERE mes = 12
  AND ano >= 2009
  AND id_municipio IS NOT NULL
GROUP BY id_municipio, ano, cnpj_basico
"

agencias_raw <- bq_project_query(project_id, sql_agencias) |>
  bq_table_download()

cat("   ESTBAN agências:", nrow(agencias_raw), "registros (banco × município × ano)\n")

# 3a. Contagem de agências por município-ano
agencias_mun <- agencias_raw |>
  group_by(cod_mun_ibge = id_municipio, ano = as.integer(ano)) |>
  summarise(n_agencias = sum(n_agencias_banco), .groups = "drop")

cat("   Agências:", nrow(agencias_mun), "registros município-ano\n")

# 3b. ICB (Índice de Concentração Bancária) — HHI por instituição
# ICB_j = Σ (credito_banco_ij / credito_total_j)²
icb <- agencias_raw |>
  group_by(cod_mun_ibge = id_municipio, ano = as.integer(ano)) |>
  mutate(
    credito_total = sum(credito),
    share = if_else(credito_total > 0, credito / credito_total, 0)
  ) |>
  summarise(ICB = sum(share^2), .groups = "drop") |>
  mutate(ICB = if_else(ICB == 0, NA_real_, ICB))

# --- 4. PLP e PLB -------------------------------------------------------------

cat(">>> Calculando PLP e PLB...\n")

estban_mun <- estban_mun |>
  mutate(
    PLP = if_else(DT > 0, depositos / DT, 0),
    PLB = if_else(op_cred > 0, depositos / op_cred, 0)
  )

# --- 5. Índices Regionais (quociente locacional) ------------------------------

cat(">>> Calculando índices regionais (IRC, IRE, IRF, IRD, IRL, IRR)...\n")

indicadores_mun <- pib |>
  left_join(estban_mun, by = c("cod_mun_ibge", "ano")) |>
  left_join(agencias_mun, by = c("cod_mun_ibge", "ano")) |>
  mutate(n_agencias = replace_na(n_agencias, 0L))

n_sem_pib <- sum(is.na(indicadores_mun$pib))
if (n_sem_pib > 0) {
  cat("   AVISO:", n_sem_pib, "registros sem PIB correspondente\n")
}

# Totais nacionais por ano
totais_nacionais <- indicadores_mun |>
  group_by(ano) |>
  summarise(
    OPC_total = sum(ifelse(is.na(op_cred), 0, op_cred)),
    E_total   = sum(ifelse(is.na(emprestimos), 0, emprestimos)),
    F_total   = sum(ifelse(is.na(fin), 0, fin)),
    DV_total  = sum(ifelse(is.na(depositos), 0, depositos)),
    L_total   = sum(ifelse(is.na(resultado), 0, resultado)),
    PC_total  = sum(ifelse(is.na(provisao_de_credito), 0, provisao_de_credito)),
    PIB_total = sum(ifelse(is.na(pib), 0, pib)),
    .groups   = "drop"
  )

indicadores_mun <- indicadores_mun |>
  left_join(totais_nacionais, by = "ano") |>
  mutate(
    pib_share = pib / PIB_total,
    IRC = if_else(pib_share > 0, (op_cred / OPC_total) / pib_share, NA_real_),
    IRE = if_else(pib_share > 0, (emprestimos / E_total) / pib_share, NA_real_),
    IRF = if_else(pib_share > 0, (fin / F_total) / pib_share, NA_real_),
    IRD = if_else(pib_share > 0, (depositos / DV_total) / pib_share, NA_real_),
    IRL = if_else(pib_share > 0, (resultado / L_total) / pib_share, NA_real_),
    IRR = if_else(pib_share > 0, (provisao_de_credito / PC_total) / pib_share, NA_real_)
  ) |>
  select(-OPC_total, -E_total, -F_total, -DV_total, -L_total, -PC_total, -PIB_total, -pib_share)

# --- 6. ICO (Índice de Concentração de Operações) -----------------------------

cat(">>> Calculando ICO (HHI por tipo de operação de crédito)...\n")

colunas_sub_credito <- c(
  "emprestimos", "fin", "fin_agricultura_inv",
  "fin_agroindustrial", "fin_imobiliarios", "outras_op_cred"
)

indicadores_mun <- indicadores_mun |>
  rowwise() |>
  mutate(
    ICO = if_else(
      op_cred > 0,
      sum((c_across(all_of(colunas_sub_credito)) / op_cred)^2),
      NA_real_
    )
  ) |>
  ungroup()

# --- 7. Juntar ICB ------------------------------------------------------------

cat(">>> Juntando ICB...\n")

indicadores_mun <- indicadores_mun |>
  left_join(icb, by = c("cod_mun_ibge", "ano"))

# --- 7b. RAIS — Mercado de trabalho formal (estabelecimentos) ----------------
cat(">>> Consultando RAIS (estabelecimentos) no BigQuery...\n")
cat("   ATENÇÃO: query pesada, pode levar vários minutos\n")

sql_rais <- "
SELECT
  id_municipio,
  CAST(ano AS INT64) AS ano,
  SUM(CAST(quantidade_vinculos_ativos AS INT64)) AS vinculos_total,
  SUM(CAST(quantidade_vinculos_clt    AS INT64)) AS vinculos_clt,
  COUNT(*) AS estabelecimentos_total,
  SUM(CASE WHEN indicador_atividade_ano = 1 THEN 1 ELSE 0 END) AS estab_ativos,
  SUM(CASE WHEN CAST(indicador_simples AS INT64) = 1 THEN 1 ELSE 0 END) AS estab_simples,
  SUM(CASE WHEN subsetor_ibge IN ('1','2','3','4','5','6','7','8','9','10','11','12','13')
           THEN CAST(quantidade_vinculos_ativos AS INT64) ELSE 0 END) AS vinculos_industria,
  SUM(CASE WHEN subsetor_ibge IN ('14','15','16','17','18','19','20','21','22','23')
           THEN CAST(quantidade_vinculos_ativos AS INT64) ELSE 0 END) AS vinculos_servicos,
  SUM(CASE WHEN subsetor_ibge = '25'
           THEN CAST(quantidade_vinculos_ativos AS INT64) ELSE 0 END) AS vinculos_agro,
  SUM(CASE WHEN subsetor_ibge = '24'
           THEN CAST(quantidade_vinculos_ativos AS INT64) ELSE 0 END) AS vinculos_publico
FROM `basedosdados.br_me_rais.microdados_estabelecimentos`
WHERE ano >= 2009
  AND id_municipio IS NOT NULL
GROUP BY id_municipio, ano
"

rais <- bq_project_query(project_id, sql_rais) |>
  bq_table_download()

rais <- rais |>
  dplyr::rename(cod_mun_ibge = id_municipio) |>
  dplyr::mutate(
    cod_mun_ibge = as.character(cod_mun_ibge),
    ano          = as.integer(ano)
  )

cat("   RAIS:", nrow(rais), "registros município-ano,",
    n_distinct(rais$cod_mun_ibge), "municípios\n")

indicadores_mun <- indicadores_mun |>
  left_join(rais, by = c("cod_mun_ibge", "ano"))

# --- 8. Resultado final -------------------------------------------------------

cat(">>> Selecionando colunas finais...\n")

resultado <- indicadores_mun |>
  select(
    cod_mun_ibge, ano,
    # Bancário
    pib, n_agencias,
    depositos, DT, op_cred, emprestimos, fin, resultado, provisao_de_credito,
    PLP, PLB,
    IRC, IRE, IRF, IRD, IRL, IRR,
    ICO, ICB,
    # Real (PIB municipal IBGE)
    vab_total, vab_agro, vab_ind, vab_serv, vab_apu, impostos,
    # Mercado de trabalho formal (RAIS)
    vinculos_total, vinculos_clt,
    estabelecimentos_total, estab_ativos, estab_simples,
    vinculos_industria, vinculos_servicos, vinculos_agro, vinculos_publico
  ) |>
  arrange(cod_mun_ibge, ano)

# --- 8b. Deflacionar PIB e VABs (IPCA, base = 2024) --------------------------

cat(">>> Deflacionando PIB e VABs pelo IPCA (base = 2024)...\n")

# IPCA acumulado no ano (% dez/dez), fonte: IBGE/SIDRA tabela 1737
ipca_anual <- tibble::tribble(
  ~ano, ~ipca_pct,
  2009,  4.31,
  2010,  5.91,
  2011,  6.50,
  2012,  5.84,
  2013,  5.91,
  2014,  6.41,
  2015, 10.67,
  2016,  6.29,
  2017,  2.95,
  2018,  3.75,
  2019,  4.31,
  2020,  4.52,
  2021, 10.06,
  2022,  5.79,
  2023,  4.62,
  2024,  4.83
)

# Índice acumulado (base 2024 = 1.00)
ipca_anual <- ipca_anual |>
  mutate(
    fator       = cumprod(1 + ipca_pct / 100),
    indice_2024 = fator / fator[ano == 2024]
  ) |>
  select(ano, indice_2024)

resultado <- resultado |>
  left_join(ipca_anual, by = "ano") |>
  mutate(
    pib_real       = pib       / indice_2024,
    vab_total_real = vab_total / indice_2024,
    vab_agro_real  = vab_agro  / indice_2024,
    vab_ind_real   = vab_ind   / indice_2024,
    vab_serv_real  = vab_serv  / indice_2024,
    vab_apu_real   = vab_apu   / indice_2024,
    impostos_real  = impostos  / indice_2024,
    ano            = as.integer(ano)
  ) |>
  select(-indice_2024)

# --- 8c. Composição setorial (shares) e taxa de formalização -----------------

cat(">>> Calculando shares setoriais e taxa de formalização...\n")

resultado <- resultado |>
  mutate(
    share_agro  = if_else(vab_total > 0, vab_agro  / vab_total, NA_real_),
    share_ind   = if_else(vab_total > 0, vab_ind   / vab_total, NA_real_),
    share_serv  = if_else(vab_total > 0, vab_serv  / vab_total, NA_real_),
    share_apu   = if_else(vab_total > 0, vab_apu   / vab_total, NA_real_),
    # Vínculos formais por mil habitantes do PIB (proxy de adensamento de
    # mercado de trabalho); razão entre estabelecimentos optantes do SIMPLES
    # e estabelecimentos ativos (proxy de fragmentação produtiva).
    estab_simples_share = if_else(estab_ativos > 0, estab_simples / estab_ativos, NA_real_)
  )

# --- 8d. Junção com classificações territoriais ------------------------------

resultado <- resultado |>
  left_join(classificacoes, by = "cod_mun_ibge")

# --- 9. Exportar --------------------------------------------------------------

dir.create("data/processed", showWarnings = FALSE, recursive = TRUE)

output_path <- "data/processed/indicadores_financeiros_basedosdados.csv"
write.csv(resultado, output_path, row.names = FALSE)

cat("\n=== Concluído! ===\n")
cat("Arquivo salvo em:", output_path, "\n")
cat("Dimensões:", nrow(resultado), "linhas x", ncol(resultado), "colunas\n")
cat("Anos:", paste(sort(unique(resultado$ano)), collapse = ", "), "\n")
cat("Municípios:", n_distinct(resultado$cod_mun_ibge), "\n")

# --- Resumo estatístico dos indicadores ---------------------------------------

cat("\n--- Resumo dos indicadores bancários ---\n")
resultado |>
  select(n_agencias, PLP, PLB, IRC, IRE, IRF, IRD, IRL, IRR, ICO, ICB) |>
  summary() |>
  print()

cat("\n--- Resumo dos indicadores reais ---\n")
resultado |>
  select(pib_real, vab_total_real, share_agro, share_ind, share_serv, share_apu) |>
  summary() |>
  print()

cat("\n--- Resumo do mercado de trabalho formal (RAIS) ---\n")
resultado |>
  select(vinculos_total, vinculos_clt, estabelecimentos_total,
         estab_simples_share,
         vinculos_industria, vinculos_servicos, vinculos_agro, vinculos_publico) |>
  summary() |>
  print()
