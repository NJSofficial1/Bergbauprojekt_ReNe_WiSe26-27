"""Datenanbindung der Oberfläche – alles, was frontend.py über Daten wissen muss, steht hier.

Aufbau:
1. Datenquelle – Vertrag mit vier Methoden; nur diese ruft frontend.py auf
2. CsvQuelle   – monatliche CSV-Exporte aus der Nextcloud (Übergang)
3. DbQuelle    – zentrale Datenbank über SQLAlchemy (PostgreSQL, MariaDB, SQLite …)
4. oeffne_quelle() – einzige Stelle für den Wechsel der Quelle

Einstellungen (Sensoren, Ordner, Spaltenzuordnung, DB-Schema) in config.py, hier nur die Logik.

Vertrag für jede Quelle:
- Messgrößen immer unter den Schlüsseln aus config.MESSGROESSEN, nie unter Spaltennamen der Quelle
- Werte bereits in Anzeigeeinheit (z. B. hPa statt kPa)
Damit bleibt frontend.py bei jedem Quellen- oder Schemawechsel unverändert.
"""
import re
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, func, select

import config

# ── 1. Schnittstelle ───────────────────────────────────────────────────────────

class Datenquelle(ABC):

    @abstractmethod
    def hat_daten(self, sensor) -> bool:
        """Überhaupt Daten zum Sensor vorhanden – leere Standorte blendet die Oberfläche aus."""

    @abstractmethod
    def jetzt(self) -> pd.Timestamp:
        """Bezugspunkt für „letzte 24 h“ usw. – jüngster Messzeitpunkt aller Sensoren."""

    @abstractmethod
    def aktuelle_werte(self, sensor) -> tuple[pd.Timestamp, dict] | None:
        """(Zeitstempel, {Messgröße: Wert}) der letzten Messung oder None."""

    @abstractmethod
    def verlauf(self, sensor, von, bis, raster=None) -> pd.DataFrame:
        """Messwerte zwischen von und bis: Index Zeitstempel, eine Spalte je Messgröße.
        raster (z. B. "1min"): Mittelwerte je Intervall, für lange Zeiträume unverzichtbar."""


# ── 2. CSV-Exporte ─────────────────────────────────────────────────────────────


def _lies_datei(pfad, kennung):
    export = config.EXPORTE[kennung]
    roh = pd.read_csv(pfad, sep="\t", dtype=str,
                      usecols=lambda s: s.strip() in {export["zeit"], *export["spalten"]})
    roh.columns = roh.columns.str.strip()
    roh = roh.apply(lambda spalte: spalte.str.strip())  # einzelne Zeilen mit vielen Leerzeichen

    tabelle = pd.DataFrame(index=pd.to_datetime(roh[export["zeit"]], errors="coerce"))
    for spalte, groesse in export["spalten"].items():
        werte = pd.to_numeric(roh[spalte].str.replace(",", "."), errors="coerce")
        tabelle[groesse] = werte.to_numpy() * export.get("faktoren", {}).get(groesse, 1)
    return tabelle[tabelle.index.notna()]


@lru_cache(maxsize=24)  # 24 Monatstabellen, z. B. 8 Monate aller drei Geräte – Speicher begrenzen
def _lies_monat(dateien, kennung):
    """Alle Dateien eines Monats als eine Tabelle.
    dateien: ((Pfad, Änderungszeit), …) – Änderungszeit nur für den Cache: geänderte Datei neu einlesen."""
    tabelle = pd.concat(_lies_datei(pfad, kennung) for pfad, _ in dateien)
    # doppelte Zeitstempel aus Kopien wie …_1.csv nur einmal
    return tabelle[~tabelle.index.duplicated()].sort_index()


