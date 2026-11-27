# Übersicht der Bewetterungsdaten im FLB – nur Layout, Daten über schnittstelle.py, Einstellungen in config.py
# Start: streamlit run frontend.py
import pandas as pd
import plotly.express as px
import streamlit as st

import config
from schnittstelle import oeffne_quelle
from config import MESSGROESSEN, SENSOREN

# eine Quelle für alle Nutzer und Seitenaufrufe – sonst je Aufruf neue DB-Verbindung
quelle = st.cache_resource(oeffne_quelle)()


def als_text(schluessel, wert):
    groesse = MESSGROESSEN[schluessel]
    if wert is None or pd.isna(wert):
        return "–"
    return f"{wert:.{groesse.stellen}f}".replace(".", ",") + " " + groesse.einheit


@st.fragment(run_every=config.AKTUALISIERUNG)  # nur die Werte neu laden, Diagramme bleiben stehen
def werteliste(schluessel, sensoren):
    groesse = MESSGROESSEN[schluessel]
    st.markdown(f"**{groesse.name}** {groesse.zeichen}")
    for sensor in sensoren:
        stand = quelle.aktuelle_werte(sensor)
        wert = stand[1].get(schluessel) if stand else None
        st.markdown(f'<span style="color:{sensor.farbe}">●</span> '
                    f"**{als_text(schluessel, wert)}** &nbsp;{sensor.name}",
                    unsafe_allow_html=True)


@st.fragment(run_every=config.AKTUALISIERUNG)  # Uhrzeit wandert mit den Werten mit
def kopf_momentanwerte(sensoren):
    zeiten = [stand[0] for s in sensoren if (stand := quelle.aktuelle_werte(s))]
    st.markdown("#### Momentanwerte")
    st.caption(f"letzte Messung {max(zeiten).strftime(config.ZEITFORMAT)}" if zeiten else "keine Messung")


def diagramm(schluessel, verlaeufe):
    groesse = MESSGROESSEN[schluessel]
    linien = [pd.DataFrame({"Zeit": df.index, "Wert": df[schluessel].values, "Sensor": s.name})
              for s, df in verlaeufe.items() if schluessel in df]
    if not linien:
        st.caption("Keine Daten im gewählten Zeitraum")
        return

    fig = px.line(pd.concat(linien), x="Zeit", y="Wert", color="Sensor",
                  color_discrete_map={s.name: s.farbe for s in verlaeufe})
    fig.update_traces(hovertemplate=f"%{{y:.{groesse.stellen}f}} {groesse.einheit}")
    fig.update_layout(height=config.DIAGRAMMHOEHE, margin=dict(l=0, r=0, t=10, b=0),
                      hoverlabel_font_size=config.SCHRIFT_DIAGRAMM,
                      showlegend=False,  # Zuordnung über die Farbpunkte links
                      hovermode="x unified", separators=",.",
                      xaxis_title=None, yaxis_title=groesse.einheit)
    # Schriftgröße je Achse: das Streamlit-Design überschreibt die allgemeine font_size
    fig.update_xaxes(tickformat="%d.%m.%y\n%H:%M", hoverformat=config.ZEITFORMAT,
                     tickfont_size=config.SCHRIFT_DIAGRAMM)
    fig.update_yaxes(tickfont_size=config.SCHRIFT_DIAGRAMM, title_font_size=config.SCHRIFT_DIAGRAMM)
    st.plotly_chart(fig, width="stretch")


st.set_page_config(page_title="Bewetterung FLB", layout="wide")
# Grundschrift: alle Streamlit-Größen in rem, daher skaliert die ganze Seite mit
st.html(f"<style>html {{ font-size: {config.SCHRIFTGROESSE}px; }}</style>")

links, rechts = st.columns([3, 2], vertical_alignment="bottom")
links.title("Bewetterungsdaten FLB")
zeitraum = rechts.segmented_control("Zeitraum", list(config.ZEITRAEUME),
                                    default=config.STANDARD_ZEITRAUM) or config.STANDARD_ZEITRAUM

dauer, raster, beschreibung = config.ZEITRAEUME[zeitraum]
bis = quelle.jetzt()
von = bis - pd.Timedelta(dauer)

# Standorte nur mit Sensoren, die Daten haben – neue erscheinen ohne Codeänderung
standorte = {}
for sensor in SENSOREN:
    if quelle.hat_daten(sensor):
        standorte.setdefault(sensor.standort, []).append(sensor)

if not standorte:
    st.info("Keine Messdaten gefunden – Datenquelle bzw. Einstellungen in config.py prüfen.")

for nummer, (standort, sensoren) in enumerate(standorte.items()):
    if nummer:  # Abstand nur zwischen Standorten, nicht unter dem Seitentitel
        st.space(config.ABSTAND_STANDORTE)
    st.header(standort, divider="gray")

    # Spaltenköpfe: links Momentanwert, rechts Historie – gleiche Aufteilung wie die Zeilen darunter
    kopf_links, kopf_rechts = st.columns([1, 3], gap="large")
    with kopf_links:
        kopf_momentanwerte(sensoren)
    kopf_rechts.markdown(f"#### Verlauf – letzte {zeitraum}")
    kopf_rechts.caption(f"{beschreibung} bis {bis.strftime(config.ZEITFORMAT)}")

    with st.spinner("Lade Messdaten …"):
        verlaeufe = {s: quelle.verlauf(s, von, bis, raster) for s in sensoren}  # einmal je Sensor

    for schluessel in MESSGROESSEN:
        messende = [s for s in sensoren if schluessel in s.messgroessen]
        if messende:
            st.space(config.ABSTAND_ZEILEN)
            wert_spalte, diagramm_spalte = st.columns([1, 3], gap="large", vertical_alignment="center")
            with wert_spalte:
                werteliste(schluessel, messende)
            with diagramm_spalte:
                diagramm(schluessel, {s: verlaeufe[s] for s in messende})
