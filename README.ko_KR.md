[English](README.en_US.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

![PalworldSaveTools Logo](Assets/resources/PalworldSaveTools.png)
---
- **Discord로 연락:** Pylar1991
---
---
- **[https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) 에서 독립 실행형 폴더를 다운로드하여 .exe를 사용하세요!**
---

## 기능

- **초고속 파싱/읽기** 도구 – 가장 빠른 도구 중 하나.  
- 모든 플레이어/길드를 목록화.  
- 모든 팰과 상세정보 표시.  
- 플레이어의 마지막 온라인 시간 표시.  
- 플레이어 데이터를 `players.log`에 기록.  
- 보유 팰 수 기준으로 플레이어 기록 및 정렬.  
- **기지 지도 보기** 제공.  
- 비활성 기지를 대상으로 하는 PalDefender용 자동 `killnearestbase` 명령 생성.  
- 전용 서버 ↔ 싱글/협동 세계 간 저장 데이터 전송.  
- GUID 편집을 통한 호스트 세이브 복구.  
- Steam ID 변환 포함.  
- 좌표 변환 포함.  
- GamePass ⇔ Steam 변환 포함.  
- Bigger PalBox 모드 호환 슬롯 증가 인젝터.  
- 도구 사용 간 자동 백업.  
- **All in One Tools** (구 All in One Deletion Tool):
  - 플레이어 삭제  
  - 기지 삭제  
  - 길드 삭제  
  - **모든 길드 재구축**  
    - 팰을 올바른 길드로 재할당  
    - 그룹 ID 수정  
    - 원정 플래그 제거  
    - 작업 적성 초기화  
    - 중복 없는 길드 핸들 재구축  
  - 대공 포탑 초기화  
  - 참조되지 않은 데이터 삭제  
  - 미션 초기화  
  - 개인 상자 잠금 해제  
  - 잘못되거나 모드된 아이템 / 팔 제거  
  - 보호된 플레이어/길드/기지를 위한 제외 시스템  
  - 플레이어 길드 이동  
  - 길드 리더 설정  
  - 기타 도구를 파일 메뉴에 통합  


## 🗺️ 지도 잠금 해제 단계

> **참고:** "Restore Map" 옵션을 사용하지 않는 경우에만 적용됩니다.  
> ⚠️ PST의 완전히 잠금 해제된 지도로 현재 진행 상황이 덮어쓰여집니다.

### 1️⃣ 잠금 해제 지도 파일 복사
`Assets\resources\LocalData.sav`에서 `LocalData.sav` 복사.

### 2️⃣ 새 서버/월드 ID 확인
- **새 서버/월드에 접속**.  
- 파일 탐색기 열고 다음 경로 붙여넣기:

%localappdata%\Pal\Saved\SaveGames\


- **랜덤 ID 폴더** 확인 — 이것이 **Steam ID**.  
- 폴더 열고 "수정 날짜" 기준으로 하위 폴더 정렬.  
- 새 서버/월드 ID와 일치하는 폴더 확인.

### 3️⃣ 지도 파일 교체
- 복사한 `LocalData.sav`를 **새 서버/월드 폴더**에 붙여넣기.  
- 덮어쓰기 확인 메시지가 나오면 **덮어쓰기** 선택.

### 🎉 완료!
**새 서버/월드** 실행 — PST `Assets\resources`의 잠금 해제 지도와 동일하게 안개와 아이콘 표시.

---

## 🔁 Host/Co-op ↔ 서버 전환

**Host/Co-op** 저장 폴더:

%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\


**전용 서버** 저장 폴더:

steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\


---

### 🧪 전송 과정

1. **`Level.sav` 및 `Players` 폴더**를 Host/Co-op 또는 전용 서버에서 복사.  
2. 다른 저장 폴더 유형(Host ↔ 서버)에 붙여넣기.  
3. 게임 또는 서버 실행.  
4. **새 캐릭터 생성** 요청 시 생성.  
5. 약 2분간 자동 저장 후 게임/서버 종료.  
6. 새로 업데이트된 **`Level.sav` 및 `Players` 폴더** 복사.  
7. PC의 **임시 폴더**에 붙여넣기.  
8. **PST(PalworldSaveTools)** 열고 **Fix Host Save** 선택.  
9. 임시 폴더에서 **`Level.sav`** 선택.  
10. 선택:  
    - **기존 캐릭터** (원본 세이브)  
    - **새 캐릭터** (방금 생성한 캐릭터)  
11. **Migrate** 클릭.  
12. 마이그레이션 완료 후 임시 폴더에서 업데이트된 **`Level.sav` 및 `Players` 폴더** 복사.  
13. 실제 저장 폴더에 붙여넣기 (Host 또는 서버).  
14. 게임/서버 실행 후 캐릭터와 진행 상태 즐기기.

---

# Palworld 호스트 교체 과정 (UID 설명)

## 배경
- **호스트는 항상 `0001.sav` 사용** — 누가 호스트든 동일 UID.  
- 각 클라이언트는 고유 **일반 UID 세이브** 사용 (예: `123xxx.sav`, `987xxx.sav`).

## 전제 조건
구 호스트와 신 호스트 모두 **일반 세이브가 생성**되어 있어야 함.  
없으면 호스트 월드 접속 후 새 캐릭터 생성으로 생성.

---

## 단계별 호스트 교체

### 1. 일반 세이브 존재 확인
- 플레이어 A (구 호스트): 일반 세이브 `123xxx.sav` 보유.  
- 플레이어 B (신 호스트): 일반 세이브 `987xxx.sav` 보유.

### 2. 구 호스트 Host Save → 일반 세이브
- PalworldSaveTools **Fix Host Save** 사용:  
  - 구 호스트 `0001.sav` → `123xxx.sav`  
  (구 호스트 진행 상황을 일반 슬롯으로 이동)

### 3. 신 호스트 일반 세이브 → Host Save
- **Fix Host Save** 사용:  
  - 신 호스트 `987xxx.sav` → `0001.sav`  
  (신 호스트 진행 상황을 호스트 슬롯으로 이동)

---

## 결과
- 플레이어 B가 호스트가 되어 캐릭터와 팔이 `0001.sav`에 존재.  
- 플레이어 A는 클라이언트가 되어 진행 상태는 `123xxx.sav`에 존재.

---

## 요약
- **먼저 구 호스트 `0001.sav`를 일반 UID 세이브로 이동**  
- **그 다음 신 호스트 일반 UID 세이브를 `0001.sav`로 이동**

---

이 과정으로 호스트 변경 시 양쪽 플레이어의 캐릭터와 팔을 그대로 유지 가능.

---

# 🐞 알려진 버그 / 문제

## 1. Steam ➝ GamePass 변환기 작동하지 않음
**문제:** 변환기로 변경한 내용이 적용되지 않거나 유지되지 않음.  
**해결:**  
1. GamePass 버전 Palworld 종료.  
2. 몇 분 대기.  
3. Steam ➝ GamePass 변환기 실행.  
4. 다시 대기.  
5. GamePass Palworld 실행 후 세이브 확인.

---

## 2. 세이브 파싱 시 `struct.error`
**원인:** 세이브 파일 형식이 오래되어 현재 도구와 호환되지 않음.  
**해결:**  
- 오래된 세이브를 **Solo, Coop, Dedicated Server** 모드에서 로드.  
- 한 번 게임을 로드하여 **자동 구조 업데이트** 트리거.  
- 최신 패치 이후 업데이트 여부 확인.

---

## 3. `PalworldSaveTools.exe - System Error`
**에러 메시지:**

The code execution cannot proceed because VCRUNTIME140.dll was not found.
Reinstalling the program may fix this problem.

**원인:** 일부 PC(최소 구성, 샌드박스, VM)에 필요한 DLL이 없음.  
**해결:**  
- 최신 **Microsoft Visual C++ Redistributable** 설치  
- 다운로드: [Microsoft Visual C++ 2015–2022 Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable)