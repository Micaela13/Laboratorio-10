# Ejecuta el Rmd del Laboratorio 1 tal cual y exporta sus predicciones y métricas
# para el tablero. El tablero solo lee estos CSV: nunca reentrena modelos.
#
# Uso (desde la carpeta tablero/):
#   Rscript exportar_lab1.R ruta/Laboratorio_1_completo.Rmd ruta/Base_Migracion_2009-2026jun.xlsx
# Genera:
#   data/metricas_lab1.csv      MAE, RMSE, AIC, BIC por serie y modelo (conjunto de prueba)
#   data/predicciones_lab1.csv  serie observada completa + predicción de cada modelo en prueba
#   data/series_lab1.csv        fuerza de estacionalidad/tendencia, volatilidad y caída 2020

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Uso: Rscript exportar_lab1.R Laboratorio_1.Rmd Base_Migracion.xlsx")
xlsx <- normalizePath(args[2], winslash = "/", mustWork = TRUE)

codigo <- knitr::purl(args[1], output = tempfile(fileext = ".R"),
                      quiet = TRUE, documentation = 0)
src <- readLines(codigo, encoding = "UTF-8")
src <- sub("^setwd\\(.*\\)", "", src)
src <- gsub('"Base_Migracion_2009-2026jun.xlsx"', deparse(xlsx), src, fixed = TRUE)
# La función del Lab 1 ya calcula `comparacion` (real + 5 predicciones) pero solo la grafica.
src <- sub("metricas = metricas,",
           "metricas = metricas, predicciones = comparacion, arima_txt = as.character(mejor_arima), ets_txt = modelo_ets$method,",
           src, fixed = TRUE)
stopifnot(any(grepl("predicciones = comparacion", src, fixed = TRUE)))

set.seed(2026)
pdf(NULL)  # los gráficos del Rmd se descartan
for (e in parse(text = src, encoding = "UTF-8")) eval(e, globalenv())

nombres_modelo <- c(real = "Real", HoltWinters = "Holt-Winters",
                    SeasonalNaive = "Seasonal Naive")

metricas <- bind_rows(lapply(names(resultados), function(n) {
  r <- resultados[[n]]
  r$metricas %>%
    mutate(serie = n,
           especificacion = case_when(modelo == "ARIMA" ~ r$arima_txt,
                                      modelo == "ETS" ~ r$ets_txt,
                                      TRUE ~ NA_character_),
           mejor = modelo == r$mejor_modelo_global)
}))

predicciones <- bind_rows(lapply(names(resultados), function(n) {
  entreno <- series[[n]]$train$df %>%
    transmute(fecha, modelo = "Real", valor = viajeros, tramo = "Entrenamiento")
  prueba <- resultados[[n]]$predicciones %>%
    transmute(fecha, modelo = recode(serie, !!!nombres_modelo), valor, tramo = "Prueba")
  bind_rows(entreno, prueba) %>% mutate(serie = n)
}))

dir.create("data", showWarnings = FALSE)
write.csv(metricas, "data/metricas_lab1.csv", row.names = FALSE, fileEncoding = "UTF-8")
write.csv(predicciones, "data/predicciones_lab1.csv", row.names = FALSE, fileEncoding = "UTF-8")
write.csv(tabla_comparativa, "data/series_lab1.csv", row.names = FALSE, fileEncoding = "UTF-8")
cat("Exportado:", nrow(metricas), "métricas,", nrow(predicciones), "puntos de predicción\n")
