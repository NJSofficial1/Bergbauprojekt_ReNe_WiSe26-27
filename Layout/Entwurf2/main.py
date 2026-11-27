import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px # plotly zum Zeichnen der Diagramme (Express-Variante statt Graph Objects, reicht für unsere Zwecke aus)


st.set_page_config(
    page_title="Entwurf 2",
)

st.title("Entwurf 2 mit Streamlit und plotly.express", text_alignment="center")

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

# Trennen von Daten und UI: add_graph_data nur für Datenbereitstellung
def add_graph_data() -> None:
    df = pd.DataFrame(
        np.random.randn(20, len(sensors)) * 5 + 15,
        columns=sensors,
    )
    st.session_state.diagrams.append(df)

# Anlegen eines Startdiagramms, falls wir noch keine ausgewählt haben -> Init. Session State
if "diagrams" not in st.session_state:
    st.session_state.diagrams = []



for i, df in enumerate(st.session_state.diagrams):
    st.divider()

    selected_metric_type = st.selectbox(
        "Messwert",
        options=list(data_t.keys()),
        key=f"metric_select_{i}"    # eindeutiger key pro Diagramm, damit der Session State die Diagramme 
                                    # eindeutig auseinanderhalten kann
    )

    unit = data_t[selected_metric_type]
    st.subheader(f"{selected_metric_type} ({unit})")

    # UI-Teil: Liniendiagramme
    # todo Frage: Brauchen wir weitere Typen?
    figure = px.line(
        df,
        labels={"index": "Zeitpunkt", "value": f"Wert ({unit})", "variable": "Sensor"},
    )
    st.plotly_chart(figure, width="stretch")

# Hinzufügen weiterer Diagramme per Button
st.button("Messwert hinzufügen", on_click=add_graph_data)