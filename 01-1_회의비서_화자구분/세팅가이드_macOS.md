# 화자 구분 회의비서 — macOS 추가 세팅 가이드

> 기본 세팅(`../세팅가이드_macOS.md`)이 끝났다고 가정합니다.
> Python 3.12 · Homebrew · Claude Code 가 이미 동작하는 상태에서 시작.
>
> 추가 소요 시간: 약 20~30분 (HuggingFace 가입 + 모델 다운로드 포함)
>
> 각 단계 = **작업 → 명령어 → 예상 결과 → 흔한 오류 / 대처 → 검증**.

---

## 1. HuggingFace 계정 가입

**작업** — pyannote 화자 분리 모델 3개를 다운로드하려면 HuggingFace 계정이 필요.

**절차** — GUI:
1. <https://huggingface.co/join> 접속
2. 이메일 + 비밀번호 → *Next*
3. 이메일 인증 메일 → 링크 클릭
4. 프로필 설정 (이름·소속 자유롭게)

**예상 결과**: <https://huggingface.co> 로그인 상태.

**흔한 오류 / 대처**:
- 인증 메일이 안 옴 → 스팸함 확인, *Resend confirmation email*
- 회사 메일 차단 → Gmail 등 개인 메일

**검증**:
브라우저에서 <https://huggingface.co/settings/account> 접속 → 본인 이름·이메일 표시되면 OK

---

## 2. HuggingFace Read 토큰 발급

**작업** — 모델 다운로드 시 본인 인증용 토큰.

**절차**:
1. <https://huggingface.co/settings/tokens> 접속
2. **Create new token** 클릭
3. **Token type** → **Read** 선택
4. **Token name** → `pyannote` (자유)
5. **Create token** 클릭
6. ★ **표시된 `hf_...` 토큰 즉시 복사** (한 번만 표시됨)

**예상 결과**: `hf_` 로 시작하는 약 37자 토큰을 클립보드에 보유.

**흔한 오류 / 대처**:
- 실수로 닫음 → 같은 페이지에서 새 토큰 발급
- *Fine-grained* 선택함 → *"Read access to contents of all public gated repos"* 만 체크하면 OK. **Read** 가 가장 단순

**검증**:
토큰이 `hf_` 시작 + 약 37자인지 임시 메모장에 붙여넣어 확인

---

## 3. pyannote 모델 3개 동의

**작업** — pyannote 는 gated 모델이라 **각 모델 페이지마다 따로** 라이선스 동의 필요. **3개 모두 빠짐없이**.

**절차** — 다음 3개 페이지를 각각 방문해 폼 작성 + Submit:

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

**검증**:
세 페이지 모두 *"You have been granted access to this model"* 초록 박스가 떠야 함.

---

## 4. 추가 Python 라이브러리 설치

**작업** — 화자 구분에 필요한 `pyannote.audio` + `python-dotenv` 설치.

**명령어**:
```bash
cd ../01-1_회의비서_화자구분
pip3 install -r requirements.txt
```

> *기본 세팅*에서 사용한 폴더에서 시작하면 위 `cd` 한 줄로 진입.

**예상 결과** — 5~10분 동안 설치 진행:
```
Collecting pyannote.audio>=3.1.0 ...
Collecting torch ...
Successfully installed pyannote.audio-... torch-... python-dotenv-...
```

**흔한 오류 / 대처**:
- 다운로드 멈춤 → 같은 명령 재실행 (캐시 사용)
- `error: externally-managed-environment` (macOS 시스템 Python 보호)
  → `pip3 install --user -r requirements.txt` 또는 가상환경 사용
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- `Could not build wheels for ... portaudio`
  → `brew install portaudio` 후 재시도

**검증**:
```bash
python3 -c "import pyannote.audio; print('pyannote OK')"
python3 -c "import dotenv; print('dotenv OK')"
```
→ 두 줄 모두 `OK` 출력되면 정상

---

## 5. .env 파일 만들고 토큰 저장

**작업** — HF 토큰을 `.env` 파일에 저장. 코드에 직접 쓰지 않기.

**명령어**:
```bash
cp .env.example .env
open -e .env
```

> `open -e` 는 macOS 기본 *TextEdit* 으로 파일 열기. nano / vim 등 자기 편한 에디터 사용 OK.

TextEdit이 열리면 마지막 줄의 `hf_여기에_본인의_HuggingFace_Read_토큰_붙여넣기` 부분을 **2단계에서 복사한 실제 토큰**으로 교체:

