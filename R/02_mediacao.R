#!/usr/bin/env Rscript
# 06_mediacao.R
# Análise de mediação causal (Imai-Keele-Tingley) adaptada a painel com EF.
# Decompõe o efeito da exposição digital sobre IRF/IRE em:
#   - canal direto (ADE = phi)
#   - canal mediado pelo fechamento de agências (ACME = delta * psi)
#
# Saída: data/cache/mediacao.rds

suppressPackageStartupMessages({
  library(dplyr)
  library(fixest)
})

set.seed(20260426)

# ---- 1. Carregar e preparar painel ----
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

painel_med <- ind |>
  filter(ano >= 2014, ano <= 2022) |>
  inner_join(cobertura |> select(cod_mun_ibge, Exposicao), by = "cod_mun_ibge") |>
  mutate(
    Post     = as.integer(ano >= 2020),
    ln_pib   = log(pmax(pib_real, 1)),
    ln_nag   = log(pmax(n_agencias, 0) + 1),
    IRF_IRE  = ifelse(IRE > 0, IRF / IRE, NA_real_),
    TrtE     = Post * Exposicao,
    sh_agro  = ifelse(vab_total > 0, pmax(0, pmin(1, vab_agro / vab_total)), NA_real_),
    sh_ind   = ifelse(vab_total > 0, pmax(0, pmin(1, vab_ind  / vab_total)), NA_real_),
    sh_serv  = ifelse(vab_total > 0, pmax(0, pmin(1, vab_serv / vab_total)), NA_real_),
    ln_vinc  = log(pmax(vinculos_total, 0) + 1),
    sh_simples = ifelse(estabelecimentos_total > 0,
                        pmax(0, pmin(1, estab_simples / estabelecimentos_total)),
                        NA_real_)
  ) |>
  filter(!is.na(IRF_IRE), is.finite(IRF_IRE), !is.na(ln_nag))

cat(sprintf("Painel mediação: %d obs, %d municípios, anos %d-%d\n",
            nrow(painel_med),
            length(unique(painel_med$cod_mun_ibge)),
            min(painel_med$ano), max(painel_med$ano)))

# ---- 2. Equações (especificação principal: só ln_pib como controle) ----
eq_M <- feols(ln_nag  ~ TrtE + ln_pib | cod_mun_ibge + ano,
              data = painel_med, cluster = ~ cod_mun_ibge)
eq_Y <- feols(IRF_IRE ~ TrtE + ln_nag + ln_pib | cod_mun_ibge + ano,
              data = painel_med, cluster = ~ cod_mun_ibge)
eq_T <- feols(IRF_IRE ~ TrtE + ln_pib | cod_mun_ibge + ano,
              data = painel_med, cluster = ~ cod_mun_ibge)

# ---- 2b. Equações com controles reais (robustez) ----
ctrls <- "+ ln_pib + sh_agro + sh_ind + sh_serv + ln_vinc + sh_simples"
painel_med_c <- painel_med |>
  filter(!is.na(sh_agro), !is.na(sh_ind), !is.na(sh_serv),
         !is.na(ln_vinc), !is.na(sh_simples))

eq_M_c <- feols(as.formula(paste("ln_nag  ~ TrtE", ctrls, "| cod_mun_ibge + ano")),
                data = painel_med_c, cluster = ~ cod_mun_ibge)
eq_Y_c <- feols(as.formula(paste("IRF_IRE ~ TrtE + ln_nag", ctrls, "| cod_mun_ibge + ano")),
                data = painel_med_c, cluster = ~ cod_mun_ibge)
eq_T_c <- feols(as.formula(paste("IRF_IRE ~ TrtE", ctrls, "| cod_mun_ibge + ano")),
                data = painel_med_c, cluster = ~ cod_mun_ibge)

