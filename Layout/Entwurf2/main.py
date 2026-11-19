import streamlit as st
import numpy as np
import pandas as pd


st.set_page_config(
    page_title="Entwurf 2",
)

# Verfügbare Sensoren
sensors: list[str] = [
    "Acutron",
    "Zephyr",
    "Vaisala",
]

# Messwerttypen und Einheiten
data_t = {
    "Wettergeschwindigkeit": "m/s",
    "Trockentemperatur"    : "°C",
    "Feuchttemperatur"     : "°C",
    "Luftfeuchtigkeit"     : "%",
    "Luftdruck"            : "hPa",
    "Radonkonzentration"   : "mSv",
}

# Frage: Wie können Diagramme hinzugefügt werden?
diagrams: list[Diagram] = []


class Diagram:
    chart_header: st.DeltaGenerator
    chart_frame: pd.DataFrame    
    data_option: str


def addGraph() -> void:
    dia = Diagram()
    
    # zufällige Testdaten
    data: list[float] = np.random.randn(20, len(sensors)) * 5 + 15

    data_option: list[str] = list(data_t.keys())[0] # standart "Wettergeschwindigkeit"
    dia.chart_header = st.text(data_option)
    dia.chart_frame = pd.DataFrame(data, columns=sensors)
    st.line_chart(dia.chart_frame)

    # Messwert dropdown
    dia.data_option = st.selectbox(
        "Messwert",
         data_t,
         key=len(diagrams)
     )
    dia.chart_header.write(f"{dia.data_option} ({data_t.get(dia.data_option)})")

    diagrams.append(dia)


addGraph()
st.button("Messwert hinzufügen", on_click=addGraph)