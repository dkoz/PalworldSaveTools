[English](README.en_US.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

![PalworldSaveTools Logo](Assets/resources/PalworldSaveTools.png)
---
- **Contact Discord :** Pylar1991
---
---
- **Téléchargez le dossier autonome depuis [https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) pour pouvoir utiliser le .exe !**
---

## Fonctionnalités

- Outil de **lecture/analyse ultra rapide**, parmi les plus rapides disponibles.  
- Liste tous les joueurs/guildes.  
- Liste tous les pals et leurs détails.  
- Affiche la dernière activité en ligne des joueurs.  
- Enregistre les joueurs et leurs données dans `players.log`.  
- Enregistre et trie les joueurs selon le nombre de pals qu’ils possèdent.  
- Fournit une **vue de la carte des bases**.  
- Génère des commandes automatiques `killnearestbase` pour PalDefender ciblant les bases inactives.  
- Transfère les sauvegardes entre serveurs dédiés et mondes solo/coop.  
- Répare la sauvegarde hôte via modification GUID.  
- Inclut la conversion d’ID Steam.  
- Inclut la conversion de coordonnées.  
- Inclut la conversion GamePass ⇔ Steam.  
- Injecteur de slots pour augmenter les emplacements par joueur, compatible avec Bigger PalBox mod.  
- Sauvegarde automatique entre utilisations de l’outil.  
- **All in One Tools** (anciennement All in One Deletion Tool):
  - Supprimer des joueurs  
  - Supprimer des bases  
  - Supprimer des guildes  
  - **Reconstruire toutes les guildes**  
    - Réassigne chaque pal à la bonne guilde  
    - Répare les IDs de groupe  
    - Supprime les marqueurs d’expédition  
    - Réinitialise l’aptitude au travail  
    - Reconstruit les handles sans doublons  
  - Réinitialiser les tourelles anti-aériennes  
  - Supprimer les données non référencées  
  - Réinitialiser les missions  
  - Déverrouiller les coffres privés  
  - Supprimer les objets/pals invalides ou moddés 
  - Système d’exclusions pour joueurs/guildes/bases protégés  
  - Déplacer un joueur entre guildes  
  - Nommer un joueur chef de guilde  
  - Intègre d’autres outils dans le menu Fichier  


## 🗺️ Étapes pour débloquer la carte

> **Remarque :** S’applique uniquement si vous **ne voulez pas** utiliser l’option "Restore Map".  
> ⚠️ Cela écrasera votre progression actuelle avec la carte totalement débloquée de PST.

### 1️⃣ Copier le fichier de carte débloquée
Copiez le fichier `LocalData.sav` depuis `Assets\resources\LocalData.sav`.

### 2️⃣ Trouver l’ID de votre nouveau serveur/monde
- **Rejoignez votre nouveau serveur/monde**.  
- Ouvrez l’Explorateur et collez :

%localappdata%\Pal\Saved\SaveGames\


- Cherchez un dossier avec une **ID aléatoire** — c’est votre **Steam ID**.  
- Ouvrez-le et **triez les sous-dossiers par "Date de modification"**.  
- Trouvez le dossier correspondant à votre **nouveau serveur/monde**.

### 3️⃣ Remplacer le fichier de carte
- Collez le `LocalData.sav` copié dans ce **nouveau dossier serveur/monde**.  
- Confirmez le remplacement si demandé.

### 🎉 Terminé !
Lancez votre **nouveau serveur/monde** — le brouillard et les icônes correspondront maintenant à la carte débloquée de PST.

---

## 🔁 Pour déplacer de Host/Coop vers Serveur ou vice-versa

Pour **Host/Coop**, le dossier de sauvegarde se trouve généralement à :

%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\


Pour **serveurs dédiés** :

steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\


---

### 🧪 Processus de transfert

1. Copiez **`Level.sav` et le dossier `Players`** depuis votre sauvegarde Host/Coop ou Serveur dédié.  
2. Collez-les dans l’autre type de dossier de sauvegarde (Host ↔ Serveur).  
3. Lancez le jeu ou serveur.  
4. Créez un **nouveau personnage** si demandé.  
5. Attendez ~2 minutes pour l’auto-sauvegarde puis fermez le jeu/serveur.  
6. Copiez le **`Level.sav` et `Players`** mis à jour depuis ce monde.  
7. Collez-les dans un **dossier temporaire** sur votre PC.  
8. Ouvrez **PST(PalworldSaveTools)** et sélectionnez **Fix Host Save**.  
9. Sélectionnez le **`Level.sav`** dans le dossier temporaire.  
10. Choisissez :
    - **Ancien personnage** (de la sauvegarde originale)  
    - **Nouveau personnage** (créé récemment)  
11. Cliquez sur **Migrate**.  
12. Copiez les fichiers mis à jour **`Level.sav` et `Players`** du dossier temporaire.  
13. Collez-les dans votre dossier de sauvegarde réel (Host ou Serveur).  
14. Lancez le jeu/serveur et profitez de votre personnage avec tout le progrès intact.

---

# Processus d’échange de Host dans Palworld (UID expliqué)

## Contexte
- **Le Host utilise toujours `0001.sav`** — même UID pour tout host.  
- Chaque client utilise un **sauvegarde UID régulier** (ex. `123xxx.sav`, `987xxx.sav`).

## Pré-requis
Les deux joueurs (ancien et nouveau Host) **doivent avoir leurs sauvegardes régulières**.  
Un nouveau personnage est créé si aucune sauvegarde n’existe.

---

## Étapes pour échanger le Host

### 1. Vérifier l’existence des sauvegardes régulières
- Joueur A (ancien Host) a une sauvegarde régulière (`123xxx.sav`).  
- Joueur B (nouveau Host) a une sauvegarde régulière (`987xxx.sav`).

### 2. Transférer la sauvegarde de l’ancien Host vers sauvegarde régulière
- Utilisez **Fix Host Save** :  
  `0001.sav` → `123xxx.sav`  
  (Transfert du progrès de l’ancien Host vers son slot régulier)

### 3. Transférer la sauvegarde du nouveau Host vers slot Host
- Utilisez **Fix Host Save** :  
  `987xxx.sav` → `0001.sav`  
  (Transfert du progrès du nouveau Host vers le slot Host)

---

## Résultat
- Joueur B est maintenant le Host avec son personnage et Pals dans `0001.sav`.  
- Joueur A devient client avec son progrès original dans `123xxx.sav`.

---

## Résumé
- **`0001.sav` ancien Host → sauvegarde UID régulière**  
- **Sauvegarde UID régulière nouveau Host → `0001.sav`**

---

# 🐞 Bugs / Problèmes connus

## 1. Convertisseur Steam ➝ GamePass ne fonctionne pas
**Problème :** Les changements ne sont pas appliqués.  
**Solution :**  
1. Fermez la version GamePass de Palworld.  
2. Attendez quelques minutes.  
3. Exécutez le convertisseur Steam ➝ GamePass.  
4. Attendez à nouveau.  
5. Lancez Palworld sur GamePass et vérifiez que la sauvegarde est mise à jour.

---

## 2. `struct.error` lors de l’analyse de la sauvegarde
**Cause :** Sauvegarde obsolète et incompatible avec l’outil actuel.  
**Solution :**  
- Placez la sauvegarde dans Solo, Coop ou Serveur Dédié.  
- Lancez le jeu une fois pour déclencher **mise à jour automatique de la structure**.  
- Vérifiez que la sauvegarde est **après le dernier patch**.

---

## 3. `PalworldSaveTools.exe - Erreur système`
**Message d’erreur :**
The code execution cannot proceed because VCRUNTIME140.dll was not found.
Reinstalling the program may fix this problem.


**Cause :** Certains PC (systèmes minimalistes, sandbox ou VM) n’ont pas cette DLL requise.  
**Solution :**  
- Installez le **Microsoft Visual C++ Redistributable 2015–2022**  
- [Lien officiel Microsoft](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable)