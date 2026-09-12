# Automatisierte Stückzählung am Förderband mit dem Raspberry Pi

Digitales Zählsystem für Holzbretter am Förderband. Entwickelt als Abschlussprojekt zum Ende des ersten Halbjahres meiner Umschulung zum Fachinformatiker für Anwendungsentwicklung am BFW Schömberg (Sommer 2026).

## Dokumente

- [Projektskizze](Projektskizze.pdf)
- [Projektdokumentation](Projektdokumentation.pdf)

## Ausgangssituation
Bisher wurden durchlaufende Holzbretter von Hand mit Zettel und Stift gezählt. Das kostete Zeit und war fehleranfällig. Ziel war ein System, das automatisch zählt, den aktuellen Stand anzeigt und die Werte für spätere Auswertungen speichert.

## Funktionsumfang

- Berührungslose Erkennung jedes durchlaufenden Bretts über eine Lichtschranke
- Live-Anzeige des Zählerstands auf einem 16x2 LCD-Display
- Aufteilung der Zählung in Chargen (Aufträge oder Lieferungen) per Tasterdruck
- Automatischer Tageswechsel um Mitternacht
- Absicherung gegen Datenverlust bei Stromausfall, mit automatischer Wiederaufnahme der offenen Charge nach Neustart
- Persistente Speicherung aller Werte in einer XML-Datei

## Hardware

| Bauteil | Bezeichnung | Aufgabe |
|---|---|---|
| Recheneinheit | Raspberry Pi 4 (4 GB) | zählt, zeigt an, speichert |
| Laser-Modul | KY-008 | Sender der Lichtschranke |
| Lichtsensor-Modul | KY-018 | Empfänger der Lichtschranke |
| Taster-Modul | KY-004 | startet eine neue Charge |
| Display | LCD 16x2 (I2C) | zeigt Zählerstand und Uhrzeit |
| Echtzeituhr | DS1307 (I2C) | liefert Uhrzeit auch ohne Internet |

## Technischer Ansatz

Gezählt wird nicht der Zustand der Lichtschranke, sondern der Signalwechsel von "frei" zu "unterbrochen". So wird jedes Brett unabhängig von seiner Durchlaufgeschwindigkeit genau einmal erfasst. Eine Entprellung von 50 Millisekunden verhindert Mehrfachzählungen durch kurzes Signalflackern. Nach jedem gezählten Brett wird der Stand sofort in einer XML-Datei gesichert, sodass bei einem Stromausfall keine Daten verloren gehen und die offene Charge nach einem Neustart automatisch fortgesetzt wird.

## Herausforderungen

Die größte Herausforderung war die Sensorauswahl. Mehrere Ansätze scheiterten an unzuverlässigen oder flackernden Signalen, darunter ein sichtbarer Laser an einem Infrarot-Empfänger, eine getaktete Infrarot-Sendediode und ein Infrarot-Abstandssensor. Die stabile Lösung war schließlich die Kombination aus Laser-Modul (KY-008) und Lichtsensor-Modul (KY-018), die ein sauberes An/Aus-Signal liefert.

## Tech-Stack

Python 3, RPi.GPIO, RPLCD, Raspberry Pi OS (Lite), Entwicklung über VS Code mit Remote-SSH.

## Status

Projekt erfolgreich abgeschlossen. Umfang: 40 Stunden, Abschlussprojekt zum Ende des ersten Halbjahres der Umschulung, Sommer 2026.

## Lizenz

Wird noch festgelegt.
