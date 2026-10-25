"""Agrega la base de migración del Laboratorio 1 a CSV livianos para el tablero.

Uso:
    python preparar_datos.py ruta/Base_Migracion_2009-2026jun.xlsx
Genera en data/:
    migracion_agregada.csv  (año, mes, vía, tipo de viajero, viajeros)
    paises_anual.csv        (año, país, región de origen, vía, tipo, viajeros)
    fronteras_mensual.csv   (año, mes, vía, frontera, tipo, viajeros)
"""
import sys
from pathlib import Path

import pandas as pd

DATOS = Path(__file__).parent / "data"

# MCEO agrupado en 5 regiones de origen (colores Okabe-Ito disponibles sin repetir vías).
REGION = {
    "01 CENTROAMÉRICA": "Centroamérica",
    "02 NORTEAMÉRICA": "Norteamérica",
    "04 EUROPA": "Europa",
    "03 SUDAMÉRICA": "Sudamérica",
}


def guardar(df: pd.DataFrame, claves: list[str], nombre: str) -> None:
    agregada = df.groupby(claves, as_index=False)["viajeros"].sum()
    agregada["viajeros"] = agregada["viajeros"].round(0).astype(int)
    agregada.to_csv(DATOS / nombre, index=False, encoding="utf-8")
    print(f"Guardado {nombre} ({len(agregada)} filas)")


def main(ruta_xlsx: str) -> None:
    df = pd.read_excel(ruta_xlsx)
    df = df.rename(columns={
        "Año": "ano",
        "Mes cod": "mes",
        "Vía": "via",
        "Tipo de Viajero": "tipo",
        "Viajero": "viajeros",
        "País": "pais",
        "Frontera": "frontera",
    })
    df["viajeros"] = df["viajeros"].fillna(0)
    df["region"] = df["MCEO"].map(REGION).fillna("Resto del mundo")
    df["frontera"] = df["frontera"].str.replace(r"^\d+\s+", "", regex=True)
    DATOS.mkdir(parents=True, exist_ok=True)
    guardar(df, ["ano", "mes", "via", "tipo"], "migracion_agregada.csv")
    guardar(df, ["ano", "pais", "region", "via", "tipo"], "paises_anual.csv")
    guardar(df, ["ano", "mes", "via", "frontera", "tipo"], "fronteras_mensual.csv")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python preparar_datos.py ruta/Base_Migracion.xlsx")
    main(sys.argv[1])
