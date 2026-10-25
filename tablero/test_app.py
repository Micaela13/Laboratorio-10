"""Prueba de humo: el tablero corre sin errores con cualquier combinación de filtros.

Ejecutar:  python test_app.py
"""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent / "app.py")
df = pd.read_csv(Path(__file__).parent / "data" / "migracion_agregada.csv")


def correr(**estado) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    for clave, valor in estado.items():
        at.session_state[clave] = valor
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


at = correr()
assert len(at.tabs) == 2
assert len(at.get("plotly_chart")) == 8 + 3, len(at.get("plotly_chart"))

for tipo in ["Todos", *df["tipo"].unique()]:
    for anio in sorted(df["ano"].unique()):
        correr(tipo=tipo, anio=int(anio))

assert "No hay gráficas" in correr(graficas=[]).warning[0].value
for serie in pd.read_csv(Path(__file__).parent / "data" / "metricas_lab1.csv")["serie"].unique():
    correr(serie_modelo=serie)
assert any("al menos un modelo" in w.value for w in correr(modelos=[]).warning)
print("OK")