```
HF_TOKEN=hf_여기에_복사한_실제_토큰_붙여넣기
```

**저장**: `⌘ + S` → TextEdit 닫기.

**예상 결과**: `.env` 파일이 폴더 안에 생성되고 본인 토큰이 들어있음.

**흔한 오류 / 대처**:
- TextEdit 이 *Rich Text(.rtf)* 로 저장하려 함
  → *Format* 메뉴 → **Make Plain Text** 선택 후 저장
- 토큰 앞뒤에 공백·따옴표 추가됨
  → `HF_TOKEN=hf_xxx` 형식 그대로 (공백 X, 따옴표 X)

**검증**:
```bash
cat .env
```
→ `HF_TOKEN=hf_xxx...` 한 줄이 정상 표시되면 OK

---

## 6. 텍스트 입력으로 빠른 검증 (모델 다운로드 없음)

**작업** — 환경 정상 여부 빠르게 확인. *이미 화자 표기된 텍스트*를 입력해 5초 만에 결과 확인.

**명령어**:
```bash
python3 run.py samples/sample_transcript.txt
```

**예상 결과**:
```
📥 입력: sample_transcript.txt
📄 텍스트 로드...
   ↳ 1,045자
🤖 Claude 요약 + 액션 추출...
🎨 HTML 렌더링 (화자별 색상)...
✅ 완료: output/2026...html
```
→ 기본 브라우저가 자동으로 열리고 *화자 3명(김부장/이대리/박과장)이 색상 다르게* 표시되는 HTML 리포트.

**흔한 오류 / 대처**:
- `claude CLI 호출 실패` → 기본 세팅의 *Claude Code 로그인* 미완료. `claude login` 재실행
- 브라우저 안 열림 → `output/` 폴더에 생성된 `.html` 파일을 더블 클릭

**검증**:
브라우저의 *회의 전문* 섹션을 펼쳤을 때 *김부장* / *이대리* / *박과장* 이름이 **서로 다른 색**으로 표시되면 OK

---

## 7. 마이크 녹음으로 실제 화자 분리 (★ 첫 실행 시 모델 다운로드 ~2GB)

**작업** — 진짜 음성에서 화자 자동 분리. 첫 실행은 모델 다운로드로 10~20분 걸림. 두 번째부터는 즉시.

**명령어**:
```bash
python3 run.py --record
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
🎤 입력 장치: 동엽의 AirPods Pro (또는 기본 마이크)
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
✅ 완료: output/...html
```

**흔한 오류 / 대처**:
- `HF_TOKEN 환경변수가 비어 있습니다` → `.env` 파일 5단계 재확인. 터미널 새 창
- `Access to model ... is restricted` → 3단계의 해당 모델 동의 누락. URL 다시 가서 *granted access* 확인
- `PortAudioError: Error opening InputStream`
  → 시스템 설정 → 개인정보 보호 및 보안 → 마이크 → 사용 중인 터미널 앱 (Terminal / iTerm2 / Cursor) **토글 ON** → ⌘+Q 후 재실행
- `objc[XXX]: Class AVFFrameReceiver is implemented in both ...` 경고
  → ffmpeg 중복 로드 경고. **정상**. 무시
- 모델 다운로드 중 멈춘 듯 보임 → 정상. ~10~20분. 인터넷 속도에 따라
- `AttributeError: 'DiarizeOutput' object has no attribute 'itertracks'`
  → `git pull origin main` 로 최신 코드 받기

**검증**:
브라우저에서 *회의 전문* 섹션 펼침 → `SPEAKER_00`, `SPEAKER_01` (혹은 더 많은 라벨) 이 *서로 다른 색*으로 표시되면 화자 분리 성공.

---

## 8. (선택) 두 번째 실행 — 모델 캐시 사용

**작업** — 첫 실행 후 두 번째부터는 모델이 캐시되어 *대기 시간 ~1분*.

**명령어**:
```bash
python3 run.py --record
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
objc[XXXXX]: Class AVFFrameReceiver is implemented in both
  .../site-packages/av/.dylibs/libavdevice.62.1.100.dylib
  /opt/homebrew/Cellar/ffmpeg/.../lib/libavdevice.62.3.101.dylib
```
→ macOS 한정. ffmpeg 중복 로드 경고. 동작 영향 없음.
→ 정 거슬리면: `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`

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

- 메인 세팅 가이드: `../세팅가이드_macOS.md`
- 기본 회의비서 (화자 구분 없는 버전): `../01_회의비서/`
- 강사 시연 흐름: `README.md` 의 *강의 시연 흐름* 섹션
