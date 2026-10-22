"""Agrega la base de migración del Laboratorio 1 a un CSV liviano para el tablero.

Uso:
    python preparar_datos.py ruta/Base_Migracion_2009-2026jun.xlsx
Genera:
    data/migracion_agregada.csv  (año, mes, vía, tipo de viajero, viajeros)
"""
import sys
from pathlib import Path

import pandas as pd

SALIDA = Path(__file__).parent / "data" / "migracion_agregada.csv"


def main(ruta_xlsx: str) -> None:
    df = pd.read_excel(ruta_xlsx)
    df = df.rename(columns={
        "Año": "ano",
        "Mes cod": "mes",
        "Vía": "via",
        "Tipo de Viajero": "tipo",
        "Viajero": "viajeros",
    })
    df["viajeros"] = df["viajeros"].fillna(0)
    agregada = (
        df.groupby(["ano", "mes", "via", "tipo"], as_index=False)["viajeros"]
        .sum()
    )
    agregada["viajeros"] = agregada["viajeros"].round(0).astype(int)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    agregada.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"Guardado {SALIDA} ({len(agregada)} filas)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python preparar_datos.py ruta/Base_Migracion.xlsx")
    main(sys.argv[1])
