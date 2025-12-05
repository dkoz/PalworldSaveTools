[English](README.en_US.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

![PalworldSaveTools Logo](Assets/resources/PalworldSaveTools.png)
---
- **联系 Discord：** Pylar1991
---
---
- **请从 [https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) 下载独立版文件夹以便使用 .exe！**
---

## 功能

- **高速解析/读取**工具——市面上最快之一。  
- 列出所有玩家/公会。  
- 列出所有帕鲁及其详细信息。  
- 显示玩家最后在线时间。  
- 将玩家及其数据记录到 `players.log` 中。  
- 根据拥有帕鲁数量记录并排序玩家。  
- 提供 **基地地图视图**。  
- 为 PalDefender 自动生成 `killnearestbase` 指令以清理不活跃基地。  
- 在专用服务器与单人/联机世界之间转移存档。  
- 通过 GUID 编辑修复主机存档。  
- 内置 Steam ID 转换。  
- 内置坐标转换。  
- 内置 GamePass ⇔ Steam 转换。  
- 玩家槽位扩展注入器（兼容 Bigger PalBox 模组）。  
- 工具使用之间自动备份。  
- **All in One Tools**（原 All in One Deletion Tool）:
  - 删除玩家  
  - 删除基地  
  - 删除公会  
  - **重建所有公会**  
    - 将所有帕鲁重新分配到正确公会  
    - 修复 group_id（公会ID）  
    - 清除远征标记  
    - 重置工作适性  
    - 重建无重复的公会句柄列表  
  - 重置防空炮台  
  - 删除未引用数据  
  - 重置任务  
  - 解锁私人箱子  
  - 删除无效或被修改的物品 / 帕鲁 
  - 排除系统（保护指定玩家/公会/基地）  
  - 在公会之间移动玩家  
  - 设置玩家为公会会长  
  - 将其他工具整合到文件菜单中  


## ✏️ 修改存档：编辑器选择

- 点击应用内的“修改存档”时，将弹出选择窗口：
  - Palworld Save Pal（推荐）：功能全面、集成更紧密；若未安装将自动下载并启动。
  - Palworld Pal Editor：支持 GUI/Web/CLI；若未安装也会自动下载并启动。
- 提示：修改前请务必备份存档。

---

## 🗺️ 解锁地图步骤

> 仅当你不使用“还原地图（Restore Map）”功能时适用。
> ⚠️ 这会用 PST 自带的全开地图覆盖你当前的地图进度。

### 1️⃣ 复制解锁地图文件
从 `Assets\resources\LocalData.sav` 复制 `LocalData.sav`。

### 2️⃣ 查找新的服务器/世界 ID
- 进入你的新服务器/世界
- 打开资源管理器并粘贴：

```
%localappdata%\Pal\Saved\SaveGames\
```

- 找到一个名字为长随机 ID 的文件夹（这是你的 Steam ID）
- 打开该文件夹并按“修改日期”排序子文件夹
- 找到与你的新服务器/世界 ID 对应的文件夹

### 3️⃣ 替换地图文件
- 将复制的 `LocalData.sav` 粘贴到上述服务器/世界文件夹
- 若提示覆盖，确认替换

### 🎉 完成
启动你的新服务器/世界——迷雾与图标将与 PST 资源文件中的全开地图一致。

---

## 🔁 从主机/联机与服务器互转

主机/联机的存档位置通常为：

```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

独立服务器的存档位置通常为：

```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

---

### 🧪 转移流程

1. 从你的主机/联机或独服世界复制 **`Level.sav` 与 `Players` 文件夹**
2. 将这两者粘贴到另一种存档类型的目录（主机 ↔ 服务器）
3. 启动游戏或服务器
4. 当提示创建**新角色**时，按提示创建
5. 等待约 2 分钟自动保存后，关闭游戏/服务器
6. 从该世界复制新的 **`Level.sav` 与 `Players` 文件夹**
7. 将其粘贴到你电脑上的**临时文件夹**
8. 打开 **PST(PalworldSaveTools)** 并选择 **Fix Host Save**
9. 选择临时文件夹内的 **`Level.sav`**
10. 选择：
    - **旧角色**（来自原存档）
    - **新角色**（你刚创建的）
11. 点击 **Migrate**
12. 迁移完成后，从临时文件夹复制更新后的 **`Level.sav` 与 `Players` 文件夹**
13. 粘贴回你的实际存档位置（主机或服务器）
14. 启动游戏/服务器，享受你完整进度的角色！

---

# Palworld 主机切换流程（UID 说明）

## 背景
- **主机永远使用 `0001.sav`** —— 无论谁当主机，UID 固定
- 每个客户端使用自己的**常规 UID 存档**（如 `123xxx.sav`、`987xxx.sav`）

## 前置条件
双方（旧主机与新主机）都需要拥有各自的常规存档。若没有，进入主机世界创建新角色即可生成。

---

## 步骤

### 1. 确保双方均有常规存档
- A（旧主机）拥有常规存档（如 `123xxx.sav`）
- B（新主机）拥有常规存档（如 `987xxx.sav`）

### 2. 将旧主机的主机存档转为其常规存档
- 使用 PalworldSaveTools 的 **Fix Host Save**：
  - 旧主机 `0001.sav` → `123xxx.sav`

### 3. 将新主机的常规存档转为主机存档
- 使用 **Fix Host Save**：
  - 新主机 `987xxx.sav` → `0001.sav`

---

## 结果
- B 成为主机，其角色与帕鲁位于 `0001.sav`
- A 成为客户端，原进度保存在 `123xxx.sav`

---

## 总结
- 先把旧主机的 `0001.sav` 转到其常规 UID 存档
- 再把新主机的常规 UID 存档转到 `0001.sav`

---

该流程可在切换主机时保留双方的角色与帕鲁完整数据。

---


# 🐞 已知问题

## 1. Steam ➝ GamePass 转换器不生效
**现象：** 转换后的改动未应用或未保留  
**处理：** 关闭 GamePass 版 Palworld → 等几分钟 → 运行转换 → 再等 → 打开 GamePass 版验证

---

## 2. 解析存档时出现 `struct.error`
**原因：** 存档结构过旧，与当前工具不兼容  
**解决：** 将旧存档放入单人/联机或独服中运行一次，触发结构升级；确保在最新补丁或之后更新

---

## 3. `PalworldSaveTools.exe - System Error`
**错误信息：**

```
The code execution cannot proceed because VCRUNTIME140.dll was not found.
Reinstalling the program may fix this problem.
```

**原因：** 某些系统（精简系统、沙箱或虚拟机）缺少必需的运行库  
**解决：** 安装最新的 **Microsoft Visual C++ 2015–2022 Redistributable**（微软官网可下载）