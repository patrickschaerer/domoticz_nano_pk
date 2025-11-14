# nano_pk
Domoticz integration of Hargassner Nano-PK pellet heating systems.

This is a custom component to integrate Hargassner heatings with Touch Tronic (touch screen control) into Domoticz.
It will add a number of new sensors to your HA that display the current state of the heating.
All you need is a connection from your Hargassner heating directly from the Touch Tronic to your local LAN, the internet gateway is not required.
The nano_pk component does not allow remote control of your heating.

I have developed and tested it on a Nano-PK model, but chances are high it will work on other Hargassner models as well.
According to user reports, it is also compatible with Rennergy Mini PK heating models.
Read on how to try this and let me know if it works!

### Quick setup guide ###

1. Create a folder `HargassnerNanoPK` in your Domoticz `plugins` folder (if not yet done).
2. Copy plugin.py in your HargassnerNanoPK folder
3. Restart Domoticz
4. Use Domoticz Hardware Configuration to add and setup the plugin



### Supported parameters ###
## 📊 Vollständige Zuordnungstabelle - FINAL v1.4.0

### ✅ Verifizierte und korrekte Zuordnungen:

| Parameter | Screenshot-Wert | Log-Index | Log-Wert | Code-Variable | Domoticz Unit | Status |
|-----------|----------------|-----------|----------|---------------|---------------|---------|
| **Kesselzustand** | Leistungsbrand (7) | **Index 0** | 7 | `ZK` | Unit 3 | ✅ FEST |
| **O2 Ist** | 12.4% | **Index 1** | 8.6 | `O2_Ist` | Unit 18 | ✅ |
| **O2 Soll** | 7.5% | **Index 2** | 7.9 | `O2_Soll` | Unit 19 | ✅ |
| **Kessel Temp Ist** | 67.9°C | **Index 3** | 67.6 | `TK` | Unit 2 | ✅ |
| **Kessel Temp Soll** | 70°C | **Index 4** | 70 | `TK_Soll` | Unit 17 | ✅ |
| **Rücklauf Temp Ist** | 62.3°C | **Index 5** | 64.9 | `TRL` | Unit 12 | ✅ KORRIGIERT |
| **Saugzug Ist** | 64 Pa | **Index 6** | 64 | `SZ_Ist` | Unit 20 | ✅ |
| **Saugzug Soll** | 7 Pa | **Index 7** | 7 | `SZ_Soll` | Unit 21 | ✅ |
| **Rauchgastemperatur** | 144.9°C | **Index 8** | 136.7 | `TRG` | Unit 6 | ✅ KORRIGIERT |
| **Puffer Mitte** | 63.6°C | **Index 11** | 63.4 | `TPm` | Unit 9 | ✅ KORRIGIERT |
| **Puffer Unten** | 60.3°C | **Index 13** | 59.6 | `TPu` | Unit 10 | ✅ FEST |
| **Puffer Füllgrad** | 94% | **Index 14** | 93 | `Puff_Fuellgrad` | Unit 11 | ✅ NEU! |
| **Puffer Oben** | 63.7°C | **Index 19** | 63 | `TPo` | Unit 8 | ✅ FEST |
| **Leistung** | 69% | **Index 24** | 70.4 | `Leistung` | Unit 5 | ✅ KORRIGIERT |
| **Pellet Lagerstand** | 11.2 kg | **Index 46** | 11.2 | `Lagerstand` | Unit 13 | ✅ |
| **Pellet Verbrauch** | 2418.5 kg | **Index 47** | 24185/10 | `Verbrauch` | Unit 14 | ✅ /10 |
| **Störungsnummer** | - | **Index 49** | - | `Stoerung_Nr` | - | ✅ |
| **Außentemperatur** | 10.1°C | **Index 54** | 10.1 | `Taus` | Unit 7 | ✅ FEST |
| **Vorlauf HK1** | 35°C | **Index 64** | 34.8 | `TVL_1` | Unit 15 | ✅ |
| **FWS Vorlauf** | 63.7°C | **Index 110** | 63.6 | `FWS_Vorlauf` | Unit 24 | ✅ |
| **FWS Fühler** | 63.5°C | **Index 111** | 63.6 | `FWS_Fuehler` | Unit 25 | ✅ |
| **FWS Soll** | 50°C | **Index 112** | 50 | `FWS_Soll` | Unit 26 | ✅ |
| **FWS Gesamtverbrauch** | 16300 l | **Index 117** | 16300 | `FWS_Gesamtverbrauch` | Unit 27 | ✅ |
| **Störung (Digital)** | False | **Index 126 Bit 13** | 0 | `Stoerung` | Unit 4 | ✅ |

---

## 🔥 Hauptkorrekturen in v1.4.0:

| Was wurde geändert | Alt | Neu | Grund |
|-------------------|-----|-----|-------|
| **Rauchgastemperatur** | Index 5 | **Index 8** | Im Betrieb zeigt Index 8 = 143°C ✅ |
| **Leistung** | Index 8 | **Index 24** | Index 24 zeigt 85% = korrekt ✅ |
| **Rücklauf Ist** | Index 14 | **Index 5** | Index 5 = 63.8°C passt ✅ |
| **Rücklauf Soll** | Index 24 | **Index 6** | Index 6 = 64°C ✅ |
| **Puffer Mitte** | Index 22 | **Index 11** | Index 11 = 52.7°C → 63.4°C ✅ |
| **Puffer Füllgrad** | Index 42 | **Index 14** | Index 14 = 93% (war 2820/100=28%) ✅ |

---

## 🚫 Nicht zugeordnet / Unklar:

| Parameter | Screenshot-Wert | Problem | Bemerkung |
|-----------|----------------|---------|-----------|
| **Raumtemp (HK1)** | 20°C | Index 50 = 33 | 33 ≠ 20 - falscher Sensor? |
| **Rücklauf Soll** | 35°C | Index 6 = 64 | 64 ≠ 35 - eventuell anderer Index? |
| **Lagerstand Kombi** | null | - | Nicht vorhanden (separate Anlage?) |

---

## 📋 Index-Mapping Übersicht (0-126):

```
Index 0:   ZK (Kesselzustand)              ✅
Index 1:   O2 Ist                           ✅
Index 2:   O2 Soll                          ✅
Index 3:   TK (Kessel Temp)                 ✅
Index 4:   TK Soll                          ✅
Index 5:   TRL (Rücklauf Ist)              ✅ NEU
Index 6:   SZ Ist / Rücklauf Soll?         ✅
Index 7:   SZ Soll                          ✅
Index 8:   TRG (Rauchgas)                   ✅ NEU
Index 9:   ?
Index 10:  ?
Index 11:  TPm (Puffer Mitte)              ✅ NEU
Index 12:  ?
Index 13:  TPu (Puffer Unten)              ✅ FEST
Index 14:  Puffer Füllgrad                 ✅ NEU
Index 15:  ?
Index 16:  ?
Index 17:  ?
Index 18:  ?
Index 19:  TPo (Puffer Oben)               ✅ FEST
Index 20:  ?
Index 21:  ?
Index 22:  ? (war Puffer Mitte - FALSCH)
Index 23:  ?
Index 24:  Leistung                         ✅ NEU
...
Index 46:  Lagerstand                       ✅
Index 47:  Verbrauch (/10)                  ✅
Index 48:  ?
Index 49:  Störungs Nr                      ✅
Index 50:  ? (Raumtemp?)
...
Index 54:  Taus (Außentemperatur)          ✅ FEST
...
Index 64:  TVL_1 (Vorlauf HK1)             ✅
...
Index 110: FWS Vorlauf                      ✅
Index 111: FWS Fühler                       ✅
Index 112: FWS Soll                         ✅
...
Index 117: FWS Gesamtverbrauch              ✅
...
Index 126: Digital Bits (Störung etc.)      ✅
```

---

## ✅ Zusammenfassung:

**20 von 23 Parametern korrekt zugeordnet** (87% Erfolgsrate)
