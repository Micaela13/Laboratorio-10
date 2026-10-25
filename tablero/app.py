"""Tablero final – Observatorio de Turismo Sostenible (Laboratorio 10).

Pestaña «Flujo de viajeros»: 8 visualizaciones interactivas; el usuario elige cuáles ver.
  Enlaces: clic en una columna del gráfico 1 = elegir año (gráficos 2–4, 6–8);
           clic en un país del gráfico 4 = elegir país (gráfico 5).
Pestaña «Comparación de modelos»: resultados del Laboratorio 1 (Prophet, ARIMA,
  Holt-Winters, ETS, Seasonal Naive). Solo se leen CSV exportados; no se reentrena.

Ejecutar:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATOS = Path(__file__).parent / "data"

VIAS = ["Terrestre", "Aérea", "Marítima"]
# Paleta Okabe-Ito (apta para daltonismo). Cada color = una vía en todo el tablero.
COLOR_VIA = {"Terrestre": "#0072B2", "Aérea": "#E69F00", "Marítima": "#009E73"}
# Las regiones usan los colores Okabe-Ito que no ocupan las vías.
COLOR_REGION = {"Centroamérica": "#56B4E9", "Norteamérica": "#D55E00",
                "Europa": "#CC79A7", "Sudamérica": "#F0E442",
                "Resto del mundo": "#999999"}
# En la pestaña de modelos el color identifica el modelo; negro = dato real.
COLOR_MODELO = {"Prophet": "#0072B2", "ARIMA": "#D55E00", "Holt-Winters": "#009E73",
                "ETS": "#CC79A7", "Seasonal Naive": "#E69F00"}
COLOR_TEXTO = "#1F2937"
COLOR_REF = "#6B7280"
COLOR_RESALTE = "#D55E00"
ESCALA_DIVERGENTE = [[0, "#56B4E9"], [0.5, "#F7F7F7"], [1, "#D55E00"]]
ESCALA_ERROR = [[0, "#FFFFFF"], [1, "#D55E00"]]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
AÑOS_REF = [2015, 2016, 2017, 2018, 2019]
ANIO_DEFECTO = 2025

st.set_page_config(page_title="Viajeros a Guatemala 2009–2026", layout="wide")


@st.cache_data
def cargar(nombre: str) -> pd.DataFrame | None:
    ruta = DATOS / nombre
    return pd.read_csv(ruta) if ruta.exists() else None


def estilo(fig: go.Figure, alto: int = 420, **kw) -> go.Figure:
    base = dict(height=alto, margin=dict(t=50, r=10, b=40, l=60),
                legend=dict(orientation="h", y=1.12, x=0), showlegend=True,
                plot_bgcolor="white", paper_bgcolor="white", font_color=COLOR_TEXTO)
    fig.update_layout(**(base | kw))
    return fig


def sin_datos(motivo: str) -> None:
    st.info(f"**Sin datos para mostrar.** {motivo} Pruebe con otro año o tipo de viajero.")


def puntos(clave: str) -> list:
    return (st.session_state.get(clave) or {}).get("selection", {}).get("points", [])


def al_elegir_anio() -> None:
    """Callback del gráfico anual: el año clicado pasa a ser el año de todo el tablero."""
    if p := puntos("grafico_anual"):
        st.session_state["anio"] = int(p[0]["x"])


def al_elegir_pais() -> None:
    """Callback del gráfico de países: el país clicado pasa al gráfico de tendencia."""
    if p := puntos("grafico_paises"):
        st.session_state["pais"] = p[0]["y"]


df = cargar("migracion_agregada.csv")
paises = cargar("paises_anual.csv")
fronteras = cargar("fronteras_mensual.csv")
if df is None or paises is None or fronteras is None:
    st.error("Faltan los datos del tablero en `data/`. Ejecute "
             "`python preparar_datos.py ruta/Base_Migracion_2009-2026jun.xlsx`.")
    st.stop()

años = sorted(int(a) for a in df["ano"].unique())
meses_por_anio = df.groupby("ano")["mes"].unique()
parcial_ultimo = len(meses_por_anio[años[-1]]) < 12
st.session_state.setdefault("anio", ANIO_DEFECTO)

# ---------------------------------------------------------------- encabezado
st.title("Viajeros internacionales a Guatemala")
st.caption("Observatorio de Turismo Sostenible · Base de migración, enero 2009 a junio 2026 "
           "· Laboratorio 10 (CC3066)")

tab_flujo, tab_modelos = st.tabs(["Flujo de viajeros", "Comparación de modelos (Lab 1)"])

# =================================================================== FLUJO
with tab_flujo:
    c1, c2, c3 = st.columns([2, 1, 2])
    tipo = c1.selectbox("Tipo de viajero", ["Todos"] + sorted(df["tipo"].unique()),
                        key="tipo")
    anio = c2.selectbox("Año (también con clic en el gráfico 1)", años[::-1], key="anio")
    detalle = c3.radio("Detalle del gráfico 2", ["Total", "Por vía"],
                       horizontal=True, key="detalle")

    def por_tipo(d: pd.DataFrame) -> pd.DataFrame:
        return d if tipo == "Todos" else d[d["tipo"] == tipo]

    filtro, f_paises, f_fronteras = por_tipo(df), por_tipo(paises), por_tipo(fronteras)
    disp = sorted(int(m) for m in meses_por_anio[anio])
    parcial = len(disp) < 12
    periodo = "todo el año" if not parcial else f"enero a {MESES[max(disp) - 1].lower()}"
    etiqueta_tipo = "" if tipo == "Todos" else f" ({tipo.lower()})"

    # Índice frente al promedio 2015–2019 en los mismos meses (100 = nivel prepandemia).
    real_via = (filtro.groupby(["ano", "via"])["viajeros"].sum().unstack(fill_value=0)
                .reindex(index=años, fill_value=0))
    ref_mes = (filtro[filtro["ano"].isin(AÑOS_REF)].groupby(["mes", "via"])["viajeros"]
               .sum().unstack(fill_value=0).reindex(range(1, 13), fill_value=0)
               / len(AÑOS_REF))
    ref_via = pd.DataFrame({a: ref_mes.loc[m].sum() for a, m in meses_por_anio.items()}).T
    ref_via = ref_via.reindex(index=años, columns=real_via.columns, fill_value=0)
    indice_via = real_via / ref_via.where(ref_via > 0) * 100
    ref_total = ref_via.sum(axis=1)
    indice_total = real_via.sum(axis=1) / ref_total.where(ref_total > 0) * 100

    # País elegido (gráficos 4 y 5): se conserva si existe para el filtro actual.
    opciones_pais = (f_paises.groupby("pais")["viajeros"].sum()
                     .sort_values(ascending=False).index.tolist())
    top_anio = (f_paises[f_paises["ano"] == anio].groupby("pais")["viajeros"].sum()
                .nlargest(10).sort_values())
    if opciones_pais and st.session_state.get("pais") not in opciones_pais:
        st.session_state["pais"] = top_anio.index[-1] if len(top_anio) else opciones_pais[0]
    pais = st.session_state.get("pais")

    # ------------------------------------------------------ tarjetas resumen
    real = int(filtro.loc[filtro["ano"] == anio, "viajeros"].sum())
    variacion = indice_total.get(anio, float("nan")) - 100
    k1, k2, k3 = st.columns(3)
    k1.metric(f"Viajeros en {anio}{' (parcial)' if parcial else ''}{etiqueta_tipo}",
              f"{real:,.0f}")
    k2.metric("Frente al promedio 2015–2019 (mismos meses)",
              "Sin referencia" if pd.isna(variacion) else f"{variacion:+.1f} %",
              help="Compara el año elegido con el promedio de 2015–2019 en los mismos "
                   "meses. Es una comparación observada, no una predicción.")
    k3.metric(f"Principal país de origen en {anio}",
              top_anio.index[-1] if len(top_anio) else "Sin datos")

    # --------------------------------------------------------- gráficas
    def g_anual() -> None:
        st.subheader("1. ¿Cómo cambia el flujo anual por vía de ingreso?")
        st.caption("Viajeros por año, apilados por vía. **Clic en una columna** para elegir "
                   "ese año en todo el tablero. Gris: pandemia. *2026 = enero a junio.")
        if filtro["viajeros"].sum() == 0:
            return sin_datos(f"No hay registros de «{tipo}».")
        fig = go.Figure()
        for via in [v for v in VIAS if v in real_via]:
            fig.add_bar(x=años, y=real_via[via], name=via, marker_color=COLOR_VIA[via],
                        hovertemplate=f"%{{x}} · {via}: %{{y:,.0f}} viajeros<extra></extra>")
        fig.add_vrect(x0=2019.5, x1=2021.5, layer="below", line_width=0,
                      fillcolor="rgba(107,114,128,0.12)",
                      annotation_text="Pandemia", annotation_position="top left")
        fig.add_vrect(x0=anio - 0.5, x1=anio + 0.5, layer="below",
                      fillcolor="rgba(31,41,55,0.08)",
                      line=dict(color=COLOR_TEXTO, width=1.5, dash="dot"))
        estilo(fig, barmode="stack", margin=dict(t=50, r=10, b=60, l=60),
               yaxis=dict(title="Viajeros", tickformat=".2s", rangemode="tozero"),
               xaxis=dict(tickmode="array", tickvals=años, tickangle=-45, title="",
                          ticktext=[f"{a}*" if a == 2026 else str(a) for a in años]))
        st.plotly_chart(fig, key="grafico_anual", on_select=al_elegir_anio,
                        selection_mode="points", width="stretch")

    def g_mensual() -> None:
        st.subheader(f"2. ¿En qué meses se concentra el flujo de {anio}?")
        st.caption("Viajeros por mes del año elegido. Línea gris punteada: promedio "
                   "2015–2019, referencia prepandemia (no es un pronóstico).")
        datos_anio = filtro[filtro["ano"] == anio]
        if datos_anio["viajeros"].sum() == 0:
            return sin_datos(f"No hay registros de «{tipo}» en {anio}.")

        def serie_mensual(datos: pd.DataFrame) -> pd.Series:
            s = (datos.groupby("mes")["viajeros"].sum()
                 .reindex(range(1, 13), fill_value=0).astype(float))
            s[~s.index.isin(disp)] = float("nan")  # meses sin datos: no se dibujan
            return s

        fig = go.Figure()
        if detalle == "Total":
            fig.add_scatter(x=MESES, y=serie_mensual(datos_anio).values,
                            mode="lines+markers", name=str(anio),
                            line=dict(color=COLOR_TEXTO, width=3), marker=dict(size=7),
                            hovertemplate="%{x} " + str(anio) + ": %{y:,.0f}<extra></extra>")
        else:
            for via in VIAS:
                fig.add_scatter(x=MESES,
                                y=serie_mensual(datos_anio[datos_anio["via"] == via]).values,
                                mode="lines+markers", name=via,
                                line=dict(color=COLOR_VIA[via], width=3), marker=dict(size=7),
                                hovertemplate="%{x} · " + via + ": %{y:,.0f}<extra></extra>")
        ref = ref_mes.sum(axis=1)
        fig.add_scatter(x=MESES, y=ref.values, mode="lines",
                        name="Promedio 2015–2019 (referencia)",
                        line=dict(color=COLOR_REF, width=2, dash="dash"),
                        hovertemplate="Promedio 2015–2019 · %{x}: %{y:,.0f}<extra></extra>")
        estilo(fig, hovermode="x unified",
               yaxis=dict(title="Viajeros por mes", tickformat=".2s", rangemode="tozero"))
        st.plotly_chart(fig, key="grafico_mensual", width="stretch")
        mes_max = serie_mensual(datos_anio).idxmax()
        st.markdown(f"**Lectura:** en {anio} ({periodo}) el mes con más viajeros fue "
                    f"**{MESES[mes_max - 1]}**.")

    def g_calor() -> None:
        st.subheader("3. ¿Se repite cada año el mismo patrón de meses altos y bajos?")
        st.caption("Índice mensual: 100 = mes promedio de ese año. Naranja = mes por encima "
                   "del promedio; celeste = por debajo. El año elegido aparece enmarcado. "
                   "2026 se compara con su promedio de enero a junio.")
        m = (filtro.groupby(["ano", "mes"])["viajeros"].sum().unstack()
             .reindex(columns=range(1, 13)))
        m = m[m.sum(axis=1) > 0]
        if m.empty:
            return sin_datos(f"No hay registros de «{tipo}».")
        pct = m.div(m.mean(axis=1), axis=0) * 100
        # Escala fija 50–150: 2020 (pandemia) satura sin opacar los demás años.
        fig = go.Figure(go.Heatmap(
            z=pct.values, x=MESES, y=pct.index, customdata=m.values,
            colorscale=ESCALA_DIVERGENTE, zmin=50, zmid=100, zmax=150,
            colorbar=dict(title="Índice", tickvals=[50, 75, 100, 125, 150],
                          ticktext=["≤50", "75", "100", "125", "≥150"]),
            hovertemplate="%{x} %{y}: %{customdata:,.0f} viajeros "
                          "(índice %{z:.0f})<extra></extra>"))
        if anio in pct.index:
            fig.add_shape(type="rect", x0=-0.5, x1=11.5, y0=anio - 0.5, y1=anio + 0.5,
                          line=dict(color=COLOR_TEXTO, width=2))
        estilo(fig, alto=480, showlegend=False, margin=dict(t=40, r=10, b=10, l=50),
               yaxis=dict(autorange="reversed", dtick=1, title=""),
               xaxis=dict(title="", side="top"))
        st.plotly_chart(fig, key="grafico_calor", width="stretch")
        promedio = pct.loc[pct.index.isin(AÑOS_REF)].mean()
        if promedio.notna().any():
            st.markdown("**Lectura:** en 2015–2019 los meses más altos fueron "
                        f"**{' y '.join(MESES[i - 1] for i in promedio.nlargest(2).index)}**; "
                        f"el más bajo, **{MESES[promedio.idxmin() - 1]}**.")

    def g_paises() -> None:
        st.subheader(f"4. ¿De qué países llegan más viajeros en {anio}?")
        st.caption("Los 10 países de residencia con más viajeros en el año elegido. "
                   "**Clic en una barra** para ver la tendencia de ese país en el gráfico 5.")
        if top_anio.empty:
            return sin_datos(f"No hay registros de «{tipo}» en {anio}.")
        total = f_paises.loc[f_paises["ano"] == anio, "viajeros"].sum()
        fig = go.Figure(go.Bar(
            x=top_anio.values, y=top_anio.index, orientation="h",
            marker_color=[COLOR_RESALTE if p == pais else COLOR_REF for p in top_anio.index],
            customdata=top_anio.values / total * 100,
            hovertemplate="%{y}: %{x:,.0f} viajeros (%{customdata:.1f} % del año)"
                          "<extra></extra>"))
        estilo(fig, showlegend=False, margin=dict(t=20, r=10, b=40, l=10),
               xaxis=dict(title="Viajeros", tickformat=".2s"), yaxis=dict(automargin=True))
        st.plotly_chart(fig, key="grafico_paises", on_select=al_elegir_pais,
                        selection_mode="points", width="stretch")
        st.markdown(f"**Lectura:** {top_anio.index[-1]} aporta el "
                    f"**{top_anio.iloc[-1] / total * 100:.0f} %** de los viajeros de {anio}; "
                    f"los 10 primeros suman el {top_anio.sum() / total * 100:.0f} %.")

    def g_pais_tendencia() -> None:
        st.subheader("5. ¿Cómo ha evolucionado el país elegido?")
        st.caption("Viajeros por año del país seleccionado, por vía de ingreso. "
                   "Elíjalo aquí o con clic en el gráfico 4. *2026 = enero a junio.")
        if not opciones_pais:
            return sin_datos(f"No hay registros de «{tipo}».")
        elegido = st.selectbox("País de residencia", opciones_pais, key="pais")
        datos = (f_paises[f_paises["pais"] == elegido]
                 .groupby(["ano", "via"])["viajeros"].sum().unstack(fill_value=0)
                 .reindex(años, fill_value=0))
        fig = go.Figure()
        for via in [v for v in VIAS if v in datos and datos[v].sum() > 0]:
            fig.add_scatter(x=años, y=datos[via], name=via, mode="lines+markers",
                            line=dict(color=COLOR_VIA[via], width=3),
                            hovertemplate=f"%{{x}} · {via}: %{{y:,.0f}}<extra></extra>")
        fig.add_vrect(x0=2019.5, x1=2021.5, layer="below", line_width=0,
                      fillcolor="rgba(107,114,128,0.12)",
                      annotation_text="Pandemia", annotation_position="top left")
        if parcial_ultimo:
            fig.add_vrect(x0=años[-1] - 0.5, x1=años[-1] + 0.5, layer="below", line_width=0,
                          fillcolor="rgba(230,159,0,0.10)",
                          annotation_text="Ene–Jun", annotation_position="top right")
        estilo(fig, hovermode="x unified",
               yaxis=dict(title="Viajeros", tickformat=".2s", rangemode="tozero"),
               xaxis=dict(dtick=2, title="", range=[años[0] - 0.5, años[-1] + 0.5]))
        st.plotly_chart(fig, key="grafico_pais", width="stretch")

    def g_fronteras() -> None:
        st.subheader(f"6. ¿Por qué puntos de ingreso entran los viajeros en {anio}?")
        st.caption("Los 10 puestos fronterizos, aeropuertos y puertos con más ingresos en "
                   "el año elegido; el color indica la vía.")
        d = (f_fronteras[f_fronteras["ano"] == anio]
             .groupby(["frontera", "via"])["viajeros"].sum().unstack(fill_value=0))
        if d.empty or d.values.sum() == 0:
            return sin_datos(f"No hay registros de «{tipo}» en {anio}.")
        total = d.values.sum()
        d = d.loc[d.sum(axis=1).nlargest(10).sort_values().index]
        fig = go.Figure()
        for via in [v for v in VIAS if v in d and d[v].sum() > 0]:
            fig.add_bar(x=d[via], y=d.index, orientation="h", name=via,
                        marker_color=COLOR_VIA[via], customdata=d[via] / total * 100,
                        hovertemplate="%{y} · " + via + ": %{x:,.0f} viajeros "
                                      "(%{customdata:.1f} % del año)<extra></extra>")
        estilo(fig, barmode="stack", margin=dict(t=50, r=10, b=40, l=10),
               xaxis=dict(title="Viajeros", tickformat=".2s"), yaxis=dict(automargin=True))
        st.plotly_chart(fig, key="grafico_fronteras", width="stretch")
        st.markdown(f"**Lectura:** {d.index[-1]} concentra el "
                    f"**{d.iloc[-1].sum() / total * 100:.0f} %** de los ingresos de {anio}.")

    def g_regiones() -> None:
        st.subheader("7. ¿Cambia la mezcla de regiones de origen?")
        st.caption("Participación de cada región de residencia en el total de cada año. "
                   "Clic en la leyenda para ocultar o mostrar una región.")
        d = (f_paises.groupby(["ano", "region"])["viajeros"].sum().unstack(fill_value=0)
             .reindex(columns=list(COLOR_REGION), fill_value=0))
        d = d[d.sum(axis=1) > 0]
        if d.empty:
            return sin_datos(f"No hay registros de «{tipo}».")
        pct = d.div(d.sum(axis=1), axis=0) * 100
        fig = go.Figure()
        for region, color in COLOR_REGION.items():
            fig.add_bar(x=pct.index, y=pct[region], name=region, marker_color=color,
                        customdata=d[region],
                        hovertemplate=f"%{{x}} · {region}: %{{y:.1f}} % "
                                      f"(%{{customdata:,.0f}} viajeros)<extra></extra>")
        if anio in pct.index:
            fig.add_vrect(x0=anio - 0.5, x1=anio + 0.5, fillcolor="rgba(0,0,0,0)",
                          line=dict(color=COLOR_TEXTO, width=1.5, dash="dot"))
        estilo(fig, barmode="stack",
               legend=dict(orientation="h", y=1.15, x=0, traceorder="normal"),
               yaxis=dict(title="% de viajeros del año", range=[0, 100], ticksuffix=" %"),
               xaxis=dict(dtick=2, title=""))
        st.plotly_chart(fig, key="grafico_regiones", width="stretch")
        if anio in pct.index:
            st.markdown(f"**Lectura:** en {anio}, Centroamérica representa el "
                        f"**{pct.loc[anio, 'Centroamérica']:.0f} %** y Norteamérica el "
                        f"**{pct.loc[anio, 'Norteamérica']:.0f} %** de los viajeros.")

    def g_recuperacion() -> None:
        st.subheader("8. ¿Cada vía ya recuperó su nivel prepandemia?")
        st.caption("Índice = viajeros del año ÷ promedio 2015–2019 en los mismos meses × 100. "
                   "Sobre 100 = más viajeros que antes de la pandemia.")
        if indice_total.dropna().empty:
            return sin_datos(f"No hay referencia 2015–2019 para «{tipo}».")
        fig = go.Figure()
        fig.add_scatter(x=años, y=indice_total, name="Total", mode="lines+markers",
                        line=dict(color=COLOR_TEXTO, width=3),
                        hovertemplate="%{x} · Total: %{y:.0f}<extra></extra>")
        for via in [v for v in VIAS if v in indice_via and indice_via[v].notna().any()]:
            fig.add_scatter(x=años, y=indice_via[via], name=via, mode="lines+markers",
                            line=dict(color=COLOR_VIA[via], width=2),
                            hovertemplate=f"%{{x}} · {via}: %{{y:.0f}}<extra></extra>")
        fig.add_hline(y=100, line=dict(color=COLOR_REF, dash="dash"),
                      annotation_text="Nivel 2015–2019 = 100",
                      annotation_position="top left")
        fig.add_vline(x=anio, line=dict(color=COLOR_TEXTO, width=1, dash="dot"))
        estilo(fig, hovermode="x unified", yaxis=dict(title="Índice (2015–2019 = 100)"),
               xaxis=dict(dtick=2, title=""))
        st.plotly_chart(fig, key="grafico_recuperacion", width="stretch")
        valor = indice_total.get(anio)
        if pd.notna(valor):
            st.markdown(f"**Lectura:** en {anio} ({periodo}) el flujo total está en "
                        f"**{valor:.0f}** puntos, "
                        + ("por encima" if valor >= 100 else "por debajo")
                        + " del nivel prepandemia.")

    GRAFICAS = {
        "1. Flujo anual por vía": g_anual,
        "2. Flujo mensual del año": g_mensual,
        "3. Mapa de calor de estacionalidad": g_calor,
        "4. Principales países de origen": g_paises,
        "5. Tendencia del país elegido": g_pais_tendencia,
        "6. Puntos de ingreso (fronteras)": g_fronteras,
        "7. Región de origen": g_regiones,
        "8. Recuperación frente a 2015–2019": g_recuperacion,
    }
    elegidas = st.multiselect("Gráficas a mostrar", list(GRAFICAS),
                              default=list(GRAFICAS), key="graficas",
                              help="Quite o agregue gráficas según la pregunta que quiera "
                                   "responder. Se muestran siempre en el mismo orden.")
    if not elegidas:
        st.warning("No hay gráficas seleccionadas. Elija al menos una en «Gráficas a mostrar».")
    elegidas = [g for g in GRAFICAS if g in elegidas]
    for i in range(0, len(elegidas), 2):
        for col, nombre in zip(st.columns(2), elegidas[i:i + 2]):
            with col:
                GRAFICAS[nombre]()

    with st.expander("Términos y cómo usar el tablero"):
        st.markdown(
            "- **Vía de ingreso:** forma en que el viajero entra al país: terrestre, "
            "aérea o marítima.\n"
            "- **Tipo de viajero:** categoría de la base de migración (turista, viajero, "
            "excursionista, cruceristas).\n"
            "- **País / región de residencia:** donde vive el viajero, no su nacionalidad.\n"
            "- **Promedio 2015–2019:** referencia histórica anterior a la pandemia. "
            "No es un pronóstico.\n"
            "- **Uso:** elija qué gráficas ver; haga clic en un año (gráfico 1) o en un país "
            "(gráfico 4) y el resto del tablero se actualiza."
        )
    st.caption("Fuente: Base_Migracion_2009-2026jun (Laboratorio 1). Colores Okabe-Ito, aptos "
               "para daltonismo; cada color identifica la misma vía en todo el tablero. "
               "Las diferencias se describen; no se atribuyen a causas específicas.")

# ================================================================= MODELOS
with tab_modelos:
    met = cargar("metricas_lab1.csv")
    pred = cargar("predicciones_lab1.csv")
    car = cargar("series_lab1.csv")
    if met is None or pred is None:
        st.warning("No se encontraron los resultados del Laboratorio 1. Ejecute "
                   "`Rscript exportar_lab1.R Laboratorio_1.Rmd Base_Migracion.xlsx`.")
        st.stop()

    st.markdown(
        "Resultados del **Laboratorio 1**: cinco modelos de series de tiempo pronosticaron "
        "el **último 30 %** de cada serie mensual, un periodo que no vieron al ajustarse. "
        "Aquí solo se muestran esos resultados; **no se reentrena ningún modelo**. "
        "El **error típico (RMSE)** indica, en viajeros por mes, cuánto se equivocó cada "
        "modelo: **menor es mejor**."
    )
    series = met["serie"].unique().tolist()
    modelos_todos = list(COLOR_MODELO)
    c1, c2 = st.columns([1, 2])
    serie = c1.selectbox("Serie analizada", series, key="serie_modelo")
    modelos = c2.multiselect("Modelos a comparar", modelos_todos, default=modelos_todos,
                             key="modelos")
    if not modelos:
        st.warning("Elija al menos un modelo en «Modelos a comparar».")
        st.stop()
    orden_modelos = [m for m in modelos_todos if m in modelos]

    real_prueba = pred[(pred["tramo"] == "Prueba") & (pred["modelo"] == "Real")]
    met = met.assign(error_pct=met["RMSE"]
                     / met["serie"].map(real_prueba.groupby("serie")["valor"].mean()) * 100)
    p = pred[pred["serie"] == serie].assign(fecha=lambda d: pd.to_datetime(d["fecha"]))
    prueba = p[(p["tramo"] == "Prueba") & (p["modelo"] == "Real")]
    m = met[(met["serie"] == serie) & met["modelo"].isin(modelos)].sort_values("RMSE")
    ganador = m.iloc[0]
    inicio, fin = prueba["fecha"].min(), prueba["fecha"].max()

    k1, k2, k3 = st.columns(3)
    k1.metric("Modelo con menor error (entre los elegidos)", ganador["modelo"])
    k2.metric("Error típico mensual (RMSE)", f"{ganador['RMSE']:,.0f} viajeros",
              help="Raíz del error cuadrático medio en el periodo de prueba.")
    k3.metric("Error frente al flujo mensual promedio", f"{ganador['error_pct']:.0f} %",
              help="RMSE ÷ promedio mensual real del periodo de prueba "
                   f"({prueba['valor'].mean():,.0f} viajeros).")
    st.caption(f"Periodo de prueba de «{serie}»: {MESES[inicio.month - 1]} {inicio.year} a "
               f"{MESES[fin.month - 1]} {fin.year}. "
               + ("Coincide con la recuperación tras la pandemia y los modelos se ajustaron "
                  "con datos que incluyen la caída de 2020, lo que eleva los errores."
                  if inicio.year >= 2021 else ""))

    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("A. ¿Qué tan cerca estuvo cada pronóstico de lo real?")
        st.caption("Negro: viajeros reales. Colores: pronóstico de cada modelo en el periodo "
                   "de prueba (sombreado). Doble clic en el gráfico para ver toda la serie.")
        fig = go.Figure()
        real_s = p[p["modelo"] == "Real"].sort_values("fecha")
        fig.add_scatter(x=real_s["fecha"], y=real_s["valor"], name="Real",
                        line=dict(color="#000000", width=2.5),
                        hovertemplate="Real: %{y:,.0f}<extra></extra>")
        for modelo in orden_modelos:
            s = p[p["modelo"] == modelo].sort_values("fecha")
            fig.add_scatter(x=s["fecha"], y=s["valor"], name=modelo,
                            line=dict(color=COLOR_MODELO[modelo], width=2),
                            hovertemplate=f"{modelo}: %{{y:,.0f}}<extra></extra>")
        fig.add_vrect(x0=inicio, x1=fin, layer="below", line_width=0,
                      fillcolor="rgba(107,114,128,0.12)",
                      annotation_text="Periodo de prueba", annotation_position="top left")
        estilo(fig, alto=450, hovermode="x unified",
               yaxis=dict(title="Viajeros por mes", tickformat=".2s"),
               xaxis=dict(range=[inicio - pd.DateOffset(years=3), fin], title="",
                          hoverformat="%b %Y"))
        st.plotly_chart(fig, key="grafico_pronostico", width="stretch")
    with col2:
        st.subheader("B. ¿Qué modelo se equivocó menos?")
        st.caption("Error típico mensual (RMSE) de cada modelo en esta serie; la etiqueta "
                   "es el error frente al flujo mensual promedio.")
        fig = go.Figure(go.Bar(
            x=m["RMSE"], y=m["modelo"], orientation="h",
            marker_color=[COLOR_MODELO[x] for x in m["modelo"]],
            text=[f"{e:.0f} %" for e in m["error_pct"]], textposition="outside",
            cliponaxis=False,
            customdata=m[["MAE", "error_pct"]].values,
            hovertemplate="%{y}<br>RMSE: %{x:,.0f}<br>MAE: %{customdata[0]:,.0f}"
                          "<br>Error relativo: %{customdata[1]:.0f} %<extra></extra>"))
        estilo(fig, alto=450, margin=dict(t=20, r=60, b=40, l=10), showlegend=False,
               xaxis=dict(title="RMSE (viajeros por mes)", tickformat=".2s"),
               yaxis=dict(autorange="reversed", automargin=True))
        st.plotly_chart(fig, key="grafico_rmse", width="stretch")
        empate = m[m["RMSE"].round(2) == round(ganador["RMSE"], 2)]
        if len(empate) > 1:
            st.markdown(f"**Empate:** {' y '.join(empate['modelo'])} obtienen el mismo error.")

    st.subheader("C. ¿Hay un modelo que funcione bien en todas las series?")
    st.caption("Error relativo (RMSE ÷ flujo mensual promedio real) de cada modelo en cada "
               "serie. Más claro = mejor. ★ = menor error de la serie entre los elegidos. "
               "En la vía marítima el flujo reciente es muy bajo, por eso todos los errores "
               "relativos son altos.")
    tabla = (met[met["modelo"].isin(modelos)]
             .pivot(index="modelo", columns="serie", values="error_pct")
             .reindex(index=orden_modelos, columns=series))
    marca = tabla.eq(tabla.min())
    texto = tabla.round(0).astype(int).astype(str) + " %" + marca.map(lambda b: " ★" if b else "")
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=tabla.columns, y=tabla.index, text=texto.values,
        # Tope de color en 150 %: la vía marítima (flujo muy bajo tras 2021) no opaca al resto.
        texttemplate="%{text}", colorscale=ESCALA_ERROR, zmin=0, zmax=150,
        colorbar=dict(title="Error", tickvals=[0, 50, 100, 150],
                      ticktext=["0 %", "50 %", "100 %", "≥150 %"]),
        hovertemplate="%{x} · %{y}: error relativo %{z:.0f} %<extra></extra>"))
    estilo(fig, alto=140 + 45 * len(orden_modelos), showlegend=False,
           margin=dict(t=20, r=10, b=40, l=10), yaxis=dict(autorange="reversed", automargin=True))
    st.plotly_chart(fig, key="grafico_error_series", width="stretch")
    victorias = marca.sum(axis=1).sort_values(ascending=False)
    st.markdown(f"**Lectura:** **{victorias.index[0]}** tiene el menor error en "
                f"{victorias.iloc[0]} de {len(series)} series"
                + ("; ningún modelo gana en todas, así que conviene elegirlo según la serie "
                   "que se quiera pronosticar." if victorias.iloc[0] < len(series) else "."))

    with st.expander("Tabla completa de métricas del Laboratorio 1"):
        st.dataframe(
            m[["modelo", "MAE", "RMSE", "error_pct", "AIC", "BIC", "especificacion"]]
            .rename(columns={"modelo": "Modelo", "error_pct": "Error relativo (%)",
                             "especificacion": "Especificación"}),
            hide_index=True, width="stretch",
            column_config={c: st.column_config.NumberColumn(format="localized")
                           for c in ["MAE", "RMSE", "Error relativo (%)", "AIC", "BIC"]})
        st.caption("MAE: error absoluto medio. RMSE: raíz del error cuadrático medio (castiga "
                   "más los errores grandes). AIC/BIC solo aplican a ARIMA y ETS y comparan "
                   "modelos de la misma familia, no entre familias.")
    if car is not None:
        with st.expander("Características de cada serie (Laboratorio 1)"):
            st.dataframe(
                car.rename(columns={"serie": "Serie",
                                    "fuerza_estacional": "Fuerza estacional (0–1)",
                                    "fuerza_tendencia": "Fuerza de tendencia (0–1)",
                                    "volatilidad_cv": "Volatilidad (CV)",
                                    "caida_pandemia_pct": "Caída 2019→2020 (%)"}),
                hide_index=True, width="stretch")
            st.caption("Calculadas sobre el tramo de entrenamiento. Guatemala no tiene caída "
                       "2020 porque su tramo de entrenamiento termina en 2018.")
