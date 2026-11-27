# Bewetterungsdaten FLB

Web-App zur Anzeige der Wettermessungen im Forschungs- und Lehrbergwerk (FLB) der TU Bergakademie Freiberg.
Aktuelle Werte und Verlauf je Standort auf einer Seite – Übersicht ohne langes Herumklicken.

Umsetzung mit Streamlit und plotly.express. Daten bis zur Fertigstellung der Datenbank aus den CSV-Exporten der Sensoren.

![Ansicht der App mit Testdaten Februar 2026](docs/ansicht.png)

*Stand: 27.11.2026*


## Schnellstart

Voraussetzung: Python 3.10 oder neuer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run frontend.py
```

Danach öffnet sich die App im Browser unter http://localhost:8501.
Vorher die Messdaten in den Ordner `testdaten/` legen (siehe [Messdaten ablegen](#messdaten-ablegen)).


## Bedienung

- **Zeitraum** oben rechts: 1 h, 24 h, 7 Tage oder 30 Tage – gilt für alle Diagramme gleichzeitig.
- **Je Standort** ein Abschnitt mit einer Kachel je Messgröße (2 nebeneinander, alle gleich groß). In jeder Kachel oben die **Momentanwerte** (Zahlen, letzte Messung), darunter der **Verlauf** im gewählten Zeitraum (Diagramm). Die Zeile unter dem Standortnamen nennt Uhrzeit der letzten Messung und Art der Mittelung.
- **Farbpunkt** vor dem Wert = Farbe der Linie im Diagramm. Deshalb keine eigene Legende.
- Kacheln je Reihe, Schriftgrößen und Diagrammhöhe im Abschnitt „Anzeige“ in `config.py` – z. B. `KACHELN_JE_REIHE = 3` für einen kompakteren Überblick auf großen Bildschirmen.
- **Aktuelle Werte** laden alle 10 s neu, die Diagramme bleiben dabei stehen (kein Flackern).
- **Standorte ohne Daten** sind ausgeblendet und erscheinen von selbst, sobald Daten vorliegen.
- Bei 24 h, 7 Tagen und 30 Tagen zeigen die Diagramme Mittelwerte (1 min, 10 min, 30 min), bei 1 h die Rohdaten im 5-s-Takt.

Hinweis zu den CSV-Daten: „Jetzt“ ist der jüngste Zeitstempel in den Dateien, nicht die Uhrzeit – sonst wäre bei alten Exporten jeder Zeitraum leer.


## Aufbau

| Datei              | Zweck                                                                                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `frontend.py`      | Layout der Seite. Kennt keine Dateien, Tabellen oder Spaltennamen.                                                                                                             |
| `schnittstelle.py` | Datenanbindung: Vertrag (`Datenquelle`), CSV-Quelle, Datenbank-Quelle, Auswahl der Quelle. Nur Logik.                                                                          |
| `config.py`        | Einstellungen und Stammdaten: Sensoren und Messgrößen, Datenquelle, Ordner, CSV-Spalten je Gerät, DB-Schema, Zeiträume, Aktualisierung, Schriftgrößen, Abstände, Diagrammhöhe. |
| `testdaten/`       | CSV-Exporte der Sensoren, nicht im Repository. Anderer Ort: `CSV_ORDNER` in `config.py`.                                                                                       |

Grundidee: Das Frontend ruft nur vier Methoden auf – `hat_daten`, `jetzt`, `aktuelle_werte`, `verlauf`.
Jede Datenquelle liefert die Messgrößen unter denselben Schlüsseln (`v`, `Tt`, `phi` …) und bereits in Anzeigeeinheit.
Dadurch bei Wechsel der Quelle oder Änderung des DB-Schemas keine Änderung am Frontend.


## Messdaten ablegen

Gleiche Struktur wie in der Nextcloud unter *Beispielmesswerte*, ein Ordner je Sensor:

```
testdaten/
├── BHMZ_Accutron_SP_Ultra/
│   ├── accutron_2026-01.csv
│   └── accutron_2026-02.csv
├── BHMZ_Maestro_Zephyr/
│   ├── zephyr_data_2026-01.csv
│   └── ...
└── BHMZ_Vaisala/
    ├── vaisala_2026_01.csv
    └── ...
