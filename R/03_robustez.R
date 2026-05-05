#!/usr/bin/env Rscript
# 07_robustez.R
# Robustez do DiD principal:
#   (i)  Placebo com t* falso em 2014 (sub-amostra 2009-2018)
#   (ii) Synthetic DiD (Arkhangelsky et al. 2021) sobre tratado vs controle
#        binarizados (tercis extremos do escore de exposição)
#   (iii) SLX-DiD com matrizes W alternativas (k=5 vizinhos mais próximos
#         e distância inversa) sobre os mesmos desfechos da §3.5
#
# Saída: data/cache/robustez.rds

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(fixest)
  library(Matrix)
  library(synthdid)
  library(spdep)
  library(sf)
  library(geobr)
})

set.seed(20260427)

# ---- 1. Painel e exposição ----
ind <- read.csv("data/processed/indicadores_financeiros_basedosdados.csv")

pre_2013 <- ind |>
  filter(ano >= 2009, ano <= 2013, !is.na(n_agencias), n_agencias > 0)

cobertura <- pre_2013 |>
  group_by(cod_mun_ibge) |>
  summarise(
    ag_per_pib = mean(n_agencias / pmax(pib_real / 1e6, 1), na.rm = TRUE),
    ICB        = mean(ICB, na.rm = TRUE),
    PLP        = mean(PLP, na.rm = TRUE),
    IRC        = mean(IRC, na.rm = TRUE),
    ln_pib     = mean(log(pmax(pib_real, 1)), na.rm = TRUE),
    .groups    = "drop"
  ) |>
  filter(if_all(everything(), is.finite))

X <- cobertura |>
  transmute(ag_per_pib, ICB, PLP, neg_IRC = -IRC, neg_ln_pib = -ln_pib) |>
  scale()
pca_exp <- prcomp(X, center = FALSE, scale. = FALSE)
cobertura$Exposicao <- as.numeric(pca_exp$x[, 1])
if (mean(cobertura$Exposicao[cobertura$ICB > median(cobertura$ICB)]) <
    mean(cobertura$Exposicao[cobertura$ICB < median(cobertura$ICB)])) {
  cobertura$Exposicao <- -cobertura$Exposicao
}

painel <- ind |>
  filter(ano >= 2009, ano <= 2023) |>
  inner_join(cobertura |> select(cod_mun_ibge, Exposicao), by = "cod_mun_ibge") |>
  mutate(
    ln_pib  = log(pmax(pib_real, 1)),
    ln_nag  = log(pmax(n_agencias, 0) + 1),
    IRF_IRE = ifelse(IRE > 0, IRF / IRE, NA_real_)
  )

painel_ag <- painel |> filter(ano <= 2022)

outcomes <- list(ln_nag = "ln_nag", IRC = "IRC", ICO = "ICO", IRF_IRE = "IRF_IRE")

# =============================================================================
# (i) PLACEBO — t* falso em 2014
# =============================================================================
cat("\n===== PLACEBO t*=2014 (amostra 2009-2018) =====\n")

painel_placebo <- painel |>
  filter(ano >= 2009, ano <= 2018) |>
  mutate(Post_fake = as.integer(ano >= 2014))

painel_placebo_ag <- painel_placebo |> filter(ano <= 2018)  # idêntico, sem corte 2022

placebo_res <- list()
for (nm in names(outcomes)) {
  yv <- outcomes[[nm]]
  d <- if (yv == "ln_nag") painel_placebo_ag else painel_placebo
  d <- d |> filter(!is.na(.data[[yv]]), is.finite(.data[[yv]]))
  m <- feols(as.formula(paste0(yv, " ~ I(Post_fake*Exposicao) + ln_pib | cod_mun_ibge + ano")),
             data = d, cluster = ~ cod_mun_ibge, warn = FALSE, notes = FALSE)
  placebo_res[[nm]] <- list(
    est = coef(m)["I(Post_fake * Exposicao)"],
    se  = sqrt(vcov(m)["I(Post_fake * Exposicao)", "I(Post_fake * Exposicao)"]),
    n   = nobs(m)
  )
  cat(sprintf("  %-10s coef = %+.5f (SE %.5f) N=%d\n",
              nm, placebo_res[[nm]]$est, placebo_res[[nm]]$se, placebo_res[[nm]]$n))
}

# =============================================================================
# (ii) SYNTHETIC DiD — tratamento binário (tercil superior vs inferior de E_i)
# =============================================================================
cat("\n===== SYNTHETIC DiD =====\n")

q <- quantile(cobertura$Exposicao, c(1/3, 2/3))
cobertura <- cobertura |>
  mutate(grupo_sd = case_when(
    Exposicao >= q[2] ~ "tratado",
    Exposicao <= q[1] ~ "controle",
    TRUE              ~ NA_character_
  ))

painel_sd <- painel_ag |>
  inner_join(cobertura |> select(cod_mun_ibge, grupo_sd), by = "cod_mun_ibge") |>
  filter(!is.na(grupo_sd)) |>
  mutate(treat_post = as.integer(grupo_sd == "tratado" & ano >= 2020))

# synthdid exige painel balanceado: município × ano sem buracos
# Para cada outcome, montamos a matriz Y, filtramos munis com observações
# completas em todos os anos da janela, e aplicamos synthdid_estimate.

executar_sdid <- function(yvar, painel_in, t_pre = 2014:2019, t_pos = 2020:2022) {
  anos <- c(t_pre, t_pos)
  d <- painel_in |>
    filter(ano %in% anos, !is.na(.data[[yvar]]), is.finite(.data[[yvar]])) |>
    select(cod_mun_ibge, ano, all_of(yvar), grupo_sd, treat_post)

  # Manter apenas munis com painel completo
  cont <- d |> count(cod_mun_ibge) |> filter(n == length(anos)) |> pull(cod_mun_ibge)
  d <- d |> filter(cod_mun_ibge %in% cont) |>
    arrange(grupo_sd, cod_mun_ibge, ano)

  Y <- d |>
    pivot_wider(id_cols = cod_mun_ibge, names_from = ano, values_from = all_of(yvar)) |>
    arrange(cod_mun_ibge)
  W <- d |>
    pivot_wider(id_cols = cod_mun_ibge, names_from = ano, values_from = treat_post,
                values_fill = 0) |>
    arrange(cod_mun_ibge)
  stopifnot(all(Y$cod_mun_ibge == W$cod_mun_ibge))

  Y_mat <- as.matrix(Y[, -1])
  W_mat <- as.matrix(W[, -1])

  # synthdid::panel.matrices precisa do painel ordenado (controles primeiro,
  # tratados ao final; anos na ordem cronológica). Reordenar:
  ord <- order(rowSums(W_mat) > 0, Y$cod_mun_ibge)
  Y_mat <- Y_mat[ord, ]
  W_mat <- W_mat[ord, ]

  N0 <- sum(rowSums(W_mat) == 0)
  T0 <- length(t_pre)

  est <- synthdid_estimate(Y_mat, N0 = N0, T0 = T0)
  metodo_se <- if (N0 > nrow(Y_mat) - N0) "placebo" else "bootstrap"
  se <- tryCatch(sqrt(vcov(est, method = metodo_se)),
                 error = function(e) NA_real_)
  list(tau = as.numeric(est), se = as.numeric(se),
       N0 = N0, N1 = nrow(Y_mat) - N0, T0 = T0, T1 = ncol(Y_mat) - T0,
       metodo_se = metodo_se)
}

sdid_res <- list()
for (nm in names(outcomes)) {
  yv <- outcomes[[nm]]
  cat(sprintf("  %s ... ", nm))
  res <- tryCatch(executar_sdid(yv, painel_sd), error = function(e) {
    cat("ERRO:", conditionMessage(e), "\n"); NULL
  })
  sdid_res[[nm]] <- res
  if (!is.null(res)) {
    cat(sprintf("tau = %+.5f (SE %.5f) N0=%d N1=%d T0=%d T1=%d\n",
                res$tau, res$se, res$N0, res$N1, res$T0, res$T1))
  }
}

# =============================================================================
# (iii) W ALTERNATIVOS — k=5 e distância inversa
# =============================================================================
cat("\n===== W ALTERNATIVOS =====\n")

w_obj <- readRDS("data/cache/W_exposicao.rds")
ilhas <- w_obj$ilhas
exp_all <- w_obj$exp_all  # cod_mun_ibge, Exp, WExp (queen)

cat("  Carregando malha geobr (pode demorar)...\n")
mun_sf <- read_municipality(year = 2020, simplified = TRUE, showProgress = FALSE)
mun_sf <- mun_sf |>
  filter(!(code_muni %in% ilhas)) |>
  mutate(code_muni = as.numeric(code_muni)) |>
  arrange(code_muni)

# Garantir alinhamento com exp_all
mun_sf <- mun_sf |> filter(code_muni %in% exp_all$cod_mun_ibge)
exp_all <- exp_all |> filter(cod_mun_ibge %in% mun_sf$code_muni) |>
  arrange(cod_mun_ibge)
stopifnot(all(mun_sf$code_muni == exp_all$cod_mun_ibge))

centroides <- suppressWarnings(st_centroid(mun_sf))
coords <- st_coordinates(centroides)

