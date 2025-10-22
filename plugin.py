"""
<plugin key="HargassnerNanoPK" name="Hargassner Nano PK" author="converted with Claude.ai from HA plugin" version="1.2.0">
    <description>
        <h2>Hargassner Nano PK Plugin</h2><br/>
        Connects to Hargassner heating via Telnet<br/>
        <br/>
        Note: The heating sends data every second via Telnet.<br/>
        The update interval controls how often Domoticz devices are updated.
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
        <param field="Mode4" label="Update Interval (seconds)" width="100px" required="true" default="30"/>
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
from datetime import datetime, timedelta

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
        self.pollInterval = 30  # Default 30 Sekunden
        self.connection = None
        self.connectionOK = False
        self.deviceName = "Hargassner"
        self.language = "EN"
        self.missedMsgs = 0
        self.lastData = {}
        self.lastUpdate = None  # NEU: Timestamp des letzten Updates
        
        # Device Units - Basis-Sensoren
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
        
        # Erweiterte Sensoren
        self.UNIT_BOILER_TEMP_TARGET = 17
        self.UNIT_O2_ACTUAL = 18
        self.UNIT_O2_TARGET = 19
        self.UNIT_DRAFT_ACTUAL = 20
        self.UNIT_DRAFT_TARGET = 21
        self.UNIT_RETURN_TEMP_TARGET = 22
        self.UNIT_ROOM_TEMP = 23
        self.UNIT_FWS_SENSOR = 24
        self.UNIT_FWS_FLOW = 25
        self.UNIT_SYSTEM_PRESSURE = 26
        
        return

    def onStart(self):
        Domoticz.Log("Hargassner Nano PK plugin started (v1.2.0)")
        
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            Domoticz.Debug("Debug mode enabled")
        
        self.deviceName = "Hargassner"
        self.language = Parameters["Mode3"]
        
        # Update Interval konfigurieren
        try:
            self.pollInterval = int(Parameters["Mode4"])
            if self.pollInterval < 5:
                Domoticz.Log("Update interval too short, setting to 5 seconds")
                self.pollInterval = 5
        except:
            self.pollInterval = 30
        
        Domoticz.Log(f"Update interval: {self.pollInterval} seconds")
        Domoticz.Log(f"Language: {self.language}")
        Domoticz.Log(f"Parameters mode: {Parameters['Mode2']}")
        Domoticz.Log("Note: Heating sends data every ~1 second, plugin throttles updates")
        
        Domoticz.Heartbeat(10)
        
        # Devices erstellen
        self.createDevices()
        
        # Telnet-Verbindung
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
            Domoticz.Log("Connected successfully to " + Parameters["Address"])
            self.connectionOK = True
            self.updateDevice(self.UNIT_CONNECTION, 0, "Connected")
        else:
            Domoticz.Error(f"Failed to connect ({Status}): {Description}")
            self.connectionOK = False
            self.updateDevice(self.UNIT_CONNECTION, 0, "Disconnected")

    def onMessage(self, Connection, Data):
        try:
            strData = Data.decode('utf-8', 'ignore').strip()
            Domoticz.Debug(f"Received {len(strData)} bytes")
            
            lines = strData.split('\n')
            
            for line in reversed(lines):
                parts = line.split()
                if len(parts) < 50:
                    continue
                
                if parts[0] != "pm":
                    continue
                
                values = parts[1:]
                Domoticz.Debug(f"Received message with {len(values)} values")
                
                try:
                    # Daten extrahieren (in self.lastData speichern)
                    self.lastData['ZK'] = values[0] if len(values) > 0 else None
                    self.lastData['O2_Ist'] = values[1] if len(values) > 1 else None
                    self.lastData['O2_Soll'] = values[2] if len(values) > 2 else None
                    self.lastData['TK'] = values[3] if len(values) > 3 else None
                    self.lastData['TK_Soll'] = values[4] if len(values) > 4 else None
                    self.lastData['TRG'] = values[5] if len(values) > 5 else None
                    self.lastData['SZ_Ist'] = values[6] if len(values) > 6 else None
                    self.lastData['SZ_Soll'] = values[7] if len(values) > 7 else None
                    self.lastData['Leistung'] = values[8] if len(values) > 8 else None
                    self.lastData['TPu'] = values[13] if len(values) > 13 else None
                    self.lastData['TPo'] = values[19] if len(values) > 19 else None
                    self.lastData['TPm'] = values[22] if len(values) > 22 else None
                    self.lastData['TRL'] = values[23] if len(values) > 23 else None
                    self.lastData['TRL_Soll'] = values[24] if len(values) > 24 else None
                    self.lastData['Puff_Fuellgrad'] = values[42] if len(values) > 42 else None
                    self.lastData['Lagerstand'] = values[46] if len(values) > 46 else None
                    self.lastData['Verbrauch'] = values[47] if len(values) > 47 else None
                    self.lastData['Stoerung_Nr'] = values[49] if len(values) > 49 else None
                    self.lastData['Raumtemp'] = values[50] if len(values) > 50 else None
                    self.lastData['Taus'] = values[54] if len(values) > 54 else None
                    self.lastData['FWS_Fuehler'] = values[55] if len(values) > 55 else None
                    self.lastData['TVL_1'] = values[64] if len(values) > 64 else None
                    
                    if len(values) > 110:
                        self.lastData['FWS_Vorlauf'] = values[110] if len(values) > 110 else None
                    
                    # Digitale Werte
                    digital_offset = 126
                    if len(values) > digital_offset:
                        try:
                            digital_0 = int(values[digital_offset], 16)
                            self.lastData['Stoerung'] = 'True' if (digital_0 & (1 << 13)) else 'False'
                        except:
                            self.lastData['Stoerung'] = 'False'
                    else:
                        self.lastData['Stoerung'] = 'False'
                    
                    # WICHTIG: Nur aktualisieren wenn Update-Intervall abgelaufen ist!
                    now = datetime.now()
                    if self.lastUpdate is None or (now - self.lastUpdate).total_seconds() >= self.pollInterval:
                        Domoticz.Debug(f"Update interval reached ({self.pollInterval}s), updating devices...")
                        self.updateAllDevices()
                        self.lastUpdate = now
                        self.missedMsgs = 0
                    else:
                        elapsed = (now - self.lastUpdate).total_seconds()
                        remaining = self.pollInterval - elapsed
                        Domoticz.Debug(f"Skipping update, {remaining:.1f}s remaining until next update")
                    
                    break
                    
                except Exception as e:
                    Domoticz.Error(f"Error parsing values: {str(e)}")
                    import traceback
                    Domoticz.Error(traceback.format_exc())
                    continue
            
        except Exception as e:
            Domoticz.Error(f"Error processing message: {str(e)}")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(f"onCommand: Unit={Unit}, Command={Command}, Level={Level}")

    def onDisconnect(self, Connection):
        Domoticz.Log("Disconnected from heating system")
        self.connectionOK = False
        self.updateDevice(self.UNIT_CONNECTION, 0, "Disconnected")

    def onHeartbeat(self):
        self.runCounter += 1
        
        # Reconnect wenn nicht verbunden
        if not self.connectionOK and self.connection:
            if self.runCounter % 30 == 0:
                Domoticz.Log("Attempting to reconnect...")
                self.connection.Connect()

    def createDevices(self):
        """Erstellt alle Devices"""
        Domoticz.Log("Creating devices...")
        
        # Basis-Devices
        if self.UNIT_CONNECTION not in Devices:
            Domoticz.Device(Name=self.deviceName + " Connection", 
                          Unit=self.UNIT_CONNECTION, TypeName="Text").Create()
        
        if self.UNIT_BOILER_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Boiler Temperature", 
                          Unit=self.UNIT_BOILER_TEMP, TypeName="Temperature").Create()
        
        if self.UNIT_BOILER_STATE not in Devices:
            Domoticz.Device(Name=self.deviceName + " Boiler State", 
                          Unit=self.UNIT_BOILER_STATE, TypeName="Text").Create()
        
        if self.UNIT_ERROR not in Devices:
            Domoticz.Device(Name=self.deviceName + " Operation", 
                          Unit=self.UNIT_ERROR, TypeName="Text").Create()
        
        if self.UNIT_OUTPUT not in Devices:
            Domoticz.Device(Name=self.deviceName + " Output", 
                          Unit=self.UNIT_OUTPUT, TypeName="Percentage").Create()
        
        if self.UNIT_SMOKE_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Smoke Gas Temperature", 
                          Unit=self.UNIT_SMOKE_TEMP, TypeName="Temperature").Create()
        
        if self.UNIT_OUTSIDE_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Outside Temperature", 
                          Unit=self.UNIT_OUTSIDE_TEMP, TypeName="Temperature").Create()
        
        if self.UNIT_BUFFER_TOP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Top", 
                          Unit=self.UNIT_BUFFER_TOP, TypeName="Temperature").Create()
        
        if self.UNIT_BUFFER_CENTER not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Center", 
                          Unit=self.UNIT_BUFFER_CENTER, TypeName="Temperature").Create()
        
        if self.UNIT_BUFFER_BOTTOM not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Bottom", 
                          Unit=self.UNIT_BUFFER_BOTTOM, TypeName="Temperature").Create()
        
        if self.UNIT_BUFFER_LEVEL not in Devices:
            Domoticz.Device(Name=self.deviceName + " Buffer Level", 
                          Unit=self.UNIT_BUFFER_LEVEL, TypeName="Percentage").Create()
        
        if self.UNIT_RETURN_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Return Temperature", 
                          Unit=self.UNIT_RETURN_TEMP, TypeName="Temperature").Create()
        
        if self.UNIT_PELLET_STOCK not in Devices:
            Domoticz.Device(Name=self.deviceName + " Pellet Stock", 
                          Unit=self.UNIT_PELLET_STOCK, TypeName="Custom",
                          Options={"Custom": "1;kg"}).Create()
        
        if self.UNIT_PELLET_CONSUMPTION not in Devices:
            Domoticz.Device(Name=self.deviceName + " Pellet Consumption", 
                          Unit=self.UNIT_PELLET_CONSUMPTION, TypeName="Custom",
                          Options={"Custom": "1;kg"}).Create()
        
        if self.UNIT_FLOW_TEMP not in Devices:
            Domoticz.Device(Name=self.deviceName + " Flow Temperature", 
                          Unit=self.UNIT_FLOW_TEMP, TypeName="Temperature").Create()
        
        if self.UNIT_ENERGY not in Devices:
            Domoticz.Device(Name=self.deviceName + " Energy", 
                          Unit=self.UNIT_ENERGY, TypeName="Custom",
                          Options={"Custom": "1;kWh"}).Create()
        
        # Erweiterte Devices (nur bei FULL mode)
        if Parameters["Mode2"] == "FULL":
            if self.UNIT_BOILER_TEMP_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " Boiler Temperature Target", 
                              Unit=self.UNIT_BOILER_TEMP_TARGET, TypeName="Temperature").Create()
            
            if self.UNIT_O2_ACTUAL not in Devices:
                Domoticz.Device(Name=self.deviceName + " O2 Actual", 
                              Unit=self.UNIT_O2_ACTUAL, TypeName="Percentage").Create()
            
            if self.UNIT_O2_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " O2 Target", 
                              Unit=self.UNIT_O2_TARGET, TypeName="Percentage").Create()
            
            if self.UNIT_DRAFT_ACTUAL not in Devices:
                Domoticz.Device(Name=self.deviceName + " Draft Actual", 
                              Unit=self.UNIT_DRAFT_ACTUAL, TypeName="Percentage").Create()
            
            if self.UNIT_DRAFT_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " Draft Target", 
                              Unit=self.UNIT_DRAFT_TARGET, TypeName="Percentage").Create()
            
            if self.UNIT_RETURN_TEMP_TARGET not in Devices:
                Domoticz.Device(Name=self.deviceName + " Return Temperature Target", 
                              Unit=self.UNIT_RETURN_TEMP_TARGET, TypeName="Temperature").Create()
            
            if self.UNIT_ROOM_TEMP not in Devices:
                Domoticz.Device(Name=self.deviceName + " Room Temperature", 
                              Unit=self.UNIT_ROOM_TEMP, TypeName="Temperature").Create()
            
            if self.UNIT_FWS_SENSOR not in Devices:
                Domoticz.Device(Name=self.deviceName + " FWS Sensor", 
                              Unit=self.UNIT_FWS_SENSOR, TypeName="Temperature").Create()
            
            if self.UNIT_FWS_FLOW not in Devices:
                Domoticz.Device(Name=self.deviceName + " FWS Flow", 
                              Unit=self.UNIT_FWS_FLOW, TypeName="Temperature").Create()
            
            if self.UNIT_SYSTEM_PRESSURE not in Devices:
                Domoticz.Device(Name=self.deviceName + " System Pressure", 
                              Unit=self.UNIT_SYSTEM_PRESSURE, TypeName="Custom",
                              Options={"Custom": "1;bar"}).Create()
        
        Domoticz.Log(f"Created/Found {len(Devices)} devices")

    def updateAllDevices(self):
        """Aktualisiert alle Devices"""
        
        Domoticz.Log("Updating all devices...")
        
        # Kesseltemperatur
        if 'TK' in self.lastData and self.lastData['TK']:
            self.updateDevice(self.UNIT_BOILER_TEMP, 0, self.lastData['TK'])
        
        # Kesselzustand
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
        
        # Leistung
        if 'Leistung' in self.lastData and self.lastData['Leistung']:
            self.updateDevice(self.UNIT_OUTPUT, 0, self.lastData['Leistung'])
        
        # Rauchgastemperatur
        if 'TRG' in self.lastData and self.lastData['TRG']:
            self.updateDevice(self.UNIT_SMOKE_TEMP, 0, self.lastData['TRG'])
        
        # Außentemperatur
        if 'Taus' in self.lastData and self.lastData['Taus']:
            self.updateDevice(self.UNIT_OUTSIDE_TEMP, 0, self.lastData['Taus'])
        
        # Puffer
        if 'TPo' in self.lastData and self.lastData['TPo']:
            self.updateDevice(self.UNIT_BUFFER_TOP, 0, self.lastData['TPo'])
        
        if 'TPm' in self.lastData and self.lastData['TPm']:
            self.updateDevice(self.UNIT_BUFFER_CENTER, 0, self.lastData['TPm'])
        
        if 'TPu' in self.lastData and self.lastData['TPu']:
            self.updateDevice(self.UNIT_BUFFER_BOTTOM, 0, self.lastData['TPu'])
        
        # Pufferfüllgrad (durch 100 teilen!)
        if 'Puff_Fuellgrad' in self.lastData and self.lastData['Puff_Fuellgrad']:
            try:
                level = float(self.lastData['Puff_Fuellgrad']) / 100.0
                self.updateDevice(self.UNIT_BUFFER_LEVEL, 0, f"{level:.0f}")
            except:
                self.updateDevice(self.UNIT_BUFFER_LEVEL, 0, self.lastData['Puff_Fuellgrad'])
        
        # Rücklauf
        if 'TRL' in self.lastData and self.lastData['TRL']:
            self.updateDevice(self.UNIT_RETURN_TEMP, 0, self.lastData['TRL'])
        
        # Pellets
        if 'Lagerstand' in self.lastData and self.lastData['Lagerstand']:
            self.updateDevice(self.UNIT_PELLET_STOCK, 0, self.lastData['Lagerstand'])
        
        if 'Verbrauch' in self.lastData and self.lastData['Verbrauch']:
            self.updateDevice(self.UNIT_PELLET_CONSUMPTION, 0, self.lastData['Verbrauch'])
            
            # Energie berechnen
            try:
                energy = float(self.lastData['Verbrauch']) * 4.8
                self.updateDevice(self.UNIT_ENERGY, 0, f"{energy:.1f}")
            except:
                pass
        
        # Vorlauf
        if 'TVL_1' in self.lastData and self.lastData['TVL_1']:
            self.updateDevice(self.UNIT_FLOW_TEMP, 0, self.lastData['TVL_1'])
        
        # Erweiterte Werte (nur bei FULL mode)
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
            
            if 'TRL_Soll' in self.lastData and self.lastData['TRL_Soll']:
                self.updateDevice(self.UNIT_RETURN_TEMP_TARGET, 0, self.lastData['TRL_Soll'])
            
            if 'Raumtemp' in self.lastData and self.lastData['Raumtemp']:
                self.updateDevice(self.UNIT_ROOM_TEMP, 0, self.lastData['Raumtemp'])
            
            if 'FWS_Fuehler' in self.lastData and self.lastData['FWS_Fuehler']:
                self.updateDevice(self.UNIT_FWS_SENSOR, 0, self.lastData['FWS_Fuehler'])
            
            if 'FWS_Vorlauf' in self.lastData and self.lastData['FWS_Vorlauf']:
                self.updateDevice(self.UNIT_FWS_FLOW, 0, self.lastData['FWS_Vorlauf'])

    def updateDevice(self, unit, nValue, sValue):
        """Aktualisiert ein Device"""
        if unit not in Devices:
            return
        
        try:
            if Devices[unit].nValue != nValue or Devices[unit].sValue != str(sValue):
                Devices[unit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Debug(f"Updated Unit {unit}: {sValue}")
        except Exception as e:
            Domoticz.Error(f"Error updating device {unit}: {str(e)}")


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
