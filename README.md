# Bergbauprojekt_ReNe_WiSe26-27

# Zeitplanung

| Woche vom ... | umzusetzende Themen | Verantwortliche |
| :--: | :--: | :--: |
|09.11.2026 - 15.11.2026 | Zeitplanung und grobes Layout | alle Gruppenmitglieder |

---

# Anforderungsanalyse 

## Frontend
+ intuitive Bedienung:
  + wenige Klickwege
  + kurze Ladezeiten, schnelle Übergänge nach Nutzerinteraktion
+  Features und darzustellende Werte:
  + Echtzeitwerte
  + Historie in Diagrammform
  + Filterung nach Sensortyp
  + Darstellung spezifischer Einheiten (gegebene Werte, Radon, Strömungsrichtung und -geschwindigkeit, etc.)
  + visuelle Hervorhebung von Warn- und Schwellwerten, eventuelles Einrichten einer Alarmfunktion inkl. Benachrichtigung
  + Skalierbarkeit, schnelle Erweiterbarkeit und entsprechende Datenstrukturen sowie Layoutelemente dafür
  + Einstellung von Filtern und evtl. Implementieren einer Suchfunktion
  + Standortauswahl in der 3d karte nach standort
+ Zugänglichkeit:
  + Zugriff aus dem Uni-Netz heraus bzw. per VPN
    

## Backend
+ zentrales Empfangen, Sammeln und Auswerten von Daten mehrerer Raspberry-Pi - Geräte
+ Ableitung, Berechnung, Ermittlung der im Frontend dargestellten Größen, Parameter und Werte aus den Rohdaten
+ Skalierbarkeit und eventuelle Schnittstelle zur Steuerung der Belüftungsanlage im Bergwerk
+ REST-API (Schnittstelle zum Frontend):
  + Endpunkte für Live-Abfragen (Polling/WebSockets für das 5-Sekunden-Intervall)
	+ Filterbare Endpunkte für historische Daten (nach Sensor, Standort, Messgröße und Zeitraum)
	+ Endpunkte für Metadaten (Standortkoordinaten, Sensor-Status, Schwellenwerte)
 
 ## Datenbank
+ Zeitreihen-Speicherung: effiziente Speicherung hochfrequenter Messdaten (Aufzeichnungsintervall ca. alle 5 Sekunden) über lange Zeiträume (Monate/Jahre)
+ Datenmodellierung: saubere Trennung zwischen Stammdaten (Sensortyp, Einbauort, Messbereich, Genauigkeit) und Bewegungsdaten (Zeitstempel, Messwert)
+ Skalierbarkeit: einfache Erweiterbarkeit für neue Standorte und Sensoren (aktuell ca. 4 installierte, mindestens 5 weitere geplante Sensoren)
+ Daten-Import: Möglichkeit zum Einspielen bestehender historischer Messwerte der letzten Monate
