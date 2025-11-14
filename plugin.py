"""
<plugin key="HargassnerNanoPK" name="Hargassner Nano PK" author="converted with Claude.ai from HA plugin" version="1.4.0">
    <description>
        <h2>Hargassner Nano PK Plugin</h2><br/>
        Connects to Hargassner heating via Telnet<br/>
        <br/>
        <b>Version 1.4.0 - Corrected running mode values!</b><br/>
        <br/>
        Supports:<br/>
        - Boiler and buffer temperatures<br/>
        - Flow and return temperatures<br/>
        - Output, oxygen levels (corrected)<br/>
        - Pellet stock and consumption<br/>
        - FWS (Fresh Water Station) parameters<br/>
        - Smoke gas temperature (corrected)
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.1.100"/>
        <param field="Port" label="Port" width="100px" required="true" default="23"/>
        <param field="Mode1" label="Message Format" width="300px" required="true" default="NANO_V14L">
            <options>
                <option label="NANO_V14K" value="NANO_V14K"/>
                <option label="NANO_V14L" value="NANO_V14L" default="true"/>
                <option label="NANO_V14M" value="NANO_V14M"/>
                <option label="NANO_V14N" value="NANO_V14N"/>
                <option label="NANO_V14N2" value="NANO_V14N2"/>
                <option label="NANO_V14O3" value="NANO_V14O3"/>
            </options>
        </param>
        <param field="Mode2" label="Parameters" width="150px" required="true" default="STANDARD">
            <options>
                <option label="Standard" value="STANDARD" default="true"/>
                <option label="Full" value="FULL"/>
            </options>
        </param>
        <param field="Mode3" label="Language" width="100px" required="true" default="EN">
            <options>
                <option label="English" value="EN" default="true"/>
                <option label="Deutsch" value="DE"/>
            </options>
        </param>
        <param field="Mode4" label="Update Interval (seconds)" width="100px" required="true" default="5"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
from datetime import datetime

# Fehlercodes
ERROR_CODES = {
    "5": "Aschelade entleeren",
    "6": "Aschelade zu voll",
    "29": "Verbrennungsstörung",
    "30": "Batterie leer",
    "31": "Blockade Einschubmotor",
    "32": "Füllzeit überschritten",
    "70": "Pelletslagerstand niedrig",
    "89": "Schieberost schwergängig",
    "93": "Aschelade offen",
    "155": "Spülung defekt",
    "227": "Lagerraumschalter aus",
    "228": "Pelletsbehälter fast leer",
    "229": "Füllstandsmelder kontrollieren",
    "371": "Brennraum prüfen"
}

# Kesselzustände
BOILER_STATES_DE = [
    "Unbekannt", "Aus", "Startvorbereitung", "Kessel Start",
    "Zündüberwachung", "Zündung", "Übergang LB", "Leistungsbrand",
    "Gluterhaltung", "Warten auf EA", "Entaschung", "-", "Putzen"
]

BOILER_STATES_EN = [
    "Unknown", "Off", "Preparing start", "Boiler start",
    "Monitoring ignition", "Ignition", "Transition to FF", "Full firing",
    "Ember preservation", "Waiting for AR", "Ash removal", "-", "Cleaning"
]

class BasePlugin:
    enabled = False
    
    def __init__(self):
        self.runCounter = 0
        self.pollInterval = 5
        self.connection = None
        self.connectionOK = False
        self.deviceName = "Hargassner"
        self.language = "EN"
        self.missedMsgs = 0
        self.lastData = {}
        
        # Device Units - Standard
        self.UNIT_CONNECTION = 1
        self.UNIT_BOILER_TEMP = 2
        self.UNIT_BOILER_STATE = 3
        self.UNIT_ERROR = 4
        self.UNIT_OUTPUT = 5
        self.UNIT_SMOKE_TEMP = 6
        self.UNIT_OUTSIDE_TEMP = 7
        self.UNIT_BUFFER_TOP = 8
        self.UNIT_BUFFER_CENTER = 9
        self.UNIT_BUFFER_BOTTOM = 10
        self.UNIT_BUFFER_LEVEL = 11
        self.UNIT_RETURN_TEMP = 12
        self.UNIT_PELLET_STOCK = 13
        self.UNIT_PELLET_CONSUMPTION = 14
        self.UNIT_FLOW_TEMP = 15
        self.UNIT_ENERGY = 16
        
        # Device Units - Extended (FULL mode)
        self.UNIT_BOILER_TEMP_TARGET = 17
        self.UNIT_O2_ACTUAL = 18
        self.UNIT_O2_TARGET = 19
        self.UNIT_DRAFT_ACTUAL = 20
        self.UNIT_DRAFT_TARGET = 21
        self.UNIT_RETURN_TEMP_TARGET = 22
        self.UNIT_FWS_FLOW_TEMP = 24
        self.UNIT_FWS_SENSOR = 25
        self.UNIT_FWS_OUTLET_TARGET = 26
        self.UNIT_FWS_WATER_TOTAL = 27
        self.UNIT_FWS_FLOW_RATE = 28
        
        return

    def onStart(self):
        Domoticz.Log("Hargassner Nano PK plugin started (v1.4.0 - Running mode corrected!)")
        
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        
        self.deviceName = "Hargassner"
        self.language = Parameters["Mode3"]
        
        try:
            self.pollInterval = int(Parameters["Mode4"])
        except:
            self.pollInterval = 5
        
        Domoticz.Heartbeat(10)
        self.createDevices()
        
        Domoticz.Log(f"Connecting to {Parameters['Address']}:{Parameters['Port']}")
        self.connection = Domoticz.Connection(
            Name="Telnet", 
            Transport="TCP/IP", 
            Protocol="None", 
            Address=Parameters["Address"], 
            Port=Parameters["Port"]
        )
        self.connection.Connect()

    def onStop(self):
        Domoticz.Log("Hargassner Nano PK plugin stopped")

    def onConnect(self, Connection, Status, Description):
        if Status == 0:
            Domoticz.Log("Connected successfully")
            self.connectionOK = True
            self.updateDevice(self.UNIT_CONNECTION, 0, "Connected")
        else:
            Domoticz.Error(f"Failed to connect ({Status}): {Description}")
            self.connectionOK = False
            self.updateDevice(self.UNIT_CONNECTION, 0, "Disconnected")

    def onMessage(self, Connection, Data):
        try:
            strData = Data.decode('utf-8', 'ignore').strip()
            lines = strData.split('\n')
            
            for line in reversed(lines):
                parts = line.split()
                if len(parts) < 50 or parts[0] != "pm":
                    continue
                
                values = parts[1:]
                
                try:
                    # ========================================
                    # VOLLSTÄNDIGE ZUORDNUNG v1.4.0
                    # Korrigiert nach Running-Mode-Test 19:50
                    # ========================================
                    
                    # Basis-Parameter
                    self.lastData['ZK'] = values[0] if len(values) > 0 else None               # Kesselzustand (7 = Leistungsbrand)
                    self.lastData['O2_Ist'] = values[1] if len(values) > 1 else None           # O2 Ist: 8.3%
                    self.lastData['O2_Soll'] = values[2] if len(values) > 2 else None          # O2 Soll: 7.7%
                    self.lastData['TK'] = values[3] if len(values) > 3 else None               # Kessel Temp Ist: 67.2°C
                    self.lastData['TK_Soll'] = values[4] if len(values) > 4 else None          # Kessel Temp Soll: 70°C
                    
                    # ✅ KORREKTUR 1: Rücklauf Ist war Index 14 → jetzt Index 5
                    self.lastData['TRL'] = values[5] if len(values) > 5 else None              # Rücklauf Ist: 63.8°C (war TRG)
                    
                    self.lastData['SZ_Ist'] = values[6] if len(values) > 6 else None           # Saugzug/Draft Ist: 64
                    self.lastData['SZ_Soll'] = values[7] if len(values) > 7 else None          # Saugzug/Draft Soll: 7
                    
                    # ✅ KORREKTUR 2: Rauchgas war Index 5 → jetzt Index 8
                    self.lastData['TRG'] = values[8] if len(values) > 8 else None              # Rauchgastemperatur: 143.0°C (war Leistung)
                    
                    # ✅ KORREKTUR 3: Puffer Mitte → Index 11 (für Unit 26)
                    self.lastData['TPm'] = values[11] if len(values) > 11 else None            # Puffer Mitte: 52.7°C (war Index 22)
                    
                    # ✅ FEST: Index 13 (Puffer unten) - NICHT ÄNDERN!
                    self.lastData['TPu'] = values[13] if len(values) > 13 else None            # Puffer unten: 43.9°C ✅ FEST
                    
                    # ✅ FEST: Index 19 (Puffer oben) - NICHT ÄNDERN!
                    self.lastData['TPo'] = values[19] if len(values) > 19 else None            # Puffer oben: 70°C ✅ FEST (zeigt nicht 58.1°C!)
                    
                    # ✅ KORREKTUR 4: Leistung war Index 8 → jetzt Index 24
                    self.lastData['Leistung'] = values[24] if len(values) > 24 else None       # Leistung: 85% (war TRL_Soll)
                    
                    # Rücklauf Soll - bleibt bei Index 24? Oder anderen Wert?
                    # Da Leistung jetzt bei 24 ist, brauchen wir neuen Index für TRL_Soll
                    # Index 6 zeigt 64 → das passt zu "Rücklauf Soll: 64°C"!
                    self.lastData['TRL_Soll'] = values[6] if len(values) > 6 else None         # Rücklauf Soll: 64°C (neu!)
                    
                    # Puffer & Pellets
                    self.lastData['Puff_Fuellgrad'] = values[14] if len(values) > 14 else None # Füllgrad /100
                    self.lastData['Lagerstand'] = values[46] if len(values) > 46 else None     # Pellets Lagerstand
                    
                    # Pellet Consumption durch 10 teilen
                    if len(values) > 47:
                        try:
                            raw_consumption = float(values[47])
                            self.lastData['Verbrauch'] = raw_consumption / 10.0
                        except:
                            self.lastData['Verbrauch'] = None
                    else:
                        self.lastData['Verbrauch'] = None
                    
                    self.lastData['Stoerung_Nr'] = values[49] if len(values) > 49 else None    # Störungsnummer
                    
                    # ✅ FEST: Index 54 (Außentemperatur) - NICHT ÄNDERN!
                    self.lastData['Taus'] = values[54] if len(values) > 54 else None           # Außentemperatur: 10.1°C ✅ FEST
                    
                    self.lastData['TVL_1'] = values[64] if len(values) > 64 else None          # Vorlauf HK1: 34.9°C
                    
                    # FWS (Frischwasserstation)
                    self.lastData['FWS_Vorlauf'] = values[110] if len(values) > 110 else None  # FWS Vorlauf: 58.5°C
                    self.lastData['FWS_Fuehler'] = values[111] if len(values) > 111 else None  # FWS Fühler: 58.5°C
                    self.lastData['FWS_Soll'] = values[112] if len(values) > 112 else None     # FWS Auslauftemp Soll: 50°C
                    self.lastData['FWS_Gesamtverbrauch'] = values[117] if len(values) > 117 else None  # FWS Gesamtverbrauch: 16293l
                    
                    # Digitale Werte (Störung)
                    digital_offset = 126
                    if len(values) > digital_offset:
                        try:
                            digital_0 = int(values[digital_offset], 16)
                            self.lastData['Stoerung'] = 'True' if (digital_0 & (1 << 13)) else 'False'
                        except:
                            self.lastData['Stoerung'] = 'False'
                    else:
                        self.lastData['Stoerung'] = 'False'
                    
                    # Debug-Ausgabe
                    if Parameters["Mode6"] == "Debug":
                        Domoticz.Debug("=== EXTRACTED VALUES v1.4.0 (CORRECTED) ===")
                        Domoticz.Debug(f"Boiler Temp: {self.lastData.get('TK')}°C")
                        Domoticz.Debug(f"Smoke Gas (Index 8): {self.lastData.get('TRG')}°C")
                        Domoticz.Debug(f"Output (Index 24): {self.lastData.get('Leistung')}%")
                        Domoticz.Debug(f"Return Temp Ist (Index 5): {self.lastData.get('TRL')}°C")
                        Domoticz.Debug(f"Return Temp Soll (Index 6): {self.lastData.get('TRL_Soll')}°C")
                        Domoticz.Debug(f"Buffer Top (Index 19 FIXED): {self.lastData.get('TPo')}°C")
                        Domoticz.Debug(f"Buffer Center (Index 11 NEW): {self.lastData.get('TPm')}°C")
                        Domoticz.Debug(f"Buffer Bottom (Index 13 FIXED): {self.lastData.get('TPu')}°C")
                        Domoticz.Debug(f"Outside Temp (Index 54 FIXED): {self.lastData.get('Taus')}°C")
                        Domoticz.Debug(f"Pellet Consumption: {self.lastData.get('Verbrauch')} kg")
                    
                    self.updateAllDevices()
                    self.missedMsgs = 0
                    break
                    
                except Exception as e:
                    Domoticz.Error(f"Error parsing: {str(e)}")
                    import traceback
                    Domoticz.Error(traceback.format_exc())
                    continue
            
        except Exception as e:
            Domoticz.Error(f"Error processing message: {str(e)}")

    def onCommand(self, Unit, Command, Level, Hue):
        pass

    def onDisconnect(self, Connection):
        Domoticz.Log("Disconnected")
        self.connectionOK = False
        self.updateDevice(self.UNIT_CONNECTION, 0, "Disconnected")

    def onHeartbeat(self):
        self.runCounter += 1
        if not self.connectionOK and self.connection:
            if self.runCounter % 30 == 0:
                self.connection.Connect()

    def createDevices(self):
        """Erstellt alle Devices"""
        
        # Standard Devices
        if self.UNIT_CONNECTION not in Devices:
            Domoticz.Device(Name=self.deviceName + " Connection", Unit=self.UNIT_CONNECTION, TypeName="Text").Create()
        if self.UNIT_BOILER_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Boiler Temperature", Unit=self.UNIT_BOILER_TEMP, TypeName="Temperature").Create()
        if self.UNIT_BOILER_STATE not in Devices:
            Domoticz.Device(Name=self.deviceName + " Boiler State", Unit=self.UNIT_BOILER_STATE, TypeName="Text").Create()
        if self.UNIT_ERROR not in Devices:
            Domoticz.Device(Name=self.deviceName + " Operation", Unit=self.UNIT_ERROR, TypeName="Text").Create()
        if self.UNIT_OUTPUT not in Devices:
            Domoticz.Device(Name=self.deviceName + " Output", Unit=self.UNIT_OUTPUT, TypeName="Percentage").Create()
        if self.UNIT_SMOKE_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Smoke Gas Temperature", Unit=self.UNIT_SMOKE_TEMP, TypeName="Temperature").Create()
        if self.UNIT_OUTSIDE_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Outside Temperature", Unit=self.UNIT_OUTSIDE_TEMP, TypeName="Temperature").Create()
        if self.UNIT_BUFFER_TOP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Top", Unit=self.UNIT_BUFFER_TOP, TypeName="Temperature").Create()
        if self.UNIT_BUFFER_CENTER not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Center", Unit=self.UNIT_BUFFER_CENTER, TypeName="Temperature").Create()
        if self.UNIT_BUFFER_BOTTOM not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Bottom", Unit=self.UNIT_BUFFER_BOTTOM, TypeName="Temperature").Create()
        if self.UNIT_BUFFER_LEVEL not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Level", Unit=self.UNIT_BUFFER_LEVEL, TypeName="Percentage").Create()
        if self.UNIT_RETURN_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Return Temperature", Unit=self.UNIT_RETURN_TEMP, TypeName="Temperature").Create()
        if self.UNIT_PELLET_STOCK not in Devices:
            Domoticz.Device(Name=self.deviceName + " Pellet Stock", Unit=self.UNIT_PELLET_STOCK, TypeName="Custom", Options={"Custom": "1;kg"}).Create()
        if self.UNIT_PELLET_CONSUMPTION not in Devices:
            Domoticz.Device(Name=self.deviceName + " Pellet Consumption", Unit=self.UNIT_PELLET_CONSUMPTION, TypeName="Custom", Options={"Custom": "0.1;kg"}).Create()
        if self.UNIT_FLOW_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Flow Temperature", Unit=self.UNIT_FLOW_TEMP, TypeName="Temperature").Create()
        if self.UNIT_ENERGY not in Devices:
            Domoticz.Device(Name=self.deviceName + " Energy", Unit=self.UNIT_ENERGY, TypeName="Custom", Options={"Custom": "1;kWh"}).Create()
        
        # FULL Mode - Erweiterte Sensoren
        if Parameters["Mode2"] == "FULL":
            if self.UNIT_BOILER_TEMP_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " Boiler Temperature Target", Unit=self.UNIT_BOILER_TEMP_TARGET, TypeName="Temperature").Create()
            if self.UNIT_O2_ACTUAL not in Devices:
                Domoticz.Device(Name=self.deviceName + " O2 Actual", Unit=self.UNIT_O2_ACTUAL, TypeName="Percentage").Create()
            if self.UNIT_O2_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " O2 Target", Unit=self.UNIT_O2_TARGET, TypeName="Percentage").Create()
            if self.UNIT_DRAFT_ACTUAL not in Devices:
                Domoticz.Device(Name=self.deviceName + " Draft Actual", Unit=self.UNIT_DRAFT_ACTUAL, TypeName="Custom", Options={"Custom": "1;Pa"}).Create()
            if self.UNIT_DRAFT_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " Draft Target", Unit=self.UNIT_DRAFT_TARGET, TypeName="Custom", Options={"Custom": "1;Pa"}).Create()
            if self.UNIT_RETURN_TEMP_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " Return Temperature Target", Unit=self.UNIT_RETURN_TEMP_TARGET, TypeName="Temperature").Create()
            
            # FWS Devices
            if self.UNIT_FWS_FLOW_TEMP not in Devices:
                Domoticz.Device(Name=self.deviceName + " FWS Flow Temperature", Unit=self.UNIT_FWS_FLOW_TEMP, TypeName="Temperature").Create()
            if self.UNIT_FWS_SENSOR not in Devices:
                Domoticz.Device(Name=self.deviceName + " FWS Sensor", Unit=self.UNIT_FWS_SENSOR, TypeName="Temperature").Create()
            if self.UNIT_FWS_OUTLET_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " FWS Outlet Target", Unit=self.UNIT_FWS_OUTLET_TARGET, TypeName="Temperature").Create()
            if self.UNIT_FWS_WATER_TOTAL not in Devices:
                Domoticz.Device(Name=self.deviceName + " FWS Water Total", Unit=self.UNIT_FWS_WATER_TOTAL, TypeName="Custom", Options={"Custom": "1;l"}).Create()

    def updateAllDevices(self):
        """Aktualisiert alle Devices"""
        
        # Kesseltemperatur
        if 'TK' in self.lastData and self.lastData['TK']:
            self.updateDevice(self.UNIT_BOILER_TEMP, 0, self.lastData['TK'])
        
        # Kesselzustand (Unit 3 - NICHT ÄNDERN per Vorgabe)
        if 'ZK' in self.lastData and self.lastData['ZK']:
            try:
                idx = int(self.lastData['ZK'])
                if 0 <= idx <= 12:
                    states = BOILER_STATES_DE if self.language == "DE" else BOILER_STATES_EN
                    self.updateDevice(self.UNIT_BOILER_STATE, 0, states[idx])
            except:
                pass
        
        # Fehlerstatus
        if 'Stoerung' in self.lastData:
            if self.lastData['Stoerung'] == 'False':
                self.updateDevice(self.UNIT_ERROR, 0, "OK")
            else:
                errorCode = self.lastData.get('Stoerung_Nr', '')
                errorText = ERROR_CODES.get(errorCode, f"Error {errorCode}")
                self.updateDevice(self.UNIT_ERROR, 0, errorText)
        
        # ✅ Leistung (Unit 5) - jetzt Index 24
        if 'Leistung' in self.lastData and self.lastData['Leistung']:
            self.updateDevice(self.UNIT_OUTPUT, 0, self.lastData['Leistung'])
        
        # ✅ Rauchgastemperatur (Unit 6) - jetzt Index 8
        if 'TRG' in self.lastData and self.lastData['TRG']:
            self.updateDevice(self.UNIT_SMOKE_TEMP, 0, self.lastData['TRG'])
        
        # Außentemperatur (FEST: Index 54)
        if 'Taus' in self.lastData and self.lastData['Taus']:
            self.updateDevice(self.UNIT_OUTSIDE_TEMP, 0, self.lastData['Taus'])
        
        # Puffer Oben (FEST: Index 19)
        if 'TPo' in self.lastData and self.lastData['TPo']:
            self.updateDevice(self.UNIT_BUFFER_TOP, 0, self.lastData['TPo'])
        
        # ✅ Puffer Mitte (Unit 9) - jetzt Index 11
        if 'TPm' in self.lastData and self.lastData['TPm']:
            self.updateDevice(self.UNIT_BUFFER_CENTER, 0, self.lastData['TPm'])
        
        # Puffer Unten (FEST: Index 13)
        if 'TPu' in self.lastData and self.lastData['TPu']:
            self.updateDevice(self.UNIT_BUFFER_BOTTOM, 0, self.lastData['TPu'])
        
        # Pufferfüllgrad
        if 'Puff_Fuellgrad' in self.lastData and self.lastData['Puff_Fuellgrad']:              
                self.updateDevice(self.UNIT_BUFFER_LEVEL, 0, self.lastData['Puff_Fuellgrad'])
           
        
        # ✅ Rücklauf Ist (Unit 12) - jetzt Index 5
        if 'TRL' in self.lastData and self.lastData['TRL']:
            self.updateDevice(self.UNIT_RETURN_TEMP, 0, self.lastData['TRL'])
        
        # Pellets
        if 'Lagerstand' in self.lastData and self.lastData['Lagerstand']:
            self.updateDevice(self.UNIT_PELLET_STOCK, 0, self.lastData['Lagerstand'])
        
        # Pellet Consumption (korrigiert /10)
        if 'Verbrauch' in self.lastData and self.lastData['Verbrauch']:
            self.updateDevice(self.UNIT_PELLET_CONSUMPTION, 0, f"{self.lastData['Verbrauch']:.1f}")
            
            # Energie berechnen
            try:
                energy = float(self.lastData['Verbrauch']) * 4.8
                self.updateDevice(self.UNIT_ENERGY, 0, f"{energy:.1f}")
            except:
                pass
        
        # Vorlauf
        if 'TVL_1' in self.lastData and self.lastData['TVL_1']:
            self.updateDevice(self.UNIT_FLOW_TEMP, 0, self.lastData['TVL_1'])
        
        # FULL Mode Updates
        if Parameters["Mode2"] == "FULL":
            if 'TK_Soll' in self.lastData and self.lastData['TK_Soll']:
                self.updateDevice(self.UNIT_BOILER_TEMP_TARGET, 0, self.lastData['TK_Soll'])
            if 'O2_Ist' in self.lastData and self.lastData['O2_Ist']:
                self.updateDevice(self.UNIT_O2_ACTUAL, 0, self.lastData['O2_Ist'])
            if 'O2_Soll' in self.lastData and self.lastData['O2_Soll']:
                self.updateDevice(self.UNIT_O2_TARGET, 0, self.lastData['O2_Soll'])
            if 'SZ_Ist' in self.lastData and self.lastData['SZ_Ist']:
                self.updateDevice(self.UNIT_DRAFT_ACTUAL, 0, self.lastData['SZ_Ist'])
            if 'SZ_Soll' in self.lastData and self.lastData['SZ_Soll']:
                self.updateDevice(self.UNIT_DRAFT_TARGET, 0, self.lastData['SZ_Soll'])
            
            # ✅ Rücklauf Soll - jetzt Index 6
            if 'TRL_Soll' in self.lastData and self.lastData['TRL_Soll']:
                self.updateDevice(self.UNIT_RETURN_TEMP_TARGET, 0, self.lastData['TRL_Soll'])
            
            # FWS Updates
            if 'FWS_Vorlauf' in self.lastData and self.lastData['FWS_Vorlauf']:
                self.updateDevice(self.UNIT_FWS_FLOW_TEMP, 0, self.lastData['FWS_Vorlauf'])
            if 'FWS_Fuehler' in self.lastData and self.lastData['FWS_Fuehler']:
                self.updateDevice(self.UNIT_FWS_SENSOR, 0, self.lastData['FWS_Fuehler'])
            if 'FWS_Soll' in self.lastData and self.lastData['FWS_Soll']:
                self.updateDevice(self.UNIT_FWS_OUTLET_TARGET, 0, self.lastData['FWS_Soll'])
            if 'FWS_Gesamtverbrauch' in self.lastData and self.lastData['FWS_Gesamtverbrauch']:
                self.updateDevice(self.UNIT_FWS_WATER_TOTAL, 0, self.lastData['FWS_Gesamtverbrauch'])

    def updateDevice(self, unit, nValue, sValue):
        """Aktualisiert ein Device"""
        if unit not in Devices:
            return
        try:
            if Devices[unit].nValue != nValue or Devices[unit].sValue != str(sValue):
                Devices[unit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Debug(f"Updated Unit {unit}: {sValue}")
        except Exception as e:
            Domoticz.Error(f"Error updating {unit}: {str(e)}")


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
