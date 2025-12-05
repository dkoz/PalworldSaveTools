[English](README.en_US.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

![PalworldSaveTools Logo](Assets/resources/PalworldSaveTools.png)
---
- **Contacto en Discord:** Pylar1991
---
---
- **Descarga la carpeta independiente desde [https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) para poder usar el .exe!**
---

## Características

- Herramienta de **lectura/análisis rápida**, una de las más veloces disponibles.  
- Lista todos los jugadores/gremios.  
- Lista todos los pals y sus detalles.  
- Muestra la última vez en línea de los jugadores.  
- Registra jugadores y datos en `players.log`.  
- Registra y ordena jugadores por la cantidad de pals que poseen.  
- Proporciona una **vista del mapa de bases**.  
- Genera comandos automáticos `killnearestbase` para PalDefender contra bases inactivas.  
- Transfiere guardados entre servidores dedicados y mundos individuales/coop.  
- Repara el guardado del host mediante edición de GUID.  
- Incluye conversión de Steam ID.  
- Incluye conversión de coordenadas.  
- Incluye conversión GamePass ⇔ Steam.  
- Inyector de slots para aumentar los espacios por jugador, compatible con Bigger PalBox mod.  
- Copias de seguridad automáticas entre usos de la herramienta.  
- **All in One Tools** (antes All in One Deletion Tool):
  - Eliminar jugadores  
  - Eliminar bases  
  - Eliminar gremios  
  - **Reconstruir todos los gremios**  
    - Reasigna cada pal a su gremio correcto  
    - Corrige IDs de grupo  
    - Elimina banderas de expedición  
    - Restablece aptitud laboral  
    - Reconstruye los handles sin duplicados  
  - Restablecer torretas antiaéreas  
  - Eliminar datos no referenciados  
  - Restablecer misiones  
  - Desbloquear cofres privados  
  - Eliminar objetos/pals no válidos o modificados 
  - Sistema de exclusiones para jugadores/gremios/bases protegidos  
  - Mover jugadores entre gremios  
  - Convertir un jugador en líder del gremio  
  - Integración de herramientas adicionales en el menú Archivo  

## 🗺️ Pasos para desbloquear el mapa

> **Nota:** Solo aplica si **NO** quieres usar la opción "Restore Map".  
> ⚠️ Esto sobrescribirá tu progreso actual del mapa con el mapa totalmente desbloqueado de PST.

### 1️⃣ Copiar el archivo de mapa desbloqueado
Copia el archivo `LocalData.sav` desde `Assets\resources\LocalData.sav`.

### 2️⃣ Encuentra la ID de tu nuevo servidor/mundo
- **Únete a tu nuevo servidor/mundo**.  
- Abre el explorador y pega:

%localappdata%\Pal\Saved\SaveGames\



- Busca una carpeta con una **ID aleatoria** — esta es tu **Steam ID**.  
- Abre esa carpeta y ordena los subdirectorios por **"Última modificación"**.  
- Encuentra la carpeta que corresponde a tu **nueva ID de servidor/mundo**.

### 3️⃣ Reemplaza el archivo de mapa
- Pega el `LocalData.sav` copiado en esta **nueva carpeta del servidor/mundo**.  
- Confirma la sobrescritura si se solicita.

### 🎉 ¡Listo!
Lanza tu **nuevo servidor/mundo** — la niebla y los íconos ahora coinciden con el mapa desbloqueado de PST.

---

## 🔁 Para mover de Host/Coop a Servidor o viceversa

Para **Host/Coop**, la carpeta de guardado normalmente está en:

%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\


Para **servidores dedicados**:

steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\


---

### 🧪 Proceso de transferencia

1. Copia **`Level.sav` y la carpeta `Players`** desde tu guardado de **Host/Coop** o **Servidor Dedicado**.  
2. Pégalo en la otra carpeta de tipo guardado (Host ↔ Servidor).  
3. Inicia el juego o servidor.  
4. Cuando se te pida, crea un **nuevo personaje**.  
5. Espera ~2 minutos para el auto-guardado y luego cierra juego/servidor.  
6. Copia el actualizado **`Level.sav` y `Players`** desde ese mundo.  
7. Pégalos en una **carpeta temporal** en tu PC.  
8. Abre **PST(PalworldSaveTools)** y selecciona **Fix Host Save**.  
9. Selecciona **`Level.sav`** de la carpeta temporal.  
10. Elige:
    - **Personaje viejo** (del guardado original)  
    - **Personaje nuevo** (recién creado)  
11. Haz clic en **Migrate**.  
12. Copia tras la migración los actualizados **`Level.sav` y `Players`** de la carpeta temporal.  
13. Pégalos en tu carpeta de guardado real (Host o Servidor).  
14. Inicia juego/servidor y disfruta de tu personaje con todo el progreso intacto.

---

# Proceso de intercambio de Host en Palworld (UID explicado)

## Antecedentes
- **El Host siempre usa `0001.sav`** — misma UID para cualquiera que hostee.  
- Cada cliente usa un **guardado UID regular** (ej. `123xxx.sav`, `987xxx.sav`).

## Requisito clave
Ambos jugadores (Host antiguo y nuevo) **deben tener sus guardados regulares**.  
Se crea un personaje automáticamente si no existe.

---

## Pasos para intercambio de Host

### 1. Asegurar que existan guardados regulares
- Jugador A (Host antiguo) tiene un guardado regular (`123xxx.sav`).  
- Jugador B (Host nuevo) tiene un guardado regular (`987xxx.sav`).

### 2. Transferir guardado del Host antiguo a guardado regular
- Usando **Fix Host Save**:  
  `0001.sav` → `123xxx.sav`  
  (Transfiere progreso del antiguo Host a su slot regular)

### 3. Transferir guardado del nuevo Host a slot Host
- Usando **Fix Host Save**:  
  `987xxx.sav` → `0001.sav`  
  (Transfiere progreso del nuevo Host a slot Host)

---

## Resultado
- Jugador B ahora es el Host con su personaje y Pals en `0001.sav`.  
- Jugador A es cliente, su progreso original en `123xxx.sav`.

---

## Resumen
- **`0001.sav` antiguo Host → guardado UID regular**  
- **Guardado UID regular nuevo Host → `0001.sav`**

---

# 🐞 Errores / Problemas conocidos

## 1. Convertidor Steam ➝ GamePass no funciona
**Problema:** Los cambios no se aplican.  
**Solución:**  
1. Cierra la versión GamePass de Palworld.  
2. Espera unos minutos.  
3. Ejecuta el convertidor Steam ➝ GamePass.  
4. Espera nuevamente.  
5. Inicia Palworld en GamePass y verifica el guardado actualizado.

---

## 2. `struct.error` al parsear el guardado
**Causa:** Guardado desactualizado y no compatible con herramientas actuales.  
**Solución:**  
- Carga el guardado en Solo, Coop o Servidor Dedicado.  
- Ejecuta el juego una vez para activar **actualización automática de estructura**.  
- Asegúrate que el guardado sea **posterior al último parche**.

---

## 3. `PalworldSaveTools.exe - Error del sistema`
**Mensaje de error:**
The code execution cannot proceed because VCRUNTIME140.dll was not found.
Reinstalling the program may fix this problem.

**Causa:** Algunos PCs (sistemas mínimos, sandbox o VM) no tienen esta DLL.  
**Solución:**  
- Instala la **Microsoft Visual C++ Redistributable 2015–2022**  
- [Enlace oficial de Microsoft](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable)