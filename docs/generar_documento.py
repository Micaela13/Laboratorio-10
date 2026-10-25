"""Genera el documento de diseño del tablero (PDF) a partir de las capturas en img/.

Uso (desde docs/):  python generar_documento.py
Requiere: reportlab. Las capturas se toman del tablero en ejecución (streamlit run app.py).
"""
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

AQUI = Path(__file__).parent
IMG = AQUI / "img"
SALIDA = AQUI / "Documento_de_diseno_tablero.pdf"

# Arial (Windows) cubre ≥, ÷, → ; si no existe se usa Helvetica.
FUENTES = Path("C:/Windows/Fonts")
if (FUENTES / "arial.ttf").exists():
    pdfmetrics.registerFont(TTFont("Texto", str(FUENTES / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Texto-B", str(FUENTES / "arialbd.ttf")))
    pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-B")
    NORMAL, NEGRITA = "Texto", "Texto-B"
else:
    NORMAL, NEGRITA = "Helvetica", "Helvetica-Bold"

TEXTO = colors.HexColor("#1F2937")
GRIS = colors.HexColor("#6B7280")
AZUL = colors.HexColor("#0072B2")

base = getSampleStyleSheet()
E = {
    "titulo": ParagraphStyle("titulo", fontName=NEGRITA, fontSize=22, leading=27,
                             textColor=TEXTO, spaceAfter=6),
    "sub": ParagraphStyle("sub", fontName=NORMAL, fontSize=11, leading=15, textColor=GRIS,
                          spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName=NEGRITA, fontSize=15, leading=19, textColor=AZUL,
                         spaceBefore=14, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName=NEGRITA, fontSize=11.5, leading=15, textColor=TEXTO,
                         spaceBefore=8, spaceAfter=4),
    "p": ParagraphStyle("p", parent=base["BodyText"], fontName=NORMAL, fontSize=10,
                        leading=14, textColor=TEXTO, spaceAfter=6),
    "li": ParagraphStyle("li", fontName=NORMAL, fontSize=10, leading=14, textColor=TEXTO,
                         leftIndent=12, bulletIndent=2, spaceAfter=3),
    "pie": ParagraphStyle("pie", fontName=NORMAL, fontSize=8.5, leading=11, textColor=GRIS,
                          alignment=TA_CENTER, spaceBefore=3, spaceAfter=10),
    "celda": ParagraphStyle("celda", fontName=NORMAL, fontSize=8.5, leading=11,
                            textColor=TEXTO),
    "celda_b": ParagraphStyle("celda_b", fontName=NEGRITA, fontSize=8.5, leading=11,
                              textColor=colors.white),
}
ANCHO = A4[0] - 4 * cm


def p(texto: str) -> Paragraph:
    return Paragraph(texto, E["p"])


def lista(items: list[str]) -> list[Paragraph]:
    return [Paragraph(i, E["li"], bulletText="•") for i in items]


def figura(nombre: str, pie: str, arriba: float = 0.075, abajo: float = 1.0) -> KeepTogether:
    """Captura recortada (fracción de alto): quita la barra de Streamlit y cortes de sección."""
    with PILImage.open(IMG / nombre) as orig:
        w, alto = orig.size
        buf = BytesIO()
        orig.crop((0, int(alto * arriba), w, int(alto * abajo))).save(buf, "PNG")
    buf.seek(0)
    img = Image(buf)
    img.drawHeight = img.imageHeight * ANCHO / img.imageWidth
    img.drawWidth = ANCHO
    return KeepTogether([img, Paragraph(pie, E["pie"])])


def tabla(filas: list[list[str]], anchos: list[float]) -> Table:
    datos = [[Paragraph(c, E["celda_b"] if i == 0 else E["celda"]) for c in fila]
             for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=[a * cm for a in anchos], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEXTO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def muestras(pares: list[tuple[str, str]]) -> Table:
    """Tabla de colores: muestra, hex, uso."""
    t = tabla([["", "Color", "Uso en el tablero"]] + [["", h, u] for h, u in pares],
              [1.0, 2.2, 13.8])
    t.setStyle(TableStyle([("BACKGROUND", (0, i + 1), (0, i + 1), colors.HexColor(h))
                           for i, (h, _) in enumerate(pares)]))
    return t


def pie_pagina(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(NORMAL, 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.2 * cm, "Laboratorio 10 · CC3066 · Documento de diseño del tablero")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


h = [
    Paragraph("Tablero de viajeros internacionales a Guatemala", E["titulo"]),
    Paragraph("Documento de diseño · Laboratorio 10 (CC3066) · Observatorio de Turismo "
              "Sostenible · Datos: base de migración, enero 2009 a junio 2026<br/>"
              "Integrantes: Micaela Yataz, Carlos Aldana, Dolan Cuellar y Daniel Sarmiento",
              E["sub"]),

    Paragraph("1. Propósito y público", E["h1"]),
    p("El tablero resume el flujo de viajeros internacionales que ingresan a Guatemala para "
      "<b>directivos y tomadores de decisión</b> del sector turismo. No requiere conocimientos "
      "de estadística: cada gráfica se titula con la pregunta que responde, incluye una línea "
      "de <b>lectura</b> en lenguaje llano con la cifra principal y evita jerga técnica "
      "(por ejemplo, «error típico mensual» en lugar de «RMSE» en los encabezados)."),
    p("Tiene dos pestañas: <b>Flujo de viajeros</b>, con 8 visualizaciones interactivas sobre "
      "los datos observados, y <b>Comparación de modelos</b>, que reutiliza los pronósticos y "
      "métricas del Laboratorio 1 (Prophet, ARIMA, Holt-Winters, ETS y Seasonal Naive) "
      "sin reentrenar ningún modelo."),

    Paragraph("2. Preguntas que responde", E["h1"]),
    tabla([
        ["#", "Pregunta para el directivo", "Gráfica y codificación", "Interacción"],
        ["1", "¿Cómo cambia el flujo anual por vía de ingreso?",
         "Columnas apiladas por año; color = vía. Sombreado gris = pandemia.",
         "Clic en una columna elige el año de todo el tablero."],
        ["2", "¿En qué meses se concentra el flujo del año elegido?",
         "Línea mensual frente al promedio 2015–2019 (línea punteada).",
         "Total o desglose por vía."],
        ["3", "¿Se repite cada año el patrón de meses altos y bajos?",
         "Mapa de calor año × mes; índice 100 = mes promedio del año; escala divergente.",
         "Marca el año elegido; detalle al pasar el cursor."],
        ["4", "¿De qué países llegan más viajeros?",
         "Barras horizontales, 10 principales países de residencia del año.",
         "Clic en un país lo envía a la gráfica 5."],
        ["5", "¿Cómo ha evolucionado el país elegido?",
         "Líneas por vía, 2009–2026; 2026 sombreado como parcial.",
         "Selector de país (o clic en la gráfica 4)."],
        ["6", "¿Por qué puntos de ingreso entran?",
         "Barras horizontales de los 10 puestos/aeropuertos/puertos; color = vía.",
         "Sigue al año elegido."],
        ["7", "¿Cambia la mezcla de regiones de origen?",
         "Columnas 100 % apiladas por región de residencia.",
         "Clic en la leyenda oculta o muestra regiones."],
        ["8", "¿Cada vía ya recuperó su nivel prepandemia?",
         "Índice anual (2015–2019 = 100) por vía y total; línea de referencia en 100.",
         "Marca el año elegido."],
    ], [0.6, 4.6, 6.6, 5.2]),
    Spacer(1, 6),
    p("Además, tres tarjetas resumen muestran los viajeros del año elegido, la variación "
      "frente al promedio 2015–2019 en los mismos meses y el principal país de origen."),

    Paragraph("3. Datos", E["h1"]),
    *lista([
        "<b>Fuente:</b> Base_Migracion_2009-2026jun (Laboratorio 1), 161,036 registros "
        "mensuales por vía, frontera, país, región y tipo de viajero.",
        "<b>Preparación</b> (<i>preparar_datos.py</i>): se agregan tres CSV livianos "
        "(año–mes–vía–tipo; año–país–región–vía–tipo; año–mes–vía–frontera–tipo). "
        "Las regiones MCEO se agrupan en 5 (Centroamérica, Norteamérica, Europa, Sudamérica, "
        "Resto del mundo) para usar colores distinguibles.",
        "<b>Modelos</b> (<i>exportar_lab1.R</i>): ejecuta el Rmd del Laboratorio 1 sin "
        "modificarlo y exporta sus métricas (MAE, RMSE, AIC, BIC) y las predicciones de cada "
        "modelo sobre el último 30 % de cada serie. El tablero solo lee esos CSV; las métricas "
        "coinciden con las reportadas en el Laboratorio 1.",
        "2026 contiene solo enero a junio; se marca con asterisco o sombreado y toda "
        "comparación con 2015–2019 usa los mismos meses.",
    ]),

    Paragraph("4. Decisiones de diseño", E["h1"]),
    Paragraph("4.1 Color: paleta Okabe-Ito", E["h2"]),
    p("Se usa la paleta Okabe-Ito, diseñada para ser distinguible con los tipos comunes de "
      "daltonismo. Cada color tiene un significado fijo: la misma vía conserva su color en "
      "todas las gráficas donde aparece."),
    muestras([
        ("#0072B2", "Vía terrestre"),
        ("#E69F00", "Vía aérea"),
        ("#009E73", "Vía marítima"),
        ("#56B4E9", "Centroamérica (gráfica 7); meses bajo el promedio (mapa de calor)"),
        ("#D55E00", "Norteamérica (gráfica 7); país resaltado (gráfica 4); meses sobre el "
                    "promedio y escala de error (mapas de calor)"),
        ("#CC79A7", "Europa (gráfica 7)"),
        ("#F0E442", "Sudamérica (gráfica 7)"),
        ("#999999", "Resto del mundo (gráfica 7)"),
        ("#1F2937", "Total y textos; referencias en gris #6B7280"),
    ]),
    Spacer(1, 4),
    p("En la pestaña de modelos el color identifica al modelo (Prophet azul, ARIMA bermellón, "
      "Holt-Winters verde, ETS púrpura, Seasonal Naive naranja) y el dato real va en negro. "
      "Los mapas de calor usan escalas con tope fijo para que los valores extremos (2020, vía "
      "marítima) no opaquen al resto; el valor exacto siempre aparece en el texto de la celda "
      "o al pasar el cursor."),

    Paragraph("4.2 Interacción y selector de gráficas", E["h2"]),
    *lista([
        "<b>Selector «Gráficas a mostrar»:</b> el usuario elige cuáles de las 8 gráficas ver; "
        "se muestran en una cuadrícula de dos columnas y siempre en el mismo orden.",
        "<b>Enlaces entre gráficas:</b> clic en un año (gráfica 1) actualiza las gráficas 2, 3, "
        "4, 6, 7 y 8 y las tarjetas; clic en un país (gráfica 4) actualiza la gráfica 5.",
        "<b>Filtros globales:</b> tipo de viajero y año. Todas las gráficas (Plotly) permiten "
        "zoom, detalle al pasar el cursor y descarga como imagen.",
        "<b>Modelos:</b> selector de serie (general, 3 países, 3 vías) y de modelos a comparar.",
    ]),

    Paragraph("4.3 Datos faltantes y casos vacíos", E["h2"]),
    p("Cuando un filtro deja una gráfica sin datos (por ejemplo, cruceristas en 2025) se "
      "muestra un mensaje que explica el motivo y sugiere otro filtro, en lugar de una gráfica "
      "vacía. Si no se elige ninguna gráfica o ningún modelo, se pide elegir al menos uno. Los "
      "meses sin datos de 2026 no se dibujan (no se rellenan con cero) y, si faltan los "
      "archivos de datos, la aplicación indica qué script ejecutar."),

    Paragraph("4.4 Texto para directivos", E["h2"]),
    *lista([
        "Títulos en forma de pregunta; subtítulo con cómo leer la gráfica.",
        "Línea de <b>Lectura</b> calculada con los datos del filtro actual.",
        "Las diferencias se describen sin atribuir causas; el promedio 2015–2019 se presenta "
        "como referencia, no como pronóstico.",
        "Glosario desplegable («Términos y cómo usar el tablero»).",
    ]),

    PageBreak(),
    Paragraph("5. Recorrido por el tablero", E["h1"]),
    figura("0_inicio.png", "Figura 1. Encabezado, filtros globales, tarjetas resumen y "
           "selector de gráficas.", arriba=0.13, abajo=0.77),
    figura("1_anual_mensual.png", "Figura 2. Gráficas 1 y 2. Clic en una columna del gráfico "
           "anual cambia el año de todo el tablero.", abajo=0.88),
    figura("2_calor_paises.png", "Figura 3. Gráficas 3 y 4. El mapa de calor muestra diciembre "
           "como el mes más alto de casi todos los años y 2020 como anomalía."),
    figura("3_pais_fronteras.png", "Figura 4. Gráficas 5 y 6. 2026 se sombrea como año parcial "
           "para no confundir la caída con una disminución real.", abajo=0.95),
    figura("4_regiones_recuperacion.png", "Figura 5. Gráficas 7 y 8.", abajo=0.92),
    figura("8_sin_datos.png", "Figura 6. Mensaje cuando el filtro no tiene datos "
           "(cruceristas en 2025).", abajo=0.81),

    Paragraph("Hallazgos observados (año 2025)", E["h2"]),
    *lista([
        "Ingresaron 3,597,235 viajeros, 7.3 % menos que el promedio 2015–2019 (índice 93).",
        "El Salvador aporta el 48 % de los viajeros; Centroamérica, el 66 %, y Norteamérica, "
        "el 24 %.",
        "El aeropuerto La Aurora concentra el 33 % de los ingresos.",
        "Diciembre es el mes más alto y septiembre el más bajo en el periodo 2015–2019.",
    ]),

    Paragraph("6. Comparación de modelos (Laboratorio 1)", E["h1"]),
    p("La pestaña reutiliza los resultados del Laboratorio 1: cada modelo se ajustó con el "
      "primer 70 % de la serie y pronosticó el 30 % restante. Se muestran tres vistas: (A) "
      "pronóstico frente a lo real en el periodo de prueba, (B) error típico mensual (RMSE) "
      "por modelo con su porcentaje frente al flujo mensual promedio y (C) un mapa de calor "
      "del error relativo de cada modelo en las 7 series."),
    figura("5_modelos_inicio.png", "Figura 7. Encabezado de la pestaña: serie, modelos y "
           "tarjetas con el modelo de menor error.", arriba=0.12, abajo=0.39),
    figura("6_modelos_ab.png", "Figura 8. Vistas A y B para la serie General.", abajo=0.86),
    figura("7_modelos_c.png", "Figura 9. Vista C: error relativo por modelo y serie.", abajo=0.84),
    tabla([
        ["Serie", "Modelo con menor error", "MAE", "RMSE"],
        ["General", "Prophet", "97,590", "107,977"],
        ["El Salvador", "Prophet", "53,253", "56,540"],
        ["Guatemala", "Seasonal Naive", "56,260", "69,513"],
        ["Estados Unidos", "Holt-Winters", "23,098", "25,169"],
        ["Vía aérea", "Holt-Winters", "26,343", "31,317"],
        ["Vía terrestre", "Prophet", "54,309", "71,306"],
        ["Vía marítima", "ARIMA (empata con Seasonal Naive)", "858", "1,732"],
    ], [4, 6.5, 3, 3.5]),
    Spacer(1, 6),
    p("<b>Lectura para directivos:</b> ningún modelo gana en todas las series. Prophet tiene "
      "el menor error en 3 de 7 y Holt-Winters en 2, así que el modelo debe elegirse según la "
      "serie a pronosticar. El periodo de prueba (abril 2021 a junio 2026 en la mayoría de "
      "series) coincide con la recuperación tras la pandemia, lo que eleva todos los errores; "
      "en la vía marítima el flujo reciente es tan bajo que los errores relativos superan el "
      "200 %."),

    Paragraph("7. Limitaciones", E["h1"]),
    *lista([
        "Los datos son registros migratorios; «país» es el país de residencia, no la "
        "nacionalidad.",
        "Los modelos no se reentrenan: el tablero no produce pronósticos posteriores a junio "
        "2026. Para ello habría que reajustarlos con la serie completa.",
        "La serie «Guatemala» del Laboratorio 1 termina en 2022, por lo que su periodo de "
        "prueba (octubre 2018 a diciembre 2022) es distinto al de las demás.",
        "El tablero describe patrones; no atribuye causas a los cambios observados.",
    ]),

    Paragraph("8. Ejecución y reproducibilidad", E["h1"]),
    *lista([
        "<b>Tablero:</b> <i>pip install -r requirements.txt</i> y <i>streamlit run app.py</i> "
        "desde la carpeta <i>tablero/</i>.",
        "<b>Datos:</b> <i>python preparar_datos.py Base_Migracion_2009-2026jun.xlsx</i>.",
        "<b>Modelos:</b> <i>Rscript exportar_lab1.R Laboratorio_1_completo.Rmd "
        "Base_Migracion_2009-2026jun.xlsx</i>.",
        "<b>Prueba:</b> <i>python test_app.py</i> ejecuta el tablero con todas las "
        "combinaciones de tipo de viajero y año y verifica que no haya errores.",
    ]),
]

SimpleDocTemplate(str(SALIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                  topMargin=1.8 * cm, bottomMargin=2 * cm,
                  title="Documento de diseño del tablero – Laboratorio 10",
                  author="Laboratorio 10 CC3066").build(h, onFirstPage=pie_pagina,
                                                         onLaterPages=pie_pagina)
print(f"Generado {SALIDA}")