```

- Neue Monatsdatei einfach in den passenden Ordner kopieren, kein Neustart nötig.
- Monat aus dem Dateinamen (`2026-01` oder `2026_01`), der Rest des Namens egal.
- Doppelte Dateien (z. B. `…_1.csv` vom Download) stören nicht, doppelte Zeitstempel werden nur einmal übernommen.
- Erster Aufruf eines Monats dauert ein paar Sekunden (Einlesen), danach aus dem Zwischenspeicher.


## Datenquelle wechseln

Auswahl in `config.py` (`DATENQUELLE`, `CSV_ORDNER`, `DB_URL`) oder über gleichnamige Umgebungsvariablen – diese haben Vorrang.
Für den Server Umgebungsvariablen nehmen, damit das DB-Passwort nicht im Repository landet:

```bash
# Standard: CSV-Dateien aus testdaten/
streamlit run frontend.py

# Datenbank
DATENQUELLE=db DB_URL="postgresql+psycopg://nutzer:passwort@server/bewetterung" streamlit run frontend.py
```

Unter Windows (PowerShell):

```powershell
$env:DATENQUELLE = "db"
$env:DB_URL = "postgresql+psycopg://nutzer:passwort@server/bewetterung"
streamlit run frontend.py
```

Für die Datenbank zusätzlich den passenden Treiber installieren, für PostgreSQL z. B. `pip install "psycopg[binary]"`.
Getestet mit SQLite, grundsätzlich jede Datenbank, die SQLAlchemy unterstützt.


## Datenbank anbinden

Erwartet wird eine „breite“ Messtabelle: eine Zeile je Sensor und Zeitpunkt, eine Spalte je Messgröße.

```sql
CREATE TABLE messdaten (
    sensor_id           INTEGER   NOT NULL,
    zeitstempel         TIMESTAMP NOT NULL,
    luftfeuchte         DECIMAL(4,1),   -- %
    trockentemperatur   DECIMAL(4,1),   -- °C
    luftdruck           DECIMAL(6,2),   -- hPa
    feuchttemperatur    DECIMAL(4,1),   -- °C
    wettergeschw        DECIMAL(5,2),   -- m/s, negativ = Gegenrichtung
    wettervolumenstrom  DECIMAL(6,2),   -- m³/s
    stroemungsrichtung  SMALLINT,       -- °
    differenzdruck_li   SMALLINT,       -- Pa
    differenzdruck_re   SMALLINT,       -- Pa
    PRIMARY KEY (sensor_id, zeitstempel)
);
```

Abweichendes Schema? Nur den Abschnitt **Datenbankschema** in `config.py` anpassen:

- `DB_TABELLE`, `DB_SENSOR_SPALTE`, `DB_ZEIT_SPALTE` – Namen von Tabelle und Schlüsselspalten
- `DB_SPALTEN` – Messgröße → Spaltenname
- `DB_SENSOR_IDS` – Sensor-Kennung aus `SENSOREN` → `sensor_id` in der Datenbank

Fehlende Spalten (z. B. Radon, solange noch kein Sensor liefert) werden einfach übersprungen.
Bei einem „langen“ Schema (eine Zeile je Einzelwert) nur `DbQuelle._abfrage()` in `schnittstelle.py` umbauen.

**Für den Backend-Branch:** Die Mittelung für lange Zeiträume läuft derzeit in pandas, d. h. bei „30 Tage“ Übertragung aller 5-s-Werte.
Bei großen Datenmengen besser in der Datenbank mitteln (z. B. TimescaleDB `time_bucket`) – Stelle in `DbQuelle.verlauf()` (`schnittstelle.py`) ist kommentiert.


## Was wo ändern

**Neuer Sensor eines bekannten Geräts** (z. B. zweiter Accutron Pro)
1. `config.py`: Eintrag in `SENSOREN` mit Kennung, Standort, Name, Messgrößen, Farbe
2. CSV-Betrieb: Eintrag in `EXPORTE` in `config.py` (Ordner, Zeitspalte, Spalten)
3. DB-Betrieb: Eintrag in `DB_SENSOR_IDS` in `config.py`

**Neue Messgröße**
1. `config.py`: Eintrag in `MESSGROESSEN` – Position im Dictionary = Position der Zeile auf der Seite
2. Spalte in `EXPORTE` bzw. `DB_SPALTEN` in `config.py` zuordnen

**Neues Gerät mit eigenem CSV-Format**
Eintrag in `EXPORTE` in `config.py`: Ordnername, Name der Zeitspalte, Zuordnung CSV-Spalte → Messgröße, bei Bedarf `faktoren` für die Umrechnung in die Anzeigeeinheit.

**Andere Zeiträume, Mittelung, Aktualisierung, Schriftgrößen, Abstände oder Diagrammhöhe**
Abschnitt „Anzeige“ in `config.py`. Faustregel: rund 1000 Punkte je Linie – mehr bringt im Diagramm nichts, macht es aber langsamer.


## Besonderheiten der Rohdaten

Alles bereits beim Einlesen abgefangen (`schnittstelle.py`, Einstellungen je Gerät in `config.py`), hier nur zur Nachvollziehbarkeit:

| Gerät             | Besonderheit                                                                      | Umgang                                        |
| ----------------- | --------------------------------------------------------------------------------- | --------------------------------------------- |
| alle              | Tabulator als Trenner, Dezimalkomma, Leerzeichen vor jedem Wert                   | beim Einlesen bereinigt                       |
| alle              | vereinzelt Zeilen mit hunderten führenden Leerzeichen (vermutlich Geräteneustart) | Leerzeichen entfernt, Zeile bleibt erhalten   |
| Maestro Zephyr    | Luftdruck in kPa                                                                  | × 10 → hPa                                    |
| Maestro Zephyr    | `DeviceTime` steht auf 1999                                                       | stattdessen `SystemTime`                      |
| Maestro Zephyr    | Wettergeschwindigkeit teils negativ                                               | bleibt so, Vorzeichen = Strömungsrichtung     |
| Vaisala           | `Devicetime` in UTC, eine Stunde hinter `Systemtime`                              | stattdessen `Systemtime`                      |
| Vaisala           | `Water Activity` konstant 3,28 (physikalisch 0–1)                                 | nicht verwendet                               |
| Accutron SP Ultra | unter 0,3 m/s laut Projektvorstellung nicht verlässlich                           | noch keine Kennzeichnung, siehe offene Punkte |
| Accutron SP Ultra | vereinzelt doppelte Zeitstempel                                                   | nur einmal übernommen                         |


## Stand und nächste Schritte

- [x] Grundgerüst, Übersicht je Standort mit aktuellen Werten und Verlauf
- [x] Schnittstelle mit CSV- und Datenbank-Quelle
- [ ] Filter nach Standort, Sensortyp und Messgröße, Suchfunktion
- [ ] Feinschliff Darstellung: Formelzeichen, Radon, Strömungsrichtung, unsichere Messbereiche
- [ ] Schwellwerte, farbliche Hervorhebung, Alarme mit Benachrichtigung
- [ ] 3D-Modell des Bergwerks
- [ ] Betrieb auf dem Server, Zugriff aus dem Uni-Netz bzw. per VPN
- [ ] Datenbank und Datenerfassung (eigener Backend-Branch)

**Offene Punkte**
- Schwellwerte für Warnungen und Alarme – kommen von den Projektpartnern
- Messwerte des Radonsensors (RadonTec) und Berechnung des Volumenstroms aus den Differenzdrücken (Sensirion)
- Darstellung: Diagrammhöhe (derzeit 200 px), Mittelung bei 24 h (1 min oder stärker glätten?) – beides in `config.py`


## Ansprechpartner Projekt

Dr.-Ing. Franziska Günther, Dipl.-Ing. Max Friedemann – Institut für Bergbau und Spezialtiefbau, TU Bergakademie Freiberg
