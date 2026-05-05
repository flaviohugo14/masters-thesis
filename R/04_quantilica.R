#!/usr/bin/env Rscript
# 08_quantilica.R
# Regressão quantílica em painel via Canay (2011) two-step:
#   Step 1: feols com EF de município e ano para identificar shifters location
#   Step 2: rq sobre y_tilde = y - alpha_i - lambda_t para cada quantil tau
# SE por bootstrap de blocos por município (B = 200).
#
# Outcomes: IRC e IRF/IRE.
# Quantis: 10, 25, 50, 75, 90.
# Spec:    Y_it = alpha_i + lambda_t + beta_tau (Post*Exp) + gamma_tau ln(pib) + e_it
# Janela:  2014–2023 (sem truncamento de 2022, pois IRC e IRF/IRE são confiáveis até 2023).
#
# Pré-requisito: install.packages("quantreg")
#
# Saída: data/cache/quantilica.rds

suppressPackageStartupMessages({
  library(dplyr)
  library(fixest)
  library(quantreg)
})

set.seed(20260503)
B <- 200

# ---- 1. Painel e exposição (idêntico aos scripts 06/07) ----
ind <- read.csv("data/processed/indicadores_financeiros_basedosdados.csv")

# Cobertura canônica idêntica à de main.qmd §3.2 (sec-exposicao):
# agregação por município das médias 2009-2013 (sem filtrar linhas zero antes
# de agregar) e filtragem do município pelo n_ag médio > 0.
pre_2013 <- ind |>
  filter(ano >= 2009, ano <= 2013) |>
  group_by(cod_mun_ibge) |>
  summarise(
    n_ag = mean(n_agencias, na.rm = TRUE),
    pib  = mean(pib_real,   na.rm = TRUE),
    IRC  = mean(IRC,        na.rm = TRUE),
    PLP  = mean(PLP,        na.rm = TRUE),
    ICB  = mean(ICB,        na.rm = TRUE),
    .groups = "drop"
  ) |>
  mutate(
    ag_per_pib = n_ag / pib * 1e6,
    ln_pib     = log(pmax(pib, 1))
  )

cobertura <- pre_2013 |>
  filter(n_ag > 0, !is.na(IRC), !is.na(PLP), !is.na(ICB))

X <- cobertura |>
  transmute(ag_per_pib, ICB, PLP, IRC_inv = -IRC, ln_pib_inv = -ln_pib) |>
  scale()
pca_exp <- prcomp(X, center = FALSE, scale. = FALSE)
cobertura$Exposicao <- as.numeric(pca_exp$x[, 1])
if (mean(cobertura$Exposicao[cobertura$ICB > median(cobertura$ICB)]) <
    mean(cobertura$Exposicao[cobertura$ICB < median(cobertura$ICB)])) {
  cobertura$Exposicao <- -cobertura$Exposicao
}

painel <- ind |>
  filter(ano >= 2014, ano <= 2023) |>
  inner_join(cobertura |> select(cod_mun_ibge, Exposicao), by = "cod_mun_ibge") |>
  mutate(
    Post    = as.integer(ano >= 2020),
    ln_pib  = log(pmax(pib_real, 1)),
    IRF_IRE = ifelse(IRE > 0, IRF / IRE, NA_real_)
  )

outcomes <- list(IRC = "IRC", IRF_IRE = "IRF_IRE")
taus     <- c(0.10, 0.25, 0.50, 0.75, 0.90)
tau_lab  <- paste0("tau_", sub("0\\.", "", sprintf("%.2f", taus)))

# ---- 2. Canay (2011) two-step ----
canay_rq <- function(d, yvar, taus) {
  d <- d[is.finite(d[[yvar]]), , drop = FALSE]
  d$y         <- d[[yvar]]
  d$post_exp  <- d$Post * d$Exposicao

  m_ols    <- feols(y ~ post_exp + ln_pib | cod_mun_ibge + ano,
                    data = d, warn = FALSE, notes = FALSE)
  fes      <- fixef(m_ols)
  alpha_i  <- fes$cod_mun_ibge[as.character(d$cod_mun_ibge)]
  lambda_t <- fes$ano[as.character(d$ano)]
  d$y_tilde <- d$y - alpha_i - lambda_t

  fit <- rq(y_tilde ~ post_exp + ln_pib, data = d, tau = taus, method = "br")
  cf  <- coef(fit)
  if (is.matrix(cf)) cf["post_exp", ] else setNames(cf["post_exp"], paste0("tau= ", taus))
}

