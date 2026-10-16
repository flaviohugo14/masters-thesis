#!/usr/bin/env Rscript
# Baixa as malhas do IBGE e salva os dados usados nos mapas.

suppressPackageStartupMessages({
  library(jsonlite)
})

dir.create("data/raw", showWarnings = FALSE, recursive = TRUE)
dir.create("data/cache", showWarnings = FALSE, recursive = TRUE)

API <- "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"

baixar <- function(intrarregiao, destino) {
  if (file.exists(destino)) {
    message("Usando malha em cache: ", destino)
    return(invisible(destino))
  }
  url <- paste0(API, "?formato=application/vnd.geo+json&qualidade=minima",
                "&intrarregiao=", intrarregiao)
  message("Baixando malha ", intrarregiao, " ...")
  utils::download.file(url, destino, quiet = TRUE)
  invisible(destino)
}

arq_mun <- baixar("municipio", "data/raw/malha_municipios.geojson")
arq_uf  <- baixar("UF",        "data/raw/malha_uf.geojson")

flatten_malha <- function(arquivo, nome_id) {
  fc <- fromJSON(arquivo, simplifyVector = FALSE)

  pedacos <- lapply(fc$features, function(f) {
    cod <- f$properties$codarea
    poligonos <- if (f$geometry$type == "MultiPolygon") {
      f$geometry$coordinates
    } else {
      list(f$geometry$coordinates)
    }
    aneis <- unlist(poligonos, recursive = FALSE)

    lapply(seq_along(aneis), function(k) {
      xy <- do.call(rbind, lapply(aneis[[k]], as.numeric))
      data.frame(
        id   = cod,
        grp  = paste(cod, k, sep = "-"),
        long = xy[, 1],
        lat  = xy[, 2],
        stringsAsFactors = FALSE
      )
    })
  })

  out <- do.call(rbind, unlist(pedacos, recursive = FALSE))
  names(out)[1] <- nome_id
  out$grp <- as.integer(factor(out$grp))
  out
}

mun <- flatten_malha(arq_mun, "cod_mun_ibge")
uf  <- flatten_malha(arq_uf,  "cod_uf")

maior_anel <- do.call(rbind, lapply(split(mun, mun$cod_mun_ibge), function(d) {
  tam <- table(d$grp)
  d[d$grp == as.integer(names(tam)[which.max(tam)]), ]
}))

cent <- aggregate(cbind(long, lat) ~ cod_mun_ibge, data = maior_anel, FUN = mean)

stopifnot(
  length(unique(mun$cod_mun_ibge)) == 5570,
  length(unique(uf$cod_uf)) == 27,
  nrow(cent) == 5570
)

saveRDS(list(mun = mun, uf = uf, cent = cent), "data/cache/mapas.rds")

message(sprintf("data/cache/mapas.rds: %d municípios, %d vértices, %.1f MB",
                length(unique(mun$cod_mun_ibge)), nrow(mun),
                file.size("data/cache/mapas.rds") / 1e6))
