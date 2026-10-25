# Tablero final – Laboratorio 10

Tablero en Streamlit + Plotly sobre los viajeros internacionales a Guatemala (2009 – jun 2026),
pensado para directivos. Documento de diseño: [`../docs/Documento_de_diseno_tablero.pdf`](../docs/Documento_de_diseno_tablero.pdf).

## Pestañas

**Flujo de viajeros**: 8 visualizaciones interactivas. El selector «Gráficas a mostrar» permite elegir cuáles ver.

1. Flujo anual por vía (clic en una columna = elegir año para todo el tablero)
2. Flujo mensual del año frente al promedio 2015–2019
3. Mapa de calor de estacionalidad (año × mes)
4. Principales países de origen (clic en un país = gráfica 5)
5. Tendencia del país elegido
6. Puntos de ingreso (fronteras, aeropuertos, puertos)
7. Región de origen (participación por año)
8. Recuperación frente a 2015–2019 por vía

**Comparación de modelos (Lab 1)**: Prophet, ARIMA, Holt-Winters, ETS y Seasonal Naive en 7 series.
Se muestran pronóstico frente a lo real, el error típico (RMSE) de cada modelo y el error relativo por serie.
**No se reentrena ningún modelo**: el tablero lee las predicciones y métricas exportadas del Lab 1.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
python test_app.py   # prueba de humo: todas las combinaciones de filtros
```

## Datos (`data/`)

Los CSV ya están incluidos, así que no se necesita el Excel ni R para usar el tablero. Para regenerarlos:

```bash
# Datos observados (migracion_agregada, paises_anual, fronteras_mensual)
python preparar_datos.py ruta/Base_Migracion_2009-2026jun.xlsx

# Resultados del Lab 1 (metricas_lab1, predicciones_lab1, series_lab1).
# Ejecuta el Rmd del Lab 1 sin modificarlo y exporta lo que ya calcula.
Rscript exportar_lab1.R ruta/Laboratorio_1_completo.Rmd ruta/Base_Migracion_2009-2026jun.xlsx
```

El documento de diseño se regenera con `python ../docs/generar_documento.py` (requiere `reportlab`).
Usa las capturas de `docs/img/`.

## Notas

- 2026 incluye solo enero a junio; las comparaciones con 2015–2019 usan los mismos meses.
- Paleta Okabe-Ito (apta para daltonismo); cada vía conserva su color en todo el tablero.
- Si un filtro no tiene datos, la gráfica muestra un mensaje en lugar de quedar vacía.
