[English](README.en_US.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

![PalworldSaveTools Logo](Assets/resources/PalworldSaveTools_Black.png)
---
- **Kontakt über Discord:** Pylar1991
---
---
- **Bitte lade den Standalone-Ordner von [https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest), um die .exe nutzen zu können!**
---

## Funktionen

- **Schnelles Parsing/Lesen** – eines der schnellsten verfügbaren Tools.  
- Listet alle Spieler/Gilden auf.  
- Listet alle Pals und deren Details auf.  
- Zeigt die letzte Online-Zeit der Spieler an.  
- Protokolliert Spieler und deren Daten in `players.log`.  
- Protokolliert und sortiert Spieler nach der Anzahl ihrer besessenen Pals.  
- Bietet eine **Basiskartenansicht**.  
- Erstellt automatische `killnearestbase`-Befehle für PalDefender, um inaktive Basen zu entfernen.  
- Überträgt Spielstände zwischen Dedicated Servern und Einzel-/Koop-Welten.  
- Repariert Host-Spielstände durch GUID-Bearbeitung.  
- Enthält Steam-ID-Konvertierung.  
- Enthält Koordinatenkonvertierung.  
- Enthält GamePass ⇔ Steam-Konvertierung.  
- Slot-Injektor zur Erhöhung der Pal-Slots pro Spieler, kompatibel mit Bigger PalBox Mod.  
- Automatisches Backup bei jeder Tool-Nutzung.  
- **All in One Tools** (ehemals All in One Deletion Tool):
  - Spieler löschen  
  - Basen löschen  
  - Gilden löschen  
  - **Alle Gilden neu aufbauen**  
    - Weist jeden Pal der korrekten Gilde zu  
    - Repariert Gruppen-IDs  
    - Entfernt Expeditionsmarkierungen  
    - Setzt Arbeitseignung zurück  
    - Baut Gilden-Handles ohne Duplikate wieder auf  
  - Anti-Air-Geschütze zurücksetzen  
  - Nicht referenzierte Daten löschen  
  - Missionen zurücksetzen  
  - Private Truhen entsperren  
  - Ungültige/modifizierte Items / Pals entfernen 
  - Ausschlusssystem für geschützte Spieler/Gilden/Basen  
  - Spieler zwischen Gilden verschieben  
  - Spieler zum Gildenleiter machen  
  - Andere Tools im Datei-Menü zusammengeführt  

## 🗺️ Schritte zum Entsperren der Karte

> **Hinweis:** Gilt nur, wenn du **nicht** die "Restore Map"-Option nutzen willst.
> ⚠️ Überschreibt deinen aktuellen Kartenfortschritt mit der vollständig entsperrten Karte aus PST.

### 1️⃣ Kopiere die entsperrte Karte
Kopiere die Datei `LocalData.sav` aus `Assets\resources\LocalData.sav`.

### 2️⃣ Finde die ID deines neuen Servers/Welt
- **Tritt deinem neuen Server/Welt bei**.  
- Öffne den Explorer und füge ein:

%localappdata%\Pal\Saved\SaveGames\

- Suche nach einem Ordner mit einer **zufälligen ID** — das ist deine **Steam-ID**.  
- Öffne den Ordner und sortiere die Unterordner nach **"Zuletzt geändert"**.  
- Finde den Ordner, der zu deinem **neuen Server/Welt-ID** passt.

### 3️⃣ Ersetze die Karten-Datei
- Füge die kopierte `LocalData.sav` in diesen **neuen Server/Welt-Ordner** ein.  
- Bestätige ggf. die Überschreibung der vorhandenen Datei.

### 🎉 Fertig!
Starte deinen **neuen Server/Welt** — Nebel und Icons stimmen jetzt mit der entsperrten PST-Karte überein.

---

## 🔁 Von Host/Koop zu Server oder umgekehrt

Für **Host/Koop** befindet sich der Save-Ordner typischerweise unter:

%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\

Für **dedizierte Server**:

steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\

---

### 🧪 Transfer-Prozess

1. Kopiere **`Level.sav` und den `Players`-Ordner** aus dem Save-Ordner von **Host/Koop** oder **dediziertem Server**.  
2. Füge sie in den Save-Ordner der anderen Save-Art ein (Host ↔ Server).  
3. Starte das Spiel oder den Server.  
4. Erstelle bei Aufforderung einen **neuen Charakter**.  
5. Warte ~2 Minuten für die Auto-Sicherung, dann schließe Spiel/Server.  
6. Kopiere die aktualisierten **`Level.sav` und `Players`** aus dieser Welt.  
7. Füge sie in einen **temporären Ordner** auf deinem PC ein.  
8. Öffne **PST(PalworldSaveTools)** und wähle **Fix Host Save**.  
9. Wähle **`Level.sav`** aus dem temporären Ordner.  
10. Wähle:
    - **Alter Charakter** (aus dem ursprünglichen Save)  
    - **Neuer Charakter** (gerade erstellt)  
11. Klicke **Migrate**.  
12. Kopiere nach Abschluss der Migration die aktualisierten **`Level.sav` und `Players`** aus dem temporären Ordner.  
13. Füge sie in den tatsächlichen Save-Ordner ein (Host oder Server).  
14. Starte Spiel/Server und genieße deinen Charakter mit vollständigem Fortschritt!

---

# Host-Tausch in Palworld (UID Erklärung)

## Hintergrund
- **Host verwendet immer `0001.sav`** — gleiche UID für jeden Host.  
- Jeder Client hat einen eigenen **regulären UID-Save** (z.B. `123xxx.sav`, `987xxx.sav`).

## Voraussetzung
Beide Spieler (alter und neuer Host) **müssen reguläre Saves haben**.  
Erstellt automatisch ein neuer Charakter, wenn nicht vorhanden.

---

## Schritt-für-Schritt Host-Tausch

### 1. Sicherstellen, dass reguläre Saves existieren
- Spieler A (alter Host) hat regulären Save (`123xxx.sav`).  
- Spieler B (neuer Host) hat regulären Save (`987xxx.sav`).

### 2. Alten Host-Host-Save auf regulären Save übertragen
- Mit **Fix Host Save**:  
  `0001.sav` → `123xxx.sav`  
  (Überträgt Fortschritt des alten Hosts in regulären Slot)

### 3. Neuen Host-Save auf Host-Slot übertragen
- Mit **Fix Host Save**:  
  `987xxx.sav` → `0001.sav`  
  (Überträgt Fortschritt des neuen Hosts in Host-Slot)

---

## Ergebnis
- Spieler B ist nun Host, Charakter und Pals in `0001.sav`.  
- Spieler A wird Client, ursprünglicher Fortschritt in `123xxx.sav`.

---

## Zusammenfassung
- **Alter Host `0001.sav` → regulärer UID-Save**  
- **Neuer Host regulärer UID-Save → `0001.sav`**

---

# 🐞 Bekannte Fehler / Probleme

## 1. Steam ➝ GamePass Konverter funktioniert nicht
**Problem:** Änderungen werden nicht übernommen.  
**Lösung:**  
1. GamePass-Version schließen.  
2. Einige Minuten warten.  
3. Konverter ausführen.  
4. Warten.  
5. GamePass starten und Save überprüfen.

---

## 2. `struct.error` beim Parsen des Saves
**Ursache:** Save-Datei ist veraltet.  
**Lösung:**  
- Save in Solo/Koop oder dedizierten Server laden.  
- Spiel einmal starten, um **automatisches Strukturupdate** auszulösen.  
- Sicherstellen, dass Save **ab dem neuesten Patch** ist.

---

## 3. `PalworldSaveTools.exe - Systemfehler`
**Fehlermeldung:**
The code execution cannot proceed because VCRUNTIME140.dll was not found.
Reinstalling the program may fix this problem.

**Ursache:** Manche PCs (Minimal-Systeme, Sandbox oder VM) haben diese DLL nicht.  
**Lösung:**  
- Installiere die **Microsoft Visual C++ Redistributable 2015–2022**  
- [Link zur offiziellen Microsoft-Seite](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable)