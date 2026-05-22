# 화자 구분 회의비서 — Windows 추가 세팅 가이드

> 기본 세팅(`../세팅가이드_Windows.md` 1~13단계)이 끝났다고 가정합니다.
> Python · PowerShell 7 · Claude Code 가 이미 동작하는 상태에서 시작.
>
> 추가 소요 시간: 약 20~30분 (HuggingFace 가입 + 모델 다운로드 포함)
>
> 각 단계 = **작업 → 명령어 → 예상 결과 → 흔한 오류 / 대처 → 검증**.

---

## 1. HuggingFace 계정 가입

**작업** — pyannote 화자 분리 모델 3개를 다운로드하려면 HuggingFace 계정이 필요.

**절차** — GUI 작업:
1. <https://huggingface.co/join> 접속
2. 이메일 + 비밀번호 입력 → *Next*
3. 이메일 인증 메일 확인 → 링크 클릭
4. 프로필 설정 (이름·소속 자유롭게)

**예상 결과**: <https://huggingface.co> 에 로그인된 상태.

**흔한 오류 / 대처**:
- 인증 메일이 안 옴 → 스팸함 확인, *Resend confirmation email*
- 회사 메일이 차단됨 → Gmail 등 개인 메일 사용

**검증**:
브라우저에서 <https://huggingface.co/settings/account> 접속 → 본인 이름·이메일 표시되면 OK

---

## 2. HuggingFace Read 토큰 발급

**작업** — 모델 다운로드 시 본인 인증용 토큰.

**절차**:
1. <https://huggingface.co/settings/tokens> 접속
2. **Create new token** 클릭
3. **Token type** → **Read** 선택 (Fine-grained 아님)
4. **Token name** → `pyannote` (자유)
5. **Create token** 클릭
6. ★ **표시된 `hf_...` 토큰 즉시 복사** (한 번만 표시됨, 닫으면 못 봄)

**예상 결과**: `hf_` 로 시작하는 약 37자 토큰을 클립보드에 보유.

**흔한 오류 / 대처**:
- 실수로 닫음 → 같은 페이지에서 새 토큰 발급 (옛 토큰 폐기)
- *Fine-grained* 선택함 → 그래도 *"Read access to contents of all public gated repos"* 만 체크하면 OK. 하지만 **Read** 가 가장 단순

**검증**:
복사한 토큰이 `hf_` 로 시작 + 약 37자인지 메모장에 임시로 붙여넣어 확인

---

## 3. pyannote 모델 3개 동의

**작업** — pyannote는 gated 모델이라 *각 모델 페이지에서 따로* 라이선스 동의 필요. **3개 모두 빠짐없이**.

**절차** — 다음 3개 페이지를 *각각* 방문해 폼 작성 + Submit:

| # | 모델 페이지 |
|---|---|
| 1 | <https://huggingface.co/pyannote/speaker-diarization-3.1> |
| 2 | <https://huggingface.co/pyannote/segmentation-3.0> |
| 3 | <https://huggingface.co/pyannote/speaker-diarization-community-1> |

각 페이지에서:
1. 상단 *"You need to agree to share your contact information"* 박스 확인
2. **Company / University**: `Personal` 또는 회사명 자유
3. **Website**: 비워도 됨
4. **Use case**: `Personal meeting transcription` 한 줄
5. 라이선스 체크박스 모두 ON → **Submit**

**예상 결과**: 각 페이지 상단에 ✅ **"You have been granted access to this model"** 표시.

**흔한 오류 / 대처**:
- *Submit* 후에도 *"Waiting for approval"* — 보통 즉시 승인. 1~2분 기다린 후 새로고침
- 페이지 못 찾음 → URL 오타 확인

**검증**:
세 페이지 모두 *"You have been granted access to this model"* 초록 박스가 떠야 함. 하나라도 없으면 다음 단계에서 막힘.

---

## 4. 추가 Python 라이브러리 설치

**작업** — 화자 구분에 필요한 `pyannote.audio` + `python-dotenv` 설치.

**명령어** — 화자 구분 폴더로 이동 후:
```powershell
cd ..\01-1_회의비서_화자구분
python -m pip install -r requirements.txt
```

**예상 결과** — 5~10분 동안 설치 진행:
```
Collecting pyannote.audio>=3.1.0 ...
Collecting torch ...
Successfully installed pyannote.audio-... torch-... python-dotenv-...
```

**흔한 오류 / 대처**:
- 다운로드 멈춤 → 같은 명령 재실행 (캐시 사용)
- `Microsoft Visual C++ 14.0 or greater is required`
  → <https://aka.ms/vs/17/release/vs_BuildTools.exe> 설치 시 *C++ 빌드 도구* 선택 → 재시도
- `ERROR: ... uses Cargo` → Rust 컴파일러 미설치. <https://rustup.rs/> 에서 설치 후 새 PowerShell

**검증**:
```powershell
python -c "import pyannote.audio; print('pyannote OK')"
python -c "import dotenv; print('dotenv OK')"
```
→ 두 줄 모두 `OK` 출력되면 정상

---

## 5. .env 파일 만들고 토큰 저장

**작업** — 발급받은 HF 토큰을 `.env` 파일에 저장. 코드에 직접 쓰지 않기.

**명령어**:
```powershell
Copy-Item .env.example .env
notepad .env
```

메모장이 열리면 마지막 줄의 `hf_여기에_본인의_HuggingFace_Read_토큰_붙여넣기` 부분을 **2단계에서 복사한 실제 토큰**으로 교체:

```
HF_TOKEN=hf_여기에_복사한_실제_토큰_붙여넣기
```

**저장**: `Ctrl + S` → 메모장 닫기.

**예상 결과**: `.env` 파일이 폴더 안에 생성되고 본인 토큰이 들어있음.

**흔한 오류 / 대처**:
- `.env.txt` 로 저장됨 (메모장이 자동 확장자 추가)
  → 파일 탐색기에서 보기 → *파일 확장명* 켜기 → `.env.txt` 를 `.env` 로 이름 변경
- 토큰 앞뒤에 공백·따옴표 추가됨
  → `HF_TOKEN=hf_xxx` 형식 그대로 (공백 X, 따옴표 X)

**검증**:
```powershell
type .env
```
→ `HF_TOKEN=hf_xxx...` 한 줄이 정상 표시되면 OK

---

## 6. 텍스트 입력으로 빠른 검증 (모델 다운로드 없음)

**작업** — 환경 정상 여부 빠르게 확인. 음성이 아닌 *이미 화자 표기된 텍스트*를 입력해 5초 만에 결과 확인.

**명령어**:
```powershell
python run.py samples\sample_transcript.txt
```

**예상 결과**:
```
📥 입력: sample_transcript.txt
📄 텍스트 로드...
   ↳ 1,045자
🤖 Claude 요약 + 액션 추출...
🎨 HTML 렌더링 (화자별 색상)...
✅ 완료: output\2026...html
```
→ 브라우저가 자동으로 열리고 *화자 3명(김부장/이대리/박과장)이 색상 다르게* 표시되는 HTML 리포트.

**흔한 오류 / 대처**:
- `claude CLI 호출 실패` → 기본 세팅의 *Claude Code 로그인* 미완료. `claude login` 재실행
- 브라우저 안 열림 → `output\` 폴더에 생성된 `.html` 파일을 직접 더블 클릭

**검증**:
브라우저의 *회의 전문* 섹션을 펼쳤을 때 *김부장* / *이대리* / *박과장* 이름이 **서로 다른 색**으로 표시되면 OK

---

## 7. 마이크 녹음으로 실제 화자 분리 (★ 첫 실행 시 모델 다운로드 ~2GB)

**작업** — 진짜 음성에서 화자 자동 분리. 첫 실행은 모델 다운로드로 10~20분 걸림. 두 번째부터는 즉시.

**명령어**:
```powershell
python run.py --record
```

**테스트 시나리오** (★ 정확도 잘 나오는 조건):
- **두 명 이상**이 번갈아 발화
- 각자 **최소 10초** 발화 (너무 짧으면 임베딩 부족)
- **총 30초~1분** 권장
- 예시 대본:
  - A: *"안녕하세요. 오늘 회의 시작하겠습니다. 첫 번째 안건은 카드뉴스 자동화입니다."* (12초)
  - B: *"네, 마케팅팀에서 다음 주까지 시안 가져오기로 했습니다. 검토는 누가 할까요?"* (10초)
  - A: *"박과장님께서 검토 부탁드립니다. 금요일까지 회신 부탁드려요."* (8초)
  - B: *"네 알겠습니다. 금요일 오후 3시까지 피드백 드리겠습니다."* (10초)

녹음 종료: **Enter** 키.

**예상 결과** — 첫 실행:
```
🎤 입력 장치: ...
🔴 녹음 시작 — Enter 또는 Ctrl+C로 종료
✅ 녹음 완료: 40초 ...
📥 입력: recording_...wav
📝 전사 + 화자 분리...
   ↳ Whisper 모델 로딩 (small, int8 CPU)...
   ↳ 전사 세그먼트 4개
   ↳ pyannote 화자 분리 중 (첫 실행은 ~1.5GB 모델 다운로드)...
pytorch_model.bin: 100%|████████| ...
   ↳ 화자 2명 감지: SPEAKER_00, SPEAKER_01
🤖 Claude 요약 + 액션 추출...
🎨 HTML 렌더링 (화자별 색상)...
✅ 완료: output\...html
```

**흔한 오류 / 대처**:
- `HF_TOKEN 환경변수가 비어 있습니다` → `.env` 파일 5단계 재확인. 새 PowerShell 창
- `Access to model ... is restricted` → 3단계의 해당 모델 동의 누락. URL 다시 가서 *granted access* 확인
- `PortAudioError` → 설정 → 개인 정보 및 보안 → 마이크 → ★ ***데스크톱 앱이 마이크에 액세스하도록 허용*** 토글 ON
- 모델 다운로드 중 *멈춘 듯 보임* → 정상. ~10~20분. 인터넷 속도에 따라
- `AttributeError: 'DiarizeOutput' object has no attribute 'itertracks'` → git pull 로 최신 코드 받기 (`git pull origin main`)

**검증**:
브라우저에서 *회의 전문* 섹션 펼침 → `SPEAKER_00`, `SPEAKER_01` (혹은 더 많은 라벨) 이 *서로 다른 색*으로 표시되면 화자 분리 성공.

---

## 7-보충. 화자 분리 — *어떤 기준으로* 동작하나

**작업** — 결과가 기대와 다를 때 *왜 그런지* 이해하기. 4단계 알고리즘 + 정확도 영향 요소.

**4단계 알고리즘**:

```
🎵 입력 오디오
    ↓
① VAD (Voice Activity Detection) — 발화 vs 무음 분리
    ↓
② Segmentation — 발화 구간을 1~2초 조각으로 자름
    ↓
③ Embedding — 각 조각의 *목소리 특징*을 192차원 벡터로 (음역대·음색·발음 습관 등)
    ↓
④ Clustering — 비슷한 벡터끼리 묶어 *같은 사람* 판정
    ↓
SPEAKER_00, SPEAKER_01, ...
```

→ *내용*과는 무관, **목소리 특성**으로만 분리. *지문 분류*와 같은 원리.
→ 결과는 *익명 라벨*. *김부장* / *이대리* 매핑은 사람이 따로 (Week 2 미션 후보).

**정확도 영향 요소**:

| 조건 | 정확도 |
|---|---|
| 마이크 품질 (헤드셋 ≫ 노트북 내장) | ★★★★★ |
| 화자별 발화 시간 (각자 10초 이상) | ★★★★★ |
| 화자 수 2~6명 | ★★★★★ (가장 정확) |
| 화자 수 7~10명 | ★★★ (정확도 점차 ↓) |
| 화자 수 11명+ | ★★ (큰 회의장 무리) |
| 너무 비슷한 목소리 (가족·형제 등) | ★★ |
| 동시 발화 (overlap) | ★★★ — pyannote 3.1 은 일부 처리 |
| 짧은 발화 (1~2초만) | ★★ — 임베딩 데이터 부족 |
| 배경 음악·잡음 | ★★ — 사전 노이즈 제거 권장 |

> **권장 환경**: 2~6명 회의, 각자 10초 이상 발화, 마이크 1개로 모두 들리는 거리.

**검증** — 결과가 이상할 때 가장 먼저 확인:
- 화자 1명만 나옴 → *한 명만 길게 말했거나, 너무 비슷한 목소리*
- 화자가 너무 많이 나옴 (실제 3명인데 7명) → *마이크 노이즈 또는 동일인이 톤 바꿈*
- `UNKNOWN` 라벨 → *발화 구간 매칭 실패 (Whisper-pyannote 타임스탬프 불일치)*

---

## 8. (선택) 두 번째 실행 — 모델 캐시 사용

**작업** — 첫 실행 후 두 번째부터는 모델이 캐시되어 *대기 시간 ~1분*.

**명령어**:
```powershell
python run.py --record
```

녹음 30초 → Enter → 약 1분 후 HTML.

**검증**: 첫 실행 대비 *"모델 다운로드"* 표시 없이 바로 *"pyannote 화자 분리 중"* 으로 진행되면 캐시 정상.

---

## 무시해도 OK인 경고 메시지

다음 메시지들은 **모두 정상**이며 동작에 영향 없음:

```
Matplotlib is building the font cache; this may take a moment.
```
→ 첫 실행 한정. 폰트 캐시 빌드.

```
UserWarning: std(): degrees of freedom is <= 0
```
→ pyannote 내부 통계 경고. 짧은 음성 조각에 대해.

```
TF32 acceleration not available
```
→ NVIDIA GPU 가속 미사용 알림. CPU로도 동작.

---

## 통과 체크리스트

- [ ] HuggingFace 계정 생성 (1단계)
- [ ] Read 토큰 발급 및 복사 (2단계)
- [ ] 3개 모델 모두 *granted access* (3단계)
- [ ] `pyannote.audio` + `python-dotenv` 설치 (4단계)
- [ ] `.env` 파일에 토큰 저장 (5단계)
- [ ] 텍스트 입력 검증 통과 (6단계)
- [ ] 마이크 녹음 실제 화자 분리 통과 (7단계) — 첫 실행은 시간 걸림

8개 모두 체크되면 **화자 구분 회의비서 100% 동작**.

---

## 참고 자료

- 메인 세팅 가이드: `../세팅가이드_Windows.md`
- 기본 회의비서 (화자 구분 없는 버전): `../01_회의비서/`
- 강사 시연 흐름: `README.md` 의 *강의 시연 흐름* 섹션
