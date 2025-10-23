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
| Screenshot-Wert | Soll-Wert | Log-Index | Log-Wert | Code-Variable | ✓ Status |
|----------------|-----------|-----------|----------|---------------|----------|
| **Temp. Vorlauf (HK 1)** | 14.4 °C | Index 64 | 14.4 | `TVL_1` | ✅ |
| **Raumtemp. (HK 1)** | 20 °C | Index 50 | 24 | - | ❌ 24 ≠ 20 |
| **Kessel Temperatur Ist** | 14.3 °C | Index 3 | 14.2 | `TK` | ✅ |
| **Kessel Temperatur Soll** | 0 °C | Index 4 | 0 | `TK_Soll` | ✅ |
| **Rauchgastemperatur** | 20.9 °C | Index 5 | 14.6 | `TRG` | ❌ 14.6 ≠ 20.9 |
| **Leistung** | 0 % | Index 8 | 20.8 | `Leistung` | ❌ 20.8 ≠ 0 |
| **Sauerstoffgehalt Ist** | 1.2 % | Index 1 | 1.2 | `O2_Ist` | ✅ |
| **Sauerstoffgehalt Soll** | 7.5 % | Index 2 | 7.5 | `O2_Soll` | ✅ |
| **Rücklauf Temperatur Ist** | 14.7 °C | Index 14 | **14** | - | ✅ NEU! |
| **Rücklauf Temperatur Soll** | 35 °C | Index 24 | 85 | `TRL_Soll` | ❌ 85 ≠ 35 |
| **Temperatur Puffer (oben)** | 27.2 °C | Index 19 | 27 | `TPo` | ✅ |
| **Temperatur Puffer (Mitte)** | 26.0 °C | Index 22 | 30.0 | `TPm` | ❌ 30 ≠ 26 |
| **Temperatur Puffer (unten)** | 25.3 °C | Index 13 | 25.2 | `TPu` | ✅ |
| **Puffer Füllgrad** | 14 % | Index 42 | 2809 | `/100` | ❌ 28 ≠ 14 |
| **Außentemperatur** | 8.7 °C | Index 54 | 8.7 | `Taus` | ✅ |
| **FWS Fühler** | 27.3 °C | Index 110 | **27.1** | - | ✅ NEU! |
| **FWS Vorlauf** | 27.3 °C | Index 111 | **27.2** | - | ✅ NEU! |
| **Lagerstand** | 50.1 kg | Index 46 | 50.1 | `Lagerstand` | ✅ |

## 📊 Erweiterte Zuordnungstabelle FWS:

| Beschreibung | Soll-Wert | Log-Index | Log-Wert | Status |
|-------------|-----------|-----------|----------|---------|
| **FWS Vorlauftemp Ist** | 27 °C | Index 110 | 27.1 | ✅ |
| **FWS Fühler (Mitte?)** | 27.3 °C | Index 111 | 27.2 | ✅ |
| **FWS Auslauftemp Soll** | 50 °C | Index 112 | 50 | ✅ NEU! |
| **FWS Gesamtverbrauch** | 16292 l | Index 117 | 16292 | ✅ NEU! |
| **FWS Durchfluss** | -- l/min | ? | 0 | ❓ |