delta_c <- coef(eq_M_c)["TrtE"]
psi_c   <- coef(eq_Y_c)["ln_nag"]
phi_c   <- coef(eq_Y_c)["TrtE"]
tau_c   <- coef(eq_T_c)["TrtE"]
ACME_c  <- delta_c * psi_c
se_delta_c <- sqrt(vcov(eq_M_c)["TrtE", "TrtE"])
se_psi_c   <- sqrt(vcov(eq_Y_c)["ln_nag", "ln_nag"])
se_phi_c   <- sqrt(vcov(eq_Y_c)["TrtE", "TrtE"])
se_tau_c   <- sqrt(vcov(eq_T_c)["TrtE", "TrtE"])

delta    <- coef(eq_M)["TrtE"]
se_delta <- sqrt(vcov(eq_M)["TrtE", "TrtE"])
psi      <- coef(eq_Y)["ln_nag"]
se_psi   <- sqrt(vcov(eq_Y)["ln_nag", "ln_nag"])
phi      <- coef(eq_Y)["TrtE"]
se_phi   <- sqrt(vcov(eq_Y)["TrtE", "TrtE"])
tau      <- coef(eq_T)["TrtE"]
se_tau   <- sqrt(vcov(eq_T)["TrtE", "TrtE"])

ACME  <- delta * psi
ADE   <- phi
TOTAL <- ACME + ADE
prop_med <- ACME / TOTAL

# Sobel: SE assintótico do produto delta*psi (assume independência das amostras)
se_acme_sobel <- sqrt(psi^2 * se_delta^2 + delta^2 * se_psi^2)
z_sobel <- ACME / se_acme_sobel
p_sobel <- 2 * pnorm(-abs(z_sobel))
ic_sobel <- ACME + c(-1, 1) * 1.96 * se_acme_sobel

# ---- 3. Bootstrap por município (cluster bootstrap) ----
muns <- unique(painel_med$cod_mun_ibge)
n_mun <- length(muns)
B <- 500
boot_acme  <- numeric(B)
boot_ade   <- numeric(B)
boot_total <- numeric(B)

# Pré-indexa para acelerar resampling
idx_by_mun <- split(seq_len(nrow(painel_med)), painel_med$cod_mun_ibge)

t0 <- Sys.time()
for (b in seq_len(B)) {
  ids <- sample(muns, n_mun, replace = TRUE)
  ids_chr <- as.character(ids)
  lst <- idx_by_mun[ids_chr]
  rows <- unlist(lst, use.names = FALSE)
  rep_id <- rep(seq_along(ids_chr), times = lengths(lst))
  d_b <- painel_med[rows, ]
  d_b$mun_b <- paste0(d_b$cod_mun_ibge, "_", rep_id)

  m_b <- tryCatch(
    feols(ln_nag  ~ TrtE + ln_pib | mun_b + ano, data = d_b, warn = FALSE, notes = FALSE),
    error = function(e) NULL)
  y_b <- tryCatch(
    feols(IRF_IRE ~ TrtE + ln_nag + ln_pib | mun_b + ano, data = d_b, warn = FALSE, notes = FALSE),
    error = function(e) NULL)
  t_b <- tryCatch(
    feols(IRF_IRE ~ TrtE + ln_pib | mun_b + ano, data = d_b, warn = FALSE, notes = FALSE),
    error = function(e) NULL)

  if (!is.null(m_b) && !is.null(y_b) && !is.null(t_b)) {
    d_b_acme <- coef(m_b)["TrtE"] * coef(y_b)["ln_nag"]
    boot_acme[b]  <- d_b_acme
    boot_ade[b]   <- coef(y_b)["TrtE"]
    boot_total[b] <- coef(t_b)["TrtE"]
  } else {
    boot_acme[b]  <- NA_real_
    boot_ade[b]   <- NA_real_
    boot_total[b] <- NA_real_
  }
  if (b %% 50 == 0) {
    cat(sprintf("  bootstrap %d/%d (elapsed %.1fs)\n",
                b, B, as.numeric(difftime(Sys.time(), t0, units = "secs"))))
  }
}

ic_acme  <- quantile(boot_acme,  c(0.025, 0.975), na.rm = TRUE)
ic_ade   <- quantile(boot_ade,   c(0.025, 0.975), na.rm = TRUE)
ic_total <- quantile(boot_total, c(0.025, 0.975), na.rm = TRUE)
ic_prop  <- quantile(boot_acme / boot_total, c(0.025, 0.975), na.rm = TRUE)

