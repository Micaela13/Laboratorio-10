"""Tablero de avance – Observatorio de Turismo Sostenible (Laboratorio 10).

Dos visualizaciones enlazadas:
  1. Viajeros por año y vía de ingreso (clic en una columna = elegir año).
  2. Viajeros por mes del año elegido, frente al promedio 2015–2019.

Ejecutar:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RUTA = Path(__file__).parent / "data" / "migracion_agregada.csv"

VIAS = ["Terrestre", "Aérea", "Marítima"]
# Paleta Okabe-Ito (apta para daltonismo). Cada color = una vía en todo el tablero.
COLOR_VIA = {"Terrestre": "#0072B2", "Aérea": "#E69F00", "Marítima": "#009E73"}
COLOR_TEXTO = "#1F2937"
COLOR_REF = "#6B7280"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
AÑOS_REF = [2015, 2016, 2017, 2018, 2019]
ANIO_DEFECTO = 2025

st.set_page_config(page_title="Viajeros a Guatemala 2009–2026", layout="wide")


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    return pd.read_csv(RUTA)


def al_elegir_anio() -> None:
    """Callback del gráfico anual: el año clicado pasa a ser el año del gráfico mensual."""
    seleccion = st.session_state.get("grafico_anual") or {}
    puntos = seleccion.get("selection", {}).get("points", [])
    if puntos:
        st.session_state["anio"] = int(puntos[0]["x"])


df = cargar_datos()
años = sorted(int(a) for a in df["ano"].unique())
tipos = ["Todos"] + sorted(df["tipo"].unique())
st.session_state.setdefault("anio", ANIO_DEFECTO)

# ---------------------------------------------------------------- encabezado
st.title("Viajeros internacionales a Guatemala por vía de ingreso")
st.caption(
    "Tablero de avance · Datos observados de la base de migración, "
    "enero 2009 a junio 2026. Haga clic en una columna del gráfico anual "
    "para ver ese año en el gráfico mensual."
)

# ------------------------------------------------------------------ controles
c1, c2, c3 = st.columns([2, 1, 2])
tipo = c1.selectbox("Tipo de viajero", tipos, key="tipo")
anio = c2.selectbox("Año (también puede elegirlo en el gráfico 1)",
                    años[::-1], key="anio")
detalle = c3.radio("Detalle del gráfico 2", ["Total", "Por vía"],
                   horizontal=True, key="detalle")

filtro = df if tipo == "Todos" else df[df["tipo"] == tipo]
disp = sorted(int(m) for m in df.loc[df["ano"] == anio, "mes"].unique())
parcial = len(disp) < 12

# --------------------------------------------------------- gráfico 1: anual
anual = filtro.groupby(["ano", "via"], as_index=False)["viajeros"].sum()
fig1 = go.Figure()
for via in VIAS:
    serie = (anual[anual["via"] == via].set_index("ano")["viajeros"]
             .reindex(años, fill_value=0))
    fig1.add_bar(x=años, y=serie.values, name=via, marker_color=COLOR_VIA[via],
                 hovertemplate=f"%{{x}} · {via}: %{{y:,.0f}} viajeros<extra></extra>")
fig1.add_vrect(x0=2019.5, x1=2021.5, layer="below", line_width=0,
               fillcolor="rgba(107,114,128,0.12)",
               annotation_text="Pandemia", annotation_position="top left")
fig1.add_vrect(x0=anio - 0.5, x1=anio + 0.5, layer="below",
               fillcolor="rgba(31,41,55,0.08)",
               line=dict(color=COLOR_TEXTO, width=1.5, dash="dot"))
fig1.update_layout(
    barmode="stack", height=430, margin=dict(t=50, r=10, b=60, l=60),
    legend=dict(orientation="h", y=1.12, x=0),
    plot_bgcolor="white", paper_bgcolor="white", font_color=COLOR_TEXTO,
    yaxis=dict(title="Viajeros", tickformat=".2s", rangemode="tozero"),
    xaxis=dict(tickmode="array", tickvals=años,
               ticktext=[f"{a}*" if a == 2026 else str(a) for a in años],
               tickangle=-45, title=""),
)

# ------------------------------------------------------- gráfico 2: mensual
def serie_mensual(datos: pd.DataFrame) -> pd.Series:
    s = (datos.groupby("mes")["viajeros"].sum()
         .reindex(range(1, 13), fill_value=0).astype(float))
    s[~s.index.isin(disp)] = float("nan")  # meses sin datos: no se dibujan
    return s


ref = (filtro[filtro["ano"].isin(AÑOS_REF)].groupby("mes")["viajeros"].sum()
       .reindex(range(1, 13), fill_value=0) / len(AÑOS_REF))

fig2 = go.Figure()
datos_anio = filtro[filtro["ano"] == anio]
if detalle == "Total":
    fig2.add_scatter(x=MESES, y=serie_mensual(datos_anio).values,
                     mode="lines+markers", name=str(anio),
                     line=dict(color=COLOR_TEXTO, width=3), marker=dict(size=7),
                     hovertemplate="%{x} " + str(anio) + ": %{y:,.0f}<extra></extra>")
else:
    for via in VIAS:
        fig2.add_scatter(x=MESES,
                         y=serie_mensual(datos_anio[datos_anio["via"] == via]).values,
                         mode="lines+markers", name=via,
                         line=dict(color=COLOR_VIA[via], width=3), marker=dict(size=7),
                         hovertemplate="%{x} · " + via + ": %{y:,.0f}<extra></extra>")
fig2.add_scatter(x=MESES, y=ref.values, mode="lines",
                 name="Promedio 2015–2019 (referencia)",
                 line=dict(color=COLOR_REF, width=2, dash="dash"),
                 hovertemplate="Promedio 2015–2019 · %{x}: %{y:,.0f}<extra></extra>")
fig2.update_layout(
    height=430, margin=dict(t=50, r=10, b=40, l=60), hovermode="x unified",
    legend=dict(orientation="h", y=1.12, x=0),
    plot_bgcolor="white", paper_bgcolor="white", font_color=COLOR_TEXTO,
    yaxis=dict(title="Viajeros por mes", tickformat=".2s", rangemode="tozero"),
)

total_anio = int(datos_anio["viajeros"].sum())
if total_anio == 0:
    fig2.add_annotation(text=f"Sin registros de «{tipo}» en {anio}",
                        xref="paper", yref="paper", x=0.5, y=0.5,
                        showarrow=False, font=dict(size=16, color=COLOR_REF))

# -------------------------------------------------- resumen y tarjetas (datos)
real = int(filtro[(filtro["ano"] == anio) & (filtro["mes"].isin(disp))]["viajeros"].sum())
ref_periodo = float(ref.loc[disp].sum())
variacion = (real / ref_periodo - 1) * 100 if ref_periodo > 0 else None
periodo = "todo el año" if not parcial else f"enero a {MESES[max(disp) - 1].lower()}"
etiqueta_tipo = "" if tipo == "Todos" else f" ({tipo.lower()})"

k1, k2 = st.columns(2)
k1.metric(f"Viajeros en {anio}{' (parcial)' if parcial else ''}{etiqueta_tipo}",
          f"{real:,.0f}")
k2.metric("Variación frente a 2015–2019 (mismo periodo)",
          "Sin referencia" if variacion is None else f"{variacion:+.1f} %",
          help="Compara los viajeros del año elegido con el promedio de 2015–2019 "
               "para los mismos meses. Es una comparación observada, no una predicción.")

st.info(
    f"**Hallazgo observado:** en {anio} ({periodo}) se registraron {real:,.0f} viajeros"
    f"{etiqueta_tipo}. "
    + ("" if variacion is None else
       f"Frente al mismo periodo del promedio 2015–2019, la diferencia es de "
       f"{variacion:+.1f} %. ")
    + "Estas diferencias se describen, no se atribuyen a causas específicas."
)

# ----------------------------------------------------------- disposición
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. ¿Cómo cambia el flujo anual por vía de ingreso?")
    st.caption("Viajeros por año, apilados por vía. Clic en una columna para elegir "
               "ese año. Sombreado gris: pandemia (2020–2021). *2026 = enero a junio.")
    st.plotly_chart(fig1, key="grafico_anual", on_select=al_elegir_anio,
                    selection_mode="points", width="stretch")
with col2:
    st.subheader(f"2. ¿En qué meses se concentra el flujo de {anio}?")
    st.caption("Viajeros por mes del año elegido. La línea gris punteada es el "
               "promedio de 2015–2019, usado como referencia prepandemia.")
    st.plotly_chart(fig2, key="grafico_mensual", width="stretch")

with st.expander("Términos y cómo usar el tablero"):
    st.markdown(
        "- **Vía de ingreso:** forma en que el viajero entra al país: terrestre, "
        "aérea o marítima.\n"
        "- **Tipo de viajero:** categoría de la base de migración (turista, viajero, "
        "excursionista, cruceristas). Use el filtro superior para ver una sola categoría.\n"
        "- **Promedio 2015–2019:** referencia histórica anterior a la pandemia. "
        "No es un pronóstico.\n"
        "- **Uso:** seleccione un año en el gráfico 1 y observe en el gráfico 2 "
        "cuándo se concentra el flujo y cómo se compara con la referencia."
    )

st.caption(
    "Fuente: Base_Migracion_2009-2026jun (Laboratorio 1). Colores: paleta Okabe-Ito, "
    "apta para daltonismo; cada color identifica una vía en todo el tablero. "
    "Este avance no incluye modelos predictivos."
)
