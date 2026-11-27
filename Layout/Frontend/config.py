"""Einstellungen und Stammdaten der App – alle Werte, die sich je nach Sensoren, Rechner oder DB-Schema ändern.

Logik in schnittstelle.py, Layout in frontend.py – beide ohne feste Werte.
Umgebungsvariablen haben Vorrang vor den Werten hier: Server und Entwicklungsrechner
dadurch mit demselben Code, Passwörter nie im Repository.
"""
import os
from dataclasses import dataclass
from pathlib import Path

# ── Sensoren und Messgrößen ─────────────────────────────────────────────────────
# Neue Sensoren hier eintragen, dazu ihre Datenherkunft weiter unten (EXPORTE bzw. DB_SENSOR_IDS).


@dataclass(frozen=True)
class Messgroesse:
    name: str
    zeichen: str     # Formelzeichen (LaTeX) wie in der Projektvorstellung
    einheit: str
    stellen: int     # Nachkommastellen laut Anzeigevorgabe


@dataclass(frozen=True)
class Sensor:
    kennung: str
    standort: str
    name: str
    messgroessen: tuple
    farbe: str       # gleiche Farbe in Werteliste und Diagramm


# Reihenfolge hier = Reihenfolge der Zeilen auf der Seite
MESSGROESSEN = {
    "v":         Messgroesse("Wettergeschwindigkeit", r"$v$", "m/s", 2),
    "Q":         Messgroesse("Wettervolumenstrom", r"$Q$", "m³/s", 2),
    "richtung":  Messgroesse("Strömungsrichtung", r"$\alpha$", "°", 0),
    "Tt":        Messgroesse("Trockentemperatur", r"$T_\mathrm{t}$", "°C", 1),
    "Tf":        Messgroesse("Feuchttemperatur", r"$T_\mathrm{f}$", "°C", 1),
    "phi":       Messgroesse("Relative Luftfeuchtigkeit", r"$\varphi$", "%", 1),
    "p":         Messgroesse("Luftdruck", r"$p$", "hPa", 2),
    "dp_links":  Messgroesse("Differenzdruck links", r"$\Delta p_\mathrm{l}$", "Pa", 0),
    "dp_rechts": Messgroesse("Differenzdruck rechts", r"$\Delta p_\mathrm{r}$", "Pa", 0),
    "radon":     Messgroesse("Radonkonzentration", r"$C_\mathrm{Rn}$", "Bq/m³", 0),
}

KLIMA = ("v", "Q", "Tt", "Tf", "phi", "p")

# Reihenfolge hier = Reihenfolge der Standorte; Sensoren ohne Daten bleiben unsichtbar
SENSOREN = [
    Sensor("zephyr",      "BHMZ",             "Maestro Zephyr AQS",     KLIMA,                 "#1f77b4"),
    Sensor("sp_ultra",    "BHMZ",             "Accutron SP Ultra",      ("v", "richtung"),     "#d62728"),
    Sensor("vaisala",     "BHMZ",             "Vaisala Indigo520",      ("Tt", "Tf", "phi"),   "#2ca02c"),
    Sensor("accutron_qw", "Querschlag West",  "Accutron Pro",           KLIMA,                 "#1f77b4"),
    Sensor("accutron_rs", "Richtstrecke Süd", "Accutron Pro",           KLIMA,                 "#1f77b4"),
    Sensor("thies",       "Richtstrecke Süd", "Thies DLU Psychrogeber", ("Tt", "Tf", "phi"),   "#2ca02c"),
    Sensor("radontec",    "Richtstrecke Süd", "RadonTec AlphaTracer",   ("radon",),            "#9467bd"),
    Sensor("sensirion",   "HGL",              "Sensirion SDP810",       ("dp_links", "dp_rechts", "Q"), "#ff7f0e"),
]


# ── Datenquelle ─────────────────────────────────────────────────────────────────

DATENQUELLE = os.getenv("DATENQUELLE", "csv")   # "csv" oder "db"
CSV_ORDNER = Path(os.getenv("CSV_ORDNER", Path(__file__).parent / "testdaten"))
DB_URL = os.getenv("DB_URL", "")                # z. B. postgresql+psycopg://nutzer:passwort@server/bewetterung


# ── CSV-Exporte ─────────────────────────────────────────────────────────────────
# Ablage wie in der Nextcloud, ein Ordner je Sensor:
#   testdaten/BHMZ_Maestro_Zephyr/zephyr_data_2026-01.csv
#   testdaten/BHMZ_Accutron_SP_Ultra/accutron_2026-01.csv
#   testdaten/BHMZ_Vaisala/vaisala_2026_01.csv
# Je Gerät: Ordner, Zeitspalte, CSV-Spalte -> Messgröße (Schlüssel aus MESSGROESSEN)

EXPORTE = {
    "zephyr": dict(
        ordner="BHMZ_Maestro_Zephyr",
        zeit="SystemTime",  # DeviceTime unbrauchbar, Geräteuhr steht auf 1999
        spalten={"Velocity in m/s": "v", "Volumetric in m³/s": "Q", "Temperature in °C": "Tt",
                 "WetBulb in °C": "Tf", "Humidity in %": "phi", "Pressure in kPa": "p"},
        faktoren={"p": 10},  # kPa -> hPa
    ),
    "sp_ultra": dict(
        ordner="BHMZ_Accutron_SP_Ultra",
        zeit="Timestamp",
        spalten={"Velocity in m/s": "v", "Airflow Angle in °": "richtung"},
    ),
    "vaisala": dict(
        ordner="BHMZ_Vaisala",
        zeit="Systemtime",  # Devicetime läuft in UTC
        spalten={"Temperature C": "Tt", "Wet Bulb C": "Tf", "Relative Humidity Pct": "phi"},
    ),
}


# ── Datenbankschema ─────────────────────────────────────────────────────────────
# „Breite“ Messtabelle: eine Zeile je Sensor und Zeitpunkt, eine Spalte je Größe.
# Schemaänderung = nur hier anpassen. Fehlende Spalten (z. B. Radon) werden übersprungen.

DB_TABELLE = "messdaten"
DB_SENSOR_SPALTE = "sensor_id"
DB_ZEIT_SPALTE = "zeitstempel"

DB_SPALTEN = {                  # Messgröße (MESSGROESSEN) -> Spalte in der Tabelle
    "v": "wettergeschw",
    "Q": "wettervolumenstrom",
    "richtung": "stroemungsrichtung",
    "Tt": "trockentemperatur",
    "Tf": "feuchttemperatur",
    "phi": "luftfeuchte",
    "p": "luftdruck",
    "dp_links": "differenzdruck_li",
    "dp_rechts": "differenzdruck_re",
    "radon": "radon",
}

DB_SENSOR_IDS = {               # Kennung (SENSOREN) -> sensor_id in der Datenbank
    "zephyr": 1, "sp_ultra": 2, "vaisala": 3, "accutron_qw": 4,
    "accutron_rs": 5, "thies": 6, "radontec": 7, "sensirion": 8,
}


# ── Anzeige ─────────────────────────────────────────────────────────────────────

ZEITFORMAT = "%d.%m.%y %H:%M:%S"    # Anzeigevorgabe dd.mm.yy hh:mm:ss

# Zeitraum -> (Dauer, Mittelungsraster, Beschriftung), jeweils rund 1000 Punkte je Linie:
# genug Details, schnell geladen. Raster None = Rohdaten im 5-s-Takt.
ZEITRAEUME = {
    "1 h":     ("1h", None, "Einzelwerte im 5-s-Takt"),
    "24 h":    ("1D", "1min", "1-Minuten-Mittelwerte"),
    "7 Tage":  ("7D", "10min", "10-Minuten-Mittelwerte"),
    "30 Tage": ("30D", "30min", "30-Minuten-Mittelwerte"),
}
STANDARD_ZEITRAUM = "24 h"

AKTUALISIERUNG = "10s"      # Neuladen der aktuellen Werte; Sensoren messen alle 5 s
SCHRIFTGROESSE = 18         # px Grundschrift der Seite, Streamlit-Standard 16
SCHRIFT_DIAGRAMM = 15       # px für Achsen und Tooltip der Diagramme
KACHELN_JE_REIHE = 2        # Messgrößen nebeneinander; 2 = große, gut lesbare Kacheln
DIAGRAMMHOEHE = 280         # px je Kachel
ABSTAND_STANDORTE = "large"   # vor jedem weiteren Standort (st.space: small, medium, large …)