ols_fe_coef <- function(d, yvar) {
  d <- d[is.finite(d[[yvar]]), , drop = FALSE]
  fm <- as.formula(paste(yvar, "~ I(Post*Exposicao) + ln_pib | cod_mun_ibge + ano"))
  m  <- feols(fm, data = d, cluster = ~ cod_mun_ibge,
              warn = FALSE, notes = FALSE)
  cf <- coef(m)["I(Post * Exposicao)"]
  se <- sqrt(vcov(m)["I(Post * Exposicao)", "I(Post * Exposicao)"])
  c(est = as.numeric(cf), se = as.numeric(se))
}

# ---- 3. Bootstrap de blocos por município ----
boot_canay <- function(d, yvar, taus, B = 200) {
  d      <- as.data.frame(d)
  d      <- d[is.finite(d[[yvar]]), , drop = FALSE]
  munis  <- unique(d$cod_mun_ibge)
  N      <- length(munis)
  splits <- split(d, d$cod_mun_ibge)

  point  <- canay_rq(d, yvar, taus)
  ols    <- ols_fe_coef(d, yvar)

  boot_mat <- matrix(NA_real_, nrow = B, ncol = length(taus),
                     dimnames = list(NULL, tau_lab))
  t0 <- Sys.time()
  for (b in seq_len(B)) {
    s     <- sample(N, N, replace = TRUE)
    parts <- splits[s]
    for (j in seq_along(parts)) parts[[j]]$cod_mun_ibge <- j
    d_b   <- do.call(rbind, parts)
    boot_mat[b, ] <- tryCatch(canay_rq(d_b, yvar, taus),
                              error = function(e) rep(NA_real_, length(taus)))
    if (b %% 25 == 0) {
      el <- difftime(Sys.time(), t0, units = "mins")
      cat(sprintf("    boot %d/%d  (decorrido: %.1f min)\n", b, B, as.numeric(el)))
    }
  }

  list(taus    = taus,
       point   = setNames(as.numeric(point), tau_lab),
       se      = apply(boot_mat, 2, sd, na.rm = TRUE),
       ic_lo   = apply(boot_mat, 2, quantile, 0.025, na.rm = TRUE),
       ic_hi   = apply(boot_mat, 2, quantile, 0.975, na.rm = TRUE),
       ols_est = ols["est"], ols_se = ols["se"],
       n_obs   = nrow(d), n_mun = N, B = B,
       boot    = boot_mat)
}

# ---- 4. Loop principal ----
res <- list()
for (nm in names(outcomes)) {
  yv <- outcomes[[nm]]
  cat(sprintf("\n===== %s =====\n", nm))
  res[[nm]] <- boot_canay(painel, yv, taus, B = B)
  cat(sprintf("  N obs = %d  N munis = %d\n",
              res[[nm]]$n_obs, res[[nm]]$n_mun))
  for (i in seq_along(taus)) {
    cat(sprintf("  τ = %.2f : %+.4f  (SE %.4f)  IC95 [%+.4f , %+.4f]\n",
                taus[i], res[[nm]]$point[i], res[[nm]]$se[i],
                res[[nm]]$ic_lo[i], res[[nm]]$ic_hi[i]))
  }
  cat(sprintf("  OLS-FE  : %+.4f  (SE %.4f)  ← efeito médio de referência\n",
              res[[nm]]$ols_est, res[[nm]]$ols_se))
}

# ---- 5. Salvar ----
dir.create("data/cache", showWarnings = FALSE, recursive = TRUE)
saveRDS(res, "data/cache/quantilica.rds")
cat("\nSalvo em data/cache/quantilica.rds\n")
