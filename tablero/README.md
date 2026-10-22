# Tablero de avance – Laboratorio 10

Dos visualizaciones interactivas enlazadas (Streamlit + Plotly):

1. **Flujo anual por vía de ingreso** (gráfico de columnas apiladas). Clic en una columna para elegir el año.
2. **Flujo mensual del año elegido** frente al promedio 2015–2019 (línea de referencia). Se actualiza al elegir año en el gráfico 1 o en el selector. Permite ver el total o desglosarlo por vía.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Datos

`data/migracion_agregada.csv` se genera a partir de la base de migración del Laboratorio 1 con:

```bash
python preparar_datos.py ruta/Base_Migracion_2009-2026jun.xlsx
```

El CSV ya contiene los datos agregados por año, mes, vía y tipo de viajero, así que la aplicación no necesita el Excel original.

## Notas

- Los datos son observados. Este avance no incluye modelos predictivos.
- 2026 incluye solo enero a junio.
- Paleta Okabe-Ito (apta para daltonismo); cada color representa la misma vía en todo el tablero.
