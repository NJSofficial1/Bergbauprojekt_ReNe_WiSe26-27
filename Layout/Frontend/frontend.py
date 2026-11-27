# Übersicht der Bewetterungsdaten im FLB – nur Layout, Daten über schnittstelle.py, Einstellungen in config.py
# Start: streamlit run frontend.py
import pandas as pd
import plotly.express as px
import streamlit as st

import config
from config import MESSGROESSEN, SENSOREN
from schnittstelle import oeffne_quelle

# eine Quelle für alle Nutzer und Seitenaufrufe – sonst je Aufruf neue DB-Verbindung
quelle = st.cache_resource(oeffne_quelle)()


def als_text(schluessel, wert):
    groesse = MESSGROESSEN[schluessel]
    if wert is None or pd.isna(wert):
        return "–"
    return f"{wert:.{groesse.stellen}f}".replace(".", ",") + " " + groesse.einheit


@st.fragment(run_every=config.AKTUALISIERUNG)  # Uhrzeit wandert mit den Werten mit
def standort_hinweis(sensoren, zeitraum, beschreibung):
    zeiten = [stand[0] for s in sensoren if (stand := quelle.aktuelle_werte(s))]
    letzte = max(zeiten).strftime(config.ZEITFORMAT) if zeiten else "–"
    st.caption(f"**Zahlen = Momentanwerte** (letzte Messung {letzte}) · "
               f"**Diagramme = Verlauf** der letzten {zeitraum} ({beschreibung})")


@st.fragment(run_every=config.AKTUALISIERUNG)  # nur die Werte neu laden, Diagramme bleiben stehen
def momentanwerte(schluessel, sensoren, zeilen_gesamt):
    groesse = MESSGROESSEN[schluessel]
    zeilen = [f"**{groesse.name}** {groesse.zeichen}"]
    for sensor in sensoren:
        stand = quelle.aktuelle_werte(sensor)
        wert = stand[1].get(schluessel) if stand else None
        zeilen.append(f'<span style="color:{sensor.farbe}">●</span> '
                      f"**{als_text(schluessel, wert)}** &nbsp;{sensor.name}")
    # Leerzeilen auffüllen: Kacheln mit einem Sensor gleich hoch wie solche mit mehreren
    zeilen += ["&nbsp;"] * (zeilen_gesamt - len(sensoren))
    st.markdown("  \n".join(zeilen), unsafe_allow_html=True)


def verlauf(schluessel, verlaeufe):
    groesse = MESSGROESSEN[schluessel]
    linien = [pd.DataFrame({"Zeit": df.index, "Wert": df[schluessel].values, "Sensor": s.name})
              for s, df in verlaeufe.items() if schluessel in df]
    if not linien:
        st.caption("Keine Daten im gewählten Zeitraum")
        return

    fig = px.line(pd.concat(linien), x="Zeit", y="Wert", color="Sensor",
                  color_discrete_map={s.name: s.farbe for s in verlaeufe})
    fig.update_traces(hovertemplate=f"%{{y:.{groesse.stellen}f}} {groesse.einheit}")
    fig.update_layout(height=config.DIAGRAMMHOEHE, margin=dict(l=0, r=0, t=5, b=0),
                      hoverlabel_font_size=config.SCHRIFT_DIAGRAMM,
                      showlegend=False,  # Zuordnung über die Farbpunkte bei den Werten
                      hovermode="x unified", separators=",.",
                      xaxis_title=None, yaxis_title=groesse.einheit)
    # Schriftgröße je Achse: das Streamlit-Design überschreibt die allgemeine font_size
    fig.update_xaxes(tickformat="%d.%m.\n%H:%M", hoverformat=config.ZEITFORMAT,
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
    standort_hinweis(sensoren, zeitraum, beschreibung)

    with st.spinner("Lade Messdaten …"):
        verlaeufe = {s: quelle.verlauf(s, von, bis, raster) for s in sensoren}  # einmal je Sensor

    # Kacheln im Raster statt einer Zeile je Messgröße – ganzer Standort ohne langes Scrollen
    messende = {g: [s for s in sensoren if g in s.messgroessen] for g in MESSGROESSEN}
    messende = {g: liste for g, liste in messende.items() if liste}
    zeilen_gesamt = max(len(liste) for liste in messende.values())

    n = config.KACHELN_JE_REIHE
    kacheln = list(messende.items())
    for start in range(0, len(kacheln), n):
        for spalte, (schluessel, liste) in zip(st.columns(n, gap="medium"), kacheln[start:start + n]):
            with spalte.container(border=True):
                momentanwerte(schluessel, liste, zeilen_gesamt)
                verlauf(schluessel, {s: verlaeufe[s] for s in liste})