class CsvQuelle(Datenquelle):

    def __init__(self, ordner=config.CSV_ORDNER):
        self.ordner = Path(ordner)

    def _monatsdateien(self, sensor):
        """{Monatsanfang: [Pfade]} – Monat aus dem Dateinamen, da 2026-01 und 2026_01 gemischt.
        Liste statt Einzelpfad: mehrere Dateien je Monat möglich (Teilexporte, Kopien wie …_1.csv)."""
        if sensor.kennung not in config.EXPORTE:
            return {}
        dateien = {}
        for pfad in (self.ordner / config.EXPORTE[sensor.kennung]["ordner"]).glob("*.csv"):
            if treffer := re.search(r"(\d{4})[-_](\d{2})", pfad.name):
                monat = pd.Timestamp(int(treffer[1]), int(treffer[2]), 1)
                dateien.setdefault(monat, []).append(pfad)
        return dict(sorted(dateien.items()))

    def _monat(self, pfade, sensor):
        dateien = tuple((str(p), p.stat().st_mtime) for p in sorted(pfade))
        return _lies_monat(dateien, sensor.kennung)

    def hat_daten(self, sensor):
        return bool(self._monatsdateien(sensor))

    def jetzt(self):
        zeiten = [stand[0] for s in config.SENSOREN if (stand := self.aktuelle_werte(s))]
        return max(zeiten, default=pd.Timestamp.now())

    def aktuelle_werte(self, sensor):
        monate = self._monatsdateien(sensor)
        if not monate:
            return None
        tabelle = self._monat(list(monate.values())[-1], sensor)
        return (tabelle.index[-1], tabelle.iloc[-1].to_dict()) if len(tabelle) else None

    def verlauf(self, sensor, von, bis, raster=None):
        # nur Monate laden, die den Zeitraum berühren – bei 24 h meist ein einziger
        monate = [self._monat(pfade, sensor) for monat, pfade in self._monatsdateien(sensor).items()
                  if monat <= bis and monat + pd.offsets.MonthBegin() > von]
        if not monate:
            return pd.DataFrame()
        tabelle = pd.concat(monate).loc[von:bis]
        return tabelle.resample(raster).mean() if raster else tabelle


# ── 3. Datenbank ───────────────────────────────────────────────────────────────
# Schema-Zuordnung in config.py. Für ein „langes“ Schema (eine Zeile je Einzelwert)
# nur _abfrage() umbauen, Rest bleibt.


class DbQuelle(Datenquelle):

    def __init__(self, url):
        # pool_pre_ping: abgebrochene Verbindungen (VPN, Netzwechsel) vor Gebrauch erkennen
        self.engine = create_engine(url, pool_pre_ping=True)
        self.tabelle = Table(config.DB_TABELLE, MetaData(), autoload_with=self.engine)
        # nur Messgrößen, deren Spalte es wirklich gibt
        self.spalten = {g: s for g, s in config.DB_SPALTEN.items() if s in self.tabelle.c}

    def _abfrage(self, sensor, *bedingungen, neueste_zuerst=False, anzahl=None):
        t = self.tabelle
        sql = (select(t.c[config.DB_ZEIT_SPALTE].label("zeit"),
                      *(t.c[s].label(g) for g, s in self.spalten.items() if g in sensor.messgroessen))
               .where(t.c[config.DB_SENSOR_SPALTE] == config.DB_SENSOR_IDS.get(sensor.kennung), *bedingungen)
               .order_by(t.c[config.DB_ZEIT_SPALTE].desc() if neueste_zuerst else t.c[config.DB_ZEIT_SPALTE])
               .limit(anzahl))
        with self.engine.connect() as verbindung:
            tabelle = pd.read_sql(sql, verbindung, parse_dates=["zeit"])
        return tabelle.set_index("zeit").sort_index()

    def hat_daten(self, sensor):
        return sensor.kennung in config.DB_SENSOR_IDS and not self._abfrage(sensor, anzahl=1).empty

    def jetzt(self):
        with self.engine.connect() as verbindung:
            neueste = verbindung.scalar(select(func.max(self.tabelle.c[config.DB_ZEIT_SPALTE])))
        # bei laufender Erfassung ≈ aktuelle Uhrzeit, bei alten Testdaten deren Ende
        return pd.Timestamp(neueste) if neueste else pd.Timestamp.now()

    def aktuelle_werte(self, sensor):
        tabelle = self._abfrage(sensor, neueste_zuerst=True, anzahl=1)
        return (tabelle.index[-1], tabelle.iloc[-1].to_dict()) if len(tabelle) else None

    def verlauf(self, sensor, von, bis, raster=None):
        zeit = self.tabelle.c[config.DB_ZEIT_SPALTE]
        tabelle = self._abfrage(sensor, zeit >= von.to_pydatetime(), zeit <= bis.to_pydatetime())
        # Mittelung hier in pandas, damit es mit jeder Datenbank läuft. Bei großen Datenmengen
        # besser in der DB mitteln (z. B. TimescaleDB time_bucket) – nur diese Stelle ändern.
        return tabelle.resample(raster).mean() if raster and len(tabelle) else tabelle


# ── 4. Auswahl der Quelle ──────────────────────────────────────────────────────

def oeffne_quelle() -> Datenquelle:
    """Einzige Stelle für den Wechsel der Datenquelle – Auswahl über DATENQUELLE in config.py."""
    if config.DATENQUELLE == "db":
        if not config.DB_URL:
            raise RuntimeError("DATENQUELLE=db, aber keine DB_URL gesetzt (Umgebungsvariable oder config.py).")
        return DbQuelle(config.DB_URL)
    return CsvQuelle()
