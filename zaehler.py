import time
import datetime
import os
import xml.etree.ElementTree as ET
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

# ── Einstellungen ─────────────────────────────────────────────────────────────
LASER_PIN      = 18
EMPFAENGER_PIN = 25
BUTTON_PIN     = 17

XML_DATEI    = '/home/mark/zaehler_daten.xml'
ENTPRELLZEIT = 0.05          # 50 ms, gilt fuer Sensor und Taster

# ── Hardware vorbereiten ──────────────────────────────────────────────────────
lcd = CharLCD('PCF8574', 0x27)
lcd.clear()

GPIO.setmode(GPIO.BCM)
GPIO.setup(LASER_PIN,      GPIO.OUT)
GPIO.setup(EMPFAENGER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_PIN,     GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(LASER_PIN, GPIO.HIGH)

# ── kleine Helfer ─────────────────────────────────────────────────────────────
def jetzt_zeit():
    return datetime.datetime.now().strftime('%H:%M:%S')

def heute_datum():
    return datetime.date.today().strftime('%Y-%m-%d')

def lcd_zeile(zeile, text):
    lcd.cursor_pos = (zeile, 0)
    lcd.write_string(text.ljust(16))

# ── XML: einmal laden, im Speicher halten ─────────────────────────────────────
def xml_laden():
    if os.path.exists(XML_DATEI):
        return ET.parse(XML_DATEI)
    return ET.ElementTree(ET.Element('zaehler'))

tree = xml_laden()
root = tree.getroot()

def speichern():
    # Schreibt den aktuellen Stand komplett auf die Karte
    ET.indent(tree)
    tree.write(XML_DATEI, encoding='unicode', xml_declaration=True)

def tag_holen(datum):
    # Vorhandenen Tag-Eintrag suchen oder neu anlegen
    for tag in root.findall('tag'):
        if tag.get('datum') == datum:
            return tag
    tag = ET.SubElement(root, 'tag')
    tag.set('datum',  datum)
    tag.set('gesamt', '0')
    return tag

def offene_charge(tag):
    # Gibt die noch nicht beendete Charge zurueck, falls es eine gibt
    for charge in tag.findall('charge'):
        if charge.get('status') == 'offen':
            return charge
    return None

def neue_charge(tag, nummer):
    charge = ET.SubElement(tag, 'charge')
    charge.set('nummer', str(nummer))
    charge.set('start',  jetzt_zeit())
    charge.set('wert',   '0')
    charge.set('status', 'offen')
    return charge

# ── Startzustand wiederherstellen ─────────────────────────────────────────────
# Nach einem Stromausfall wird hier der letzte gespeicherte Stand geladen.
tag_element    = tag_holen(heute_datum())
gesamt_zaehler = int(tag_element.get('gesamt', '0'))

charge_element = offene_charge(tag_element)
if charge_element is None:
    charge_nummer  = len(tag_element.findall('charge')) + 1
    charge_element = neue_charge(tag_element, charge_nummer)
    speichern()
else:
    # offene Charge gefunden: dort weiterzaehlen, wo es aufgehoert hat
    charge_nummer = int(charge_element.get('nummer'))

charge_zaehler = int(charge_element.get('wert', '0'))

letzter_status        = GPIO.input(EMPFAENGER_PIN)
letzter_button        = GPIO.input(BUTTON_PIN)
letzter_impuls        = 0.0
letzter_button_impuls = 0.0
letzter_tag           = datetime.date.today()
letzte_uhrzeit        = ''

lcd_zeile(0, f'C{charge_nummer}: {charge_zaehler}')
lcd_zeile(1, jetzt_zeit())
print("Zaehler aktiv | Strg+C zum Beenden")
print(f"Charge {charge_nummer} laeuft (Stand: {charge_zaehler})")
print("-" * 40)

# ── Aktionen ──────────────────────────────────────────────────────────────────
def brett_zaehlen():
    global gesamt_zaehler, charge_zaehler
    gesamt_zaehler += 1
    charge_zaehler += 1
    # Stand sofort sichern, damit bei Stromausfall nichts verloren geht
    tag_element.set('gesamt', str(gesamt_zaehler))
    charge_element.set('wert', str(charge_zaehler))
    speichern()
    lcd_zeile(0, f'C{charge_nummer}: {charge_zaehler}, G: {gesamt_zaehler}')
    print(f"[{jetzt_zeit()}]  Gezaehlt! Charge: {charge_zaehler} | Gesamt: {gesamt_zaehler}")

def charge_beenden():
    global charge_nummer, charge_zaehler, charge_element
    charge_element.set('ende',   jetzt_zeit())
    charge_element.set('status', 'beendet')
    print(f"Charge {charge_nummer} beendet: {charge_zaehler} Teile")
    # neue Charge starten
    charge_nummer += 1
    charge_zaehler = 0
    charge_element = neue_charge(tag_element, charge_nummer)
    speichern()
    lcd_zeile(0, f'C{charge_nummer}: {charge_zaehler}, G: {gesamt_zaehler}')
    print(f"Charge {charge_nummer} gestartet um {charge_element.get('start')}")

def tageswechsel(neuer_tag):
    global tag_element, charge_element, gesamt_zaehler, charge_zaehler, charge_nummer, letzter_tag
    # offene Charge des alten Tages abschliessen
    charge_element.set('ende',   jetzt_zeit())
    charge_element.set('status', 'beendet')
    # neuen Tag anlegen
    tag_element    = tag_holen(neuer_tag.strftime('%Y-%m-%d'))
    gesamt_zaehler = 0
    charge_zaehler = 0
    charge_nummer  = 1
    charge_element = neue_charge(tag_element, charge_nummer)
    letzter_tag    = neuer_tag
    speichern()
    lcd_zeile(0, f'C{charge_nummer}: {charge_zaehler}, G: {gesamt_zaehler}')
    print("Mitternacht. Neuer Tag, Charge 1 gestartet.")

# ── Hauptschleife ─────────────────────────────────────────────────────────────
try:
    while True:
        jetzt  = time.time()
        heute  = datetime.date.today()
        status = GPIO.input(EMPFAENGER_PIN)
        button = GPIO.input(BUTTON_PIN)

        # Tageswechsel um Mitternacht
        if heute != letzter_tag:
            tageswechsel(heute)

        # Zählen: nur beim Wechsel auf "unterbrochen" (LOW), mit Entprellung
        if status != letzter_status:
            if status == GPIO.LOW and (jetzt - letzter_impuls) >= ENTPRELLZEIT:
                letzter_impuls = jetzt
                brett_zaehlen()
            letzter_status = status

        # Taster: Charge beenden, mit Entprellung
        if button == GPIO.LOW and letzter_button == GPIO.HIGH:
            if (jetzt - letzter_button_impuls) >= ENTPRELLZEIT:
                letzter_button_impuls = jetzt
                charge_beenden()
            letzter_button = button

        # Uhrzeit jede Sekunde aktualisieren
        uhrzeit = jetzt_zeit()
        if uhrzeit != letzte_uhrzeit:
            lcd_zeile(1, uhrzeit)
            letzte_uhrzeit = uhrzeit

        time.sleep(0.01)

except KeyboardInterrupt:
    charge_element.set('ende',   jetzt_zeit())
    charge_element.set('status', 'beendet')
    speichern()
    GPIO.output(LASER_PIN, GPIO.LOW)
    lcd.clear()
    lcd.write_string(f'Gesamt: {gesamt_zaehler}')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('Programm Ende')
    time.sleep(10)
    lcd.clear()
    GPIO.cleanup()
    print(f"Beendet. Charge {charge_nummer}: {charge_zaehler} | Gesamt: {gesamt_zaehler}")
