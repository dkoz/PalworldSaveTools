[English](README.en_US.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

![PalworldSaveTools Logo](Assets/resources/PalworldSaveTools_Black.png)
---
- **Discordで連絡:** Pylar1991
---
---
- **[https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) からスタンドアロンフォルダをダウンロードして、.exe を使用してください！**
---

## 機能

- **超高速パース/読み込み**ツール（最高クラスの速度）。  
- 全プレイヤー/ギルドを一覧表示。  
- 全パルとその詳細を一覧表示。  
- プレイヤーの最終オンライン時間を表示。  
- プレイヤー情報を `players.log` に記録。  
- 所有パル数でプレイヤーを記録・並び替え。  
- **基地マップビュー**を提供。  
- 非アクティブ基地向けの PalDefender 用 `killnearestbase` 自動コマンド生成。  
- 専用サーバーとシングル/協力プレイ間でセーブデータ転送。  
- GUID 編集によるホストセーブ修復。  
- Steam ID 変換を搭載。  
- 座標変換を搭載。  
- GamePass ⇔ Steam 変換を搭載。  
- Bigger PalBox 対応のスロット増加インジェクター。  
- ツール使用間の自動バックアップ。  
- **All in One Tools**（旧 All in One Deletion Tool）:
  - プレイヤー削除  
  - 基地削除  
  - ギルド削除  
  - **ギルドを全再構築**  
    - 各パルを正しいギルドへ再割り当て  
    - グループID修正  
    - 遠征フラグ削除  
    - 作業適性をリセット  
    - 重複のないギルドハンドルを再構築  
  - 対空砲台のリセット  
  - 未参照データの削除  
  - ミッションのリセット  
  - プライベートチェストの解除  
  - 無効・改造されたアイテム／パルを削除  
  - プレイヤー/ギルド/基地保護用の除外システム  
  - ギルド間でプレイヤー移動  
  - ギルドリーダーの設定  
  - 他ツールをファイルメニューへ統合  


## 🗺️ マップアンロック手順

> **注意:** 「Restore Map」を使用しない場合のみ適用されます。  
> ⚠️ PSTの完全アンロックマップで現在のマップ進行が上書きされます。

### 1️⃣ アンロックマップファイルをコピー
`Assets\resources\LocalData.sav` から `LocalData.sav` をコピー。

### 2️⃣ 新しいサーバー/ワールドIDを確認
- **新しいサーバー/ワールドに参加**。  
- エクスプローラーを開き、以下を貼り付け：

%localappdata%\Pal\Saved\SaveGames\


- **ランダムIDのフォルダ**を探す — これがあなたの **Steam ID**。  
- フォルダを開き、「更新日時」でサブフォルダをソート。  
- 新しいサーバー/ワールドIDに一致するフォルダを見つける。

### 3️⃣ マップファイルを置換
- コピーした `LocalData.sav` を **新しいサーバー/ワールドフォルダ** に貼り付け。  
- 上書き確認が出た場合は **上書き** を選択。

### 🎉 完了！
**新しいサーバー/ワールド** を起動 — PST の `Assets\resources` のアンロックマップと同じ霧とアイコンになります。

---

## 🔁 Host/Co-op からサーバーへの移行、またはその逆

**Host/Co-op** のセーブフォルダ:

%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\


**専用サーバー** のセーブフォルダ:

steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\


---

### 🧪 転送手順

1. **`Level.sav` と `Players` フォルダ** を Host/Co-op または専用サーバーのセーブからコピー。  
2. 別のセーブフォルダタイプ（Host ↔ サーバー）に貼り付け。  
3. ゲームまたはサーバーを起動。  
4. **新しいキャラクター作成**を求められたら作成。  
5. 約2分間オートセーブを待機後、ゲーム/サーバーを終了。  
6. 更新された **`Level.sav` と `Players` フォルダ** をコピー。  
7. PCの **一時フォルダ** に貼り付け。  
8. **PST(PalworldSaveTools)** を開き、**Fix Host Save** を選択。  
9. 一時フォルダの **`Level.sav`** を選択。  
10. 選択:  
    - **古いキャラクター**（元のセーブ）  
    - **新しいキャラクター**（作成したばかり）  
11. **Migrate** をクリック。  
12. マイグレーション後、一時フォルダから更新された **`Level.sav` と `Players` フォルダ`** をコピー。  
13. 実際のセーブフォルダに貼り付け（Hostまたはサーバー）。  
14. ゲーム/サーバーを起動して、キャラクターと進行状況を楽しむ！

---

# Palworld ホストスワップ手順（UID解説）

## 背景
- **ホストは常に `0001.sav`** — 誰がホストでも同じUID。  
- クライアントは個別の **通常UIDセーブ** を使用（例: `123xxx.sav`, `987xxx.sav`）。

## 前提条件
古いホストと新ホストの両方が **通常セーブを持つ** 必要があります。  
ない場合は、ホストのワールドで新キャラクターを作成して生成。

---

## ホストスワップ手順

### 1. 通常セーブの確認
- プレイヤーA（旧ホスト）：通常セーブ `123xxx.sav` を持つ。  
- プレイヤーB（新ホスト）：通常セーブ `987xxx.sav` を持つ。

### 2. 旧ホストの Host Save を通常セーブへ
- PalworldSaveTools **Fix Host Save** 使用:  
  - 旧ホスト `0001.sav` → `123xxx.sav`  
  （旧ホストの進行状況を通常スロットへ移動）

### 3. 新ホストの通常セーブを Host Save へ
- **Fix Host Save** 使用:  
  - 新ホスト `987xxx.sav` → `0001.sav`  
  （新ホストの進行状況をホストスロットへ移動）

---

## 結果
- プレイヤーBがホストになり、キャラクターとパルは `0001.sav` に。  
- プレイヤーAはクライアントになり、進行状況は `123xxx.sav` に。

---

## まとめ
- **まず旧ホストの `0001.sav` を通常UIDセーブへ移動**  
- **次に新ホストの通常UIDセーブを `0001.sav` へ移動**  

---

この手順で、ホスト変更時に両プレイヤーのキャラクターとパルを保持可能。

---

# 🐞 既知のバグ / 問題

## 1. Steam ➝ GamePass コンバーターが動作しない
**問題:** コンバーターでの変更が適用されない/保持されない。  
**解決方法:**  
1. GamePass版 Palworld を閉じる。  
2. 数分待機。  
3. Steam ➝ GamePass コンバーターを実行。  
4. 再度待機。  
5. GamePass版 Palworld を起動してセーブを確認。

---

## 2. 保存解析時に `struct.error`
**原因:** 保存形式が古く、現行ツールと互換性がない。  
**解決方法:**  
- 古い保存を **Solo, Coop, Dedicated Server** で読み込む。  
- 1回ロードして自動構造更新をトリガー。  
- 最新パッチ以降の更新を確認。

---

## 3. `PalworldSaveTools.exe - System Error`
**エラーメッセージ:**

The code execution cannot proceed because VCRUNTIME140.dll was not found.
Reinstalling the program may fix this problem.

**原因:** 一部のPC（最小構成、サンドボックス、VM）に必要DLLが存在しない。  
**解決方法:**  
- 最新版 **Microsoft Visual C++ Redistributable** をインストール  
- ダウンロード: [Microsoft Visual C++ 2015–2022 Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable)