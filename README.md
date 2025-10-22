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
 Screenshot-Name | Screenshot-Wert | Log-Index | Log-Wert | Code-Variable | Status |
|----------------|-----------------|-----------|----------|---------------|--------|
| **Temp. Vorlauf (HK 1)** | 14.8 °C | Index 64 | 14.7 | `TVL_1` | ✅ Korrekt |
| **Raumtemp. (HK 1)** | 20.5 °C | Index 50 | 24 | `Raumtemp` | ⚠️ Ungenau |
| **Kessel Temperatur Ist** | 14.6 °C | Index 3 | 14.5 | `TK` | ✅ Korrekt |
| **Kessel Temperatur Soll** | 0 °C | Index 4 | 0 | `TK_Soll` | ✅ Korrekt |
| **Rauchgastemperatur** | 21 °C | Index 5 | 14.9 | `TRG` | ⚠️ Alt/verzögert |
| **Leistung** | 0 % | Index 8 | 20.9 | `Leistung` | ⚠️ Alt/verzögert |
| **Sauerstoffgehalt Ist** | 1.2 % | Index 1 | 1.2 | `O2_Ist` | ✅ Korrekt |
| **Sauerstoffgehalt Soll** | 7.5 % | Index 2 | 7.5 | `O2_Soll` | ✅ Korrekt |
| **Rücklauf Temperatur Ist** | 15 °C | Index 23 | 100 | `TRL` | ❌ Falsch! |
| **Rücklauf Temperatur Soll** | 35 °C | Index 24 | 85 | `TRL_Soll` | ⚠️ Ungenau |
| **Höchste Anforderung** | 0 °C | ? | ? | - | ❓ Nicht gefunden |
| **Temperatur Kombi (PK)** | null °C | ? | ? | - | ❓ Nicht gefunden |
| **Leistung Kombi (PK)** | null % | ? | ? | - | ❓ Nicht gefunden |
| **Lagerstand Kombi (PK)** | null kg | ? | ? | - | ❓ Nicht gefunden |
| **Systemdruck** | 0 bar | ? | ? | - | ❓ Nicht gefunden |
| **Lagerstand** | 0 kg | Index 46 | 50.1 | `Lagerstand` | ❌ Widerspruch! |
| **Temperatur Puffer (oben)** | 30.4 °C | Index 19 | 30 | `TPo` | ✅ Korrekt |
| **Temperatur Puffer (Mitte)** | 30.1 °C | Index 22 | 30.0 | `TPm` | ✅ Korrekt |
| **Temperatur Puffer (unten)** | 27.9 °C | Index 13 | 27.8 | `TPu` | ✅ Korrekt |
| **Puffer Füllgrad** | 21 % | Index 42 | 2809 | `Puff_Fuellgrad / 100` | ✅ Korrekt (geteilt) |
| **Außentemperatur** | 13 °C | Index 54 | 13.1 | `Taus` | ✅ Korrekt |
| **FWS Fühler** | 30.6 °C | Index 55 | 12.3 | `FWS_Fuehler` | ❌ Falsch! |
| **FWS Vorlauf** | 30.6 °C | Index 110? | ? | `FWS_Vorlauf` | ❓ Geschätzt |