# ---- 4. Salvar resultados ----
res <- list(
  n_obs     = nrow(painel_med),
  n_mun     = length(unique(painel_med$cod_mun_ibge)),
  janela    = c(min(painel_med$ano), max(painel_med$ano)),
  delta     = delta,    se_delta = se_delta,
  psi       = psi,      se_psi   = se_psi,
  phi       = phi,      se_phi   = se_phi,
  tau       = tau,      se_tau   = se_tau,
  ACME      = ACME,     ADE      = ADE,    TOTAL = TOTAL,
  prop_med  = as.numeric(prop_med),
  sobel     = list(se = se_acme_sobel, z = z_sobel, p = p_sobel, ic = ic_sobel),
  bootstrap = list(B = B,
                   acme  = boot_acme,
                   ade   = boot_ade,
                   total = boot_total,
                   ic_acme  = ic_acme,
                   ic_ade   = ic_ade,
                   ic_total = ic_total,
                   ic_prop  = ic_prop),
  com_controles = list(
    n_obs    = nrow(painel_med_c),
    n_mun    = length(unique(painel_med_c$cod_mun_ibge)),
    delta    = delta_c, se_delta = se_delta_c,
    psi      = psi_c,   se_psi   = se_psi_c,
    phi      = phi_c,   se_phi   = se_phi_c,
    tau      = tau_c,   se_tau   = se_tau_c,
    ACME     = ACME_c
  )
)

dir.create("data/cache", showWarnings = FALSE, recursive = TRUE)
saveRDS(res, "data/cache/mediacao.rds")

cat("\n===== Resultados da mediação =====\n")
cat(sprintf("delta (Trt -> M)      = %+.5f (SE %.5f)\n", delta, se_delta))
cat(sprintf("psi   (M   -> Y | T)  = %+.5f (SE %.5f)\n", psi,   se_psi))
cat(sprintf("phi   (Trt -> Y | M)  = %+.5f (SE %.5f)  [ADE]\n", phi, se_phi))
cat(sprintf("tau   (Trt -> Y)      = %+.5f (SE %.5f)  [Total sem mediador]\n", tau, se_tau))
cat(sprintf("ACME = delta*psi      = %+.5f\n", ACME))
cat(sprintf("ACME + ADE            = %+.5f\n", TOTAL))
cat(sprintf("Proporção mediada     = %.1f%%\n", 100 * prop_med))
cat(sprintf("Sobel: z=%.2f, p=%.4f, IC95=[%+.5f, %+.5f]\n", z_sobel, p_sobel, ic_sobel[1], ic_sobel[2]))
cat(sprintf("Bootstrap (B=%d):\n", B))
cat(sprintf("  ACME IC95  = [%+.5f, %+.5f]\n", ic_acme[1],  ic_acme[2]))
cat(sprintf("  ADE  IC95  = [%+.5f, %+.5f]\n", ic_ade[1],   ic_ade[2]))
cat(sprintf("  Total IC95 = [%+.5f, %+.5f]\n", ic_total[1], ic_total[2]))
cat(sprintf("  Prop IC95  = [%.1f%%, %.1f%%]\n", 100*ic_prop[1], 100*ic_prop[2]))
cat("\n----- Robustez: com controles reais -----\n")
cat(sprintf("N obs = %d, N munis = %d\n", nrow(painel_med_c),
            length(unique(painel_med_c$cod_mun_ibge))))
cat(sprintf("delta_c = %+.5f (SE %.5f)\n", delta_c, se_delta_c))
cat(sprintf("psi_c   = %+.5f (SE %.5f)\n", psi_c,   se_psi_c))
cat(sprintf("phi_c   = %+.5f (SE %.5f)\n", phi_c,   se_phi_c))
cat(sprintf("tau_c   = %+.5f (SE %.5f)\n", tau_c,   se_tau_c))
cat(sprintf("ACME_c  = %+.5f\n", ACME_c))

cat("\nSalvo em data/cache/mediacao.rds\n")
