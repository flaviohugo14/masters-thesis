#!/usr/bin/env Rscript
# Testes de dependência espacial para o SLX-DiD (@sec-sdm): I de Moran e LM
# (simples e robustos) sobre os resíduos do SLX, e testes LR entre SLX, SAR,
# SDM, SEM e SDEM estimados por máxima verossimilhança com efeitos fixos de
# município e ano (transformação de Lee e Yu, 2010).

suppressPackageStartupMessages({
  library(dplyr)
  library(Matrix)
})

set.seed(20261020)

ind <- read.csv("data/processed/indicadores_financeiros_consolidados.csv")

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
  mutate(ag_per_pib = n_ag / pib * 1e6, ln_pib = log(pmax(pib, 1)))

cobertura <- pre_2013 |> filter(n_ag > 0, !is.na(IRC), !is.na(PLP), !is.na(ICB))
X_exp <- cobertura |>
  transmute(ag_per_pib, ICB, PLP, IRC_inv = -IRC, ln_pib_inv = -ln_pib) |>
  scale()
cobertura$Exposicao <- as.numeric(prcomp(X_exp, center = FALSE, scale. = FALSE)$x[, 1])
if (mean(cobertura$Exposicao[cobertura$ICB > median(cobertura$ICB)]) <
    mean(cobertura$Exposicao[cobertura$ICB < median(cobertura$ICB)])) {
  cobertura$Exposicao <- -cobertura$Exposicao
}

art_w <- readRDS("data/cache/W_exposicao.rds")
cods_W <- art_w$exp_all$cod_mun_ibge
C_full <- (art_w$W > 0) * 1

painel <- ind |>
  filter(ano >= 2014, ano <= 2023, !cod_mun_ibge %in% art_w$ilhas) |>
  inner_join(cobertura |> select(cod_mun_ibge, Exposicao), by = "cod_mun_ibge") |>
  inner_join(art_w$exp_all |> select(cod_mun_ibge, WExp), by = "cod_mun_ibge") |>
  mutate(
    Post    = as.integer(ano >= 2020),
    ln_pib  = log(pmax(pib_real, 1)),
    ln_nag  = log(pmax(n_agencias, 0) + 1),
    IRF_IRE = ifelse(IRE > 0, IRF / IRE, NA_real_),
    PostE   = Post * Exposicao,
    PostWE  = Post * WExp
  )

# Painel balanceado por desfecho, com W restrita à amostra e renormalizada.
# Municípios sem vizinho dentro da amostra saem, para não gerar linhas nulas.
preparar <- function(y, d) {
  d <- d |> filter(is.finite(.data[[y]]), is.finite(ln_pib))
  TT <- n_distinct(d$ano)
  bal <- d |> count(cod_mun_ibge) |> filter(n == TT) |> pull(cod_mun_ibge)
  idx <- match(sort(bal), cods_W)
  idx <- idx[rowSums(C_full[idx, idx]) > 0]
  C <- C_full[idx, idx]
  stopifnot(all(rowSums(C) > 0))
  d <- d |> filter(cod_mun_ibge %in% cods_W[idx]) |> arrange(ano, cod_mun_ibge)
  N <- length(idx)
  stopifnot(nrow(d) == N * TT)
  dg <- rowSums(C)
  S  <- Diagonal(x = 1 / sqrt(dg)) %*% C %*% Diagonal(x = 1 / sqrt(dg))
  list(d = d, N = N, TT = TT, W = Diagonal(x = 1 / dg) %*% C,
       om = eigen(as.matrix(S), symmetric = TRUE, only.values = TRUE)$values)
}

demean2 <- function(v, N, TT) {
  M <- matrix(v, N, TT)
  M <- sweep(M, 1, rowMeans(M))
  as.vector(sweep(M, 2, colMeans(M)))
}
lag_w <- function(v, W, N, TT) as.vector(W %*% matrix(v, N, TT))
ols <- function(yv, X) {
  b <- qr.solve(X, yv)
  list(b = b, e = as.vector(yv - X %*% b))
}

testar <- function(y, d) {
  p <- preparar(y, d)
  N <- p$N; TT <- p$TT; W <- p$W; om <- p$om
  n_ef <- (N - 1) * (TT - 1)
  ys <- demean2(p$d[[y]], N, TT)
  Xs <- sapply(c("PostE", "PostWE", "ln_pib"), function(v) demean2(p$d[[v]], N, TT))
  WXs <- apply(Xs, 2, lag_w, W = W, N = N, TT = TT)
  Wy <- lag_w(ys, W, N, TT)
  ldet <- function(r) sum(log(1 - r * om)) - log(1 - r)
  ll_ssr <- function(ssr) -n_ef / 2 * (log(2 * pi * ssr / n_ef) + 1)
  faixa <- c(1 / min(om) + 1e-6, 1 - 1e-6)

  # SLX e testes LM sobre seus resíduos (Anselin et al., 1996; Elhorst, 2014)
  slx <- ols(ys, Xs)
  e   <- slx$e
  s2  <- sum(e^2) / (N * TT)
  We  <- lag_w(e, W, N, TT)
  TW  <- sum(W * W) + sum(W * t(W))
  WXb <- lag_w(as.vector(Xs %*% slx$b), W, N, TT)
  J   <- (sum((WXb - Xs %*% qr.solve(Xs, WXb))^2) + TT * TW * s2) / s2
  g_lag <- sum(e * Wy) / s2
  g_err <- sum(e * We) / s2
  lm <- c(LM_lag  = g_lag^2 / J,
          LM_err  = g_err^2 / (TT * TW),
          RLM_lag = (g_lag - g_err)^2 / (J - TT * TW),
          RLM_err = (g_err - TT * TW / J * g_lag)^2 / (TT * TW * (1 - TT * TW / J)))

  # Log-verossimilhanças com sigma^2 concentrado
  ll_lag <- function(par, X) ll_ssr(sum((ys - par[1] * Wy - X %*% par[-1])^2)) + (TT - 1) * ldet(par[1])
  ll_err <- function(par, X, WX) {
    l <- par[1]
    ll_ssr(sum((ys - l * Wy - (X - l * WX) %*% par[-1])^2)) + (TT - 1) * ldet(l)
  }
  ajustar <- function(tipo, cols) {
    X <- Xs[, cols, drop = FALSE]; WX <- WXs[, cols, drop = FALSE]
    perfil <- if (tipo == "lag") function(r) ll_ssr(sum(ols(ys - r * Wy, X)$e^2)) + (TT - 1) * ldet(r)
              else function(l) ll_ssr(sum(ols(ys - l * Wy, X - l * WX)$e^2)) + (TT - 1) * ldet(l)
    o <- optimize(perfil, faixa, maximum = TRUE)
    r <- o$maximum
    b <- if (tipo == "lag") ols(ys - r * Wy, X)$b else ols(ys - r * Wy, X - r * WX)$b
    par <- c(r, b)
    H <- if (tipo == "lag") optimHess(par, ll_lag, X = X) else optimHess(par, ll_err, X = X, WX = WX)
    V <- solve(-H)
    dimnames(V) <- list(c("espacial", cols), c("espacial", cols))
    list(par = setNames(par, c("espacial", cols)), V = V, ll = o$objective)
  }
  todas <- c("PostE", "PostWE", "ln_pib")
  sdm  <- ajustar("lag", todas)
  sar  <- ajustar("lag", c("PostE", "ln_pib"))
  sdem <- ajustar("err", todas)
  sem  <- ajustar("err", c("PostE", "ln_pib"))
  ll <- c(SLX = ll_ssr(sum(e^2)), SAR = sar$ll, SDM = sdm$ll, SEM = sem$ll, SDEM = sdem$ll)
  lr <- c(SDM_SLX  = 2 * (ll[["SDM"]]  - ll[["SLX"]]),
          SDEM_SLX = 2 * (ll[["SDEM"]] - ll[["SLX"]]),
          SDM_SAR  = 2 * (ll[["SDM"]]  - ll[["SAR"]]),
          SDEM_SEM = 2 * (ll[["SDEM"]] - ll[["SEM"]]))

  # Impactos do SDM (LeSage e Pace, 2009), com erros-padrão por simulação
  impactos <- function(par) {
    r <- par[1]; b <- par[2]; th <- par[3]
    dir <- (b * sum(1 / (1 - r * om)) + th * sum(om / (1 - r * om))) / N
    tot <- (b + th) / (1 - r)
    c(direto = unname(dir), indireto = unname(tot - dir))
  }
  k <- c("espacial", "PostE", "PostWE")
  draws <- MASS::mvrnorm(1000, sdm$par[k], sdm$V[k, k])
  sim <- apply(draws, 1, impactos)

  ep <- function(m, v) sqrt(m$V[v, v])
  list(
    N = N, TT = TT,
    moran = sum(e * We) / sum(e^2),
    lm = lm, lm_p = pchisq(lm, 1, lower.tail = FALSE),
    ll = ll, lr = lr, lr_p = pchisq(lr, 1, lower.tail = FALSE),
    rho = c(est = sdm$par[["espacial"]], ep = ep(sdm, "espacial")),
    lambda = c(est = sdem$par[["espacial"]], ep = ep(sdem, "espacial")),
    sdm_imp = rbind(est = impactos(sdm$par[k]), ep = apply(sim, 1, sd)),
    sdem = rbind(est = sdem$par[c("PostE", "PostWE")],
                 ep = c(ep(sdem, "PostE"), ep(sdem, "PostWE")))
  )
}

cat("\n===== TESTES DE DEPENDÊNCIA ESPACIAL =====\n")
res <- list(
  ln_nag  = testar("ln_nag",  painel |> filter(ano <= 2022)),
  IRC     = testar("IRC",     painel),
  ICO     = testar("ICO",     painel),
  IRF_IRE = testar("IRF_IRE", painel)
)
for (nm in names(res)) {
  r <- res[[nm]]
  cat(sprintf("\n%s (N = %d, T = %d) | Moran = %.3f | rho = %.3f | lambda = %.3f\n",
              nm, r$N, r$TT, r$moran, r$rho[["est"]], r$lambda[["est"]]))
  print(round(rbind(LM = r$lm, p = r$lm_p), 3))
  print(round(rbind(LR = r$lr, p = r$lr_p), 3))
}

saveRDS(res, "data/cache/testes_espaciais.rds")
cat("\nSalvo em data/cache/testes_espaciais.rds\n")