# Helper: converte listw em Matrix esparsa
listw_to_sparse <- function(lw) {
  n  <- length(lw$neighbours)
  k  <- card(lw$neighbours)
  i_ <- rep(seq_len(n), times = k)
  j_ <- unlist(lw$neighbours)
  x_ <- unlist(lw$weights)
  if (length(j_) == 0) return(sparseMatrix(i = integer(0), j = integer(0),
                                           x = numeric(0), dims = c(n, n)))
  sparseMatrix(i = i_, j = j_, x = x_, dims = c(n, n))
}

# k=5 vizinhos mais próximos
cat("  Construindo W_k5...\n")
nb_k5 <- knn2nb(knearneigh(coords, k = 5))
lw_k5 <- nb2listw(nb_k5, style = "W", zero.policy = TRUE)
W_k5  <- listw_to_sparse(lw_k5)

# Distância inversa (até 200km, evita matriz densa)
cat("  Construindo W_inv (corte 200km)...\n")
nb_dist <- dnearneigh(coords, 0, 200000, longlat = TRUE)
distancias <- nbdists(nb_dist, coords, longlat = TRUE)
inv_dist <- lapply(distancias, function(x) 1 / pmax(x, 1))
sem_vizinhos <- which(card(nb_dist) == 0)
if (length(sem_vizinhos) > 0) {
  cat(sprintf("    %d municípios sem vizinhos no raio; usando k=5 como fallback\n",
              length(sem_vizinhos)))
  for (idx in sem_vizinhos) {
    nb_dist[[idx]]   <- nb_k5[[idx]]
    inv_dist[[idx]]  <- rep(1 / 5, length(nb_k5[[idx]]))
  }
}
lw_inv <- nb2listw(nb_dist, glist = inv_dist, style = "W", zero.policy = TRUE)
W_inv  <- listw_to_sparse(lw_inv)

# Construir vetor de exposição alinhado e calcular WExp para cada matriz
E_vec <- exp_all$Exp
WExp_k5  <- as.numeric(W_k5  %*% E_vec)
WExp_inv <- as.numeric(W_inv %*% E_vec)

exp_alt <- exp_all |>
  mutate(WExp_k5 = WExp_k5, WExp_inv = WExp_inv)

# Painel SLX-DiD para cada matriz
painel_slx <- painel_ag |>
  inner_join(exp_alt |> select(cod_mun_ibge, WExp_k5, WExp_inv),
             by = "cod_mun_ibge") |>
  mutate(Post = as.integer(ano >= 2020))

slx_res <- list()
for (nm in names(outcomes)) {
  yv <- outcomes[[nm]]
  d <- painel_slx |> filter(!is.na(.data[[yv]]), is.finite(.data[[yv]]))
  m_k5  <- feols(as.formula(paste0(yv, " ~ I(Post*Exposicao) + I(Post*WExp_k5)  + ln_pib | cod_mun_ibge + ano")),
                 data = d, cluster = ~ cod_mun_ibge, warn = FALSE, notes = FALSE)
  m_inv <- feols(as.formula(paste0(yv, " ~ I(Post*Exposicao) + I(Post*WExp_inv) + ln_pib | cod_mun_ibge + ano")),
                 data = d, cluster = ~ cod_mun_ibge, warn = FALSE, notes = FALSE)
  slx_res[[nm]] <- list(
    k5 = list(
      direto    = coef(m_k5)["I(Post * Exposicao)"],
      se_direto = sqrt(vcov(m_k5)["I(Post * Exposicao)", "I(Post * Exposicao)"]),
      spillover = coef(m_k5)["I(Post * WExp_k5)"],
      se_spill  = sqrt(vcov(m_k5)["I(Post * WExp_k5)", "I(Post * WExp_k5)"]),
      n         = nobs(m_k5)
    ),
    inv = list(
      direto    = coef(m_inv)["I(Post * Exposicao)"],
      se_direto = sqrt(vcov(m_inv)["I(Post * Exposicao)", "I(Post * Exposicao)"]),
      spillover = coef(m_inv)["I(Post * WExp_inv)"],
      se_spill  = sqrt(vcov(m_inv)["I(Post * WExp_inv)", "I(Post * WExp_inv)"]),
      n         = nobs(m_inv)
    )
  )
  cat(sprintf("  %-10s | k=5: direto %+.4f spill %+.4f | inv: direto %+.4f spill %+.4f\n",
              nm,
              slx_res[[nm]]$k5$direto,  slx_res[[nm]]$k5$spillover,
              slx_res[[nm]]$inv$direto, slx_res[[nm]]$inv$spillover))
}

# ---- 4. Salvar ----
res <- list(
  placebo = placebo_res,
  sdid    = sdid_res,
  slx     = slx_res
)
dir.create("data/cache", showWarnings = FALSE, recursive = TRUE)
saveRDS(res, "data/cache/robustez.rds")
cat("\nSalvo em data/cache/robustez.rds\n")
