#!/usr/bin/env python3
"""
회의 비서 (화자 구분 버전) — 음성/텍스트 → 화자별 HTML 리포트

기본 회의비서(`01_회의비서/`)와의 차이:
  - pyannote.audio로 화자 분리 (SPEAKER_00, SPEAKER_01, ...)
  - HTML 리포트에 화자별 색상 표시
  - HF_TOKEN 환경변수 또는 .env 파일 필요

Usage:
  python run.py --record                       # 마이크 녹음 (Enter로 종료) → 전사 → 요약
  python run.py samples/meeting.m4a            # 기존 오디오 파일 → 화자 분리 → 요약
  python run.py samples/sample_transcript.txt  # 텍스트 파일 (화자 표기 있으면 그대로 사용)
"""
import sys
import os
import json
import re
import html
import shutil
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

# Windows 콘솔 한글·이모지 깨짐 방지
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Windows에서는 claude가 claude.cmd로 등록 → subprocess 호출에 shell=True 필요
_USE_SHELL = sys.platform.startswith("win")

# .env 파일에서 환경변수 로드 (HF_TOKEN 등)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

ROOT = Path(__file__).parent
PROMPT_FILE = ROOT / "prompts" / "summarize.md"
TEMPLATE_FILE = ROOT / "templates" / "report.html"
OUTDIR = ROOT / "output"
OUTDIR.mkdir(exist_ok=True)


def record_audio() -> Path:
    """기본 마이크에서 16kHz 모노 WAV 녹음. Enter 또는 Ctrl+C로 종료."""
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
    except ImportError:
        sys.exit("❌ 의존성 미설치: pip install sounddevice soundfile numpy")

    samplerate = 16000
    channels = 1

    try:
        info = sd.query_devices(kind="input")
        print(f"🎤 입력 장치: {info['name']}")
    except Exception:
        print("🎤 입력 장치: (기본)")

    print("🔴 녹음 시작 — Enter 또는 Ctrl+C로 종료")
    chunks: list = []

    def callback(indata, frames, time_info, status):
        if status:
            print(f"⚠  {status}", file=sys.stderr)
        chunks.append(indata.copy())

    started = datetime.now()
    stream = sd.InputStream(
        samplerate=samplerate, channels=channels, dtype="float32", callback=callback
    )
    with stream:
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

    duration = (datetime.now() - started).total_seconds()
    if not chunks:
        sys.exit("❌ 녹음된 데이터 없음")

    audio = np.concatenate(chunks, axis=0)
    samples_dir = ROOT / "samples"
    samples_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = samples_dir / f"recording_{ts}.wav"
    sf.write(str(out), audio, samplerate)
    print(f"✅ 녹음 완료: {duration:.1f}초 · {out.stat().st_size/1024:.0f} KB · {out.name}")
    return out


def transcribe(src: Path) -> str:
    """텍스트면 그대로, 오디오면 화자 분리 + 전사 후 화자별로 라벨링."""
    if src.suffix.lower() in {".txt", ".md"}:
        return src.read_text(encoding="utf-8")

    # 1. HF_TOKEN 점검 (pyannote 모델 다운로드용)
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not hf_token:
        sys.exit(
            "❌ HF_TOKEN 환경변수가 비어 있습니다.\n"
            "   1) https://huggingface.co/settings/tokens 에서 Read 토큰 발급\n"
            "   2) 다음 3개 모델 페이지에서 모두 Agree and access:\n"
            "      - https://huggingface.co/pyannote/speaker-diarization-3.1\n"
            "      - https://huggingface.co/pyannote/segmentation-3.0\n"
            "      - https://huggingface.co/pyannote/speaker-diarization-community-1 (임베딩, 새 버전)\n"
            "   3) .env 파일 (이 폴더 안)에 HF_TOKEN=hf_xxx... 저장 후 재실행"
        )

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("❌ faster-whisper 미설치. `pip install faster-whisper` 먼저.")
    try:
        from pyannote.audio import Pipeline
    except ImportError:
        sys.exit("❌ pyannote.audio 미설치. `pip install pyannote.audio` 먼저.")

    # 2. faster-whisper로 전사
    print("   ↳ Whisper 모델 로딩 (small, int8 CPU)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(src), language="ko", vad_filter=True
    )
    whisper_segments = [
        {"start": s.start, "end": s.end, "text": s.text.strip()}
        for s in segments if s.text.strip()
    ]
    print(f"   ↳ 전사 세그먼트 {len(whisper_segments)}개")

    # 3. pyannote로 화자 분리
    print("   ↳ pyannote 화자 분리 중 (첫 실행은 ~1.5GB 모델 다운로드)...")
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token,
        )
    except Exception as e:
        sys.exit(
            f"❌ pyannote 모델 로드 실패: {e}\n"
            "   다음 3개를 모두 확인하세요:\n"
            "   - HF_TOKEN 이 유효한 Read 토큰인지\n"
            "   - https://huggingface.co/pyannote/speaker-diarization-3.1 (메인)\n"
            "   - https://huggingface.co/pyannote/segmentation-3.0 (세그먼테이션)\n"
            "   - https://huggingface.co/pyannote/speaker-diarization-community-1 (임베딩, 새 버전)\n"
            "   각 페이지에서 'You have been granted access' 표시 확인"
        )
    diarization = pipeline(str(src))

    speaker_turns = [
        {"start": turn.start, "end": turn.end, "speaker": speaker}
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]
    speakers = sorted(set(t["speaker"] for t in speaker_turns))
    print(f"   ↳ 화자 {len(speakers)}명 감지: {', '.join(speakers)}")

    # 4. 병합 — Whisper 세그먼트마다 가장 많이 겹치는 화자 매칭
    lines = []
    for ws in whisper_segments:
        best_speaker = "UNKNOWN"
        best_overlap = 0.0
        for st in speaker_turns:
            overlap = min(ws["end"], st["end"]) - max(ws["start"], st["start"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = st["speaker"]
        lines.append(f"{best_speaker}: {ws['text']}")

    return "\n".join(lines)


def summarize(transcript: str) -> dict:
    """Claude Code CLI로 요약 + 액션 추출. 화자 라벨이 있으면 owner 추론에 사용."""
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    full = f"{prompt}\n\n[회의 전문 — 화자 라벨 포함 가능]\n{transcript}"

    proc = subprocess.run(
        ["claude", "-p", full, "--output-format", "json"],
        capture_output=True,
        text=True,
        shell=_USE_SHELL,
    )
    if proc.returncode != 0:
        sys.exit(f"❌ claude CLI 호출 실패:\n{proc.stderr}")

    raw = json.loads(proc.stdout).get("result", "")
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        sys.exit(f"❌ JSON 블록을 찾지 못함:\n{raw}")
    return json.loads(match.group(0))


def render(data: dict, transcript: str) -> Path:
    """HTML 렌더링 — 화자별 색상 적용."""
    tpl = TEMPLATE_FILE.read_text(encoding="utf-8")

    def esc(s):
        return html.escape(str(s)) if s else ""

    title = esc(data.get("title") or "회의 요약")
    date = esc(data.get("date") or datetime.now().strftime("%Y-%m-%d"))
    summary = esc(data.get("summary") or "").replace("\n", "<br>")

    actions = data.get("actions") or []
    if actions:
        rows = "".join(
            f'<li>'
            f'<span class="who">{esc(a.get("owner") or "TBD")}</span>'
            f'<span class="what">{esc(a.get("task") or "")}</span>'
            f'<span class="due">{esc(a.get("due") or "")}</span>'
            f'</li>'
            for a in actions
        )
        actions_block = f'<ul class="actions">{rows}</ul>'
    else:
        actions_block = '<div class="empty">액션 아이템 없음</div>'

    def list_block(items):
        items = items or []
        if not items:
            return '<div class="empty">해당 사항 없음</div>'
        lis = "".join(f"<li>{esc(x)}</li>" for x in items)
        return f'<ul class="list">{lis}</ul>'

    decisions_block = list_block(data.get("decisions"))
    risks_block = list_block(data.get("risks"))

    # 화자 라벨에 색상 매핑 (전문 표시용)
    speaker_colors = ["#7A2E2E", "#1F4E79", "#3C7A3C", "#7A5C1F", "#5C2E7A", "#7A2E5C"]
    speaker_map: dict = {}
    transcript_html_lines = []
    for raw_line in transcript.split("\n"):
        if not raw_line.strip():
            continue
        m = re.match(r"^([A-Za-z가-힣_0-9]+(?:\s*\([가-힣A-Za-z]+\))?)\s*:\s*(.+)$", raw_line)
        if m:
            speaker, text = m.group(1).strip(), m.group(2).strip()
            if speaker not in speaker_map:
                speaker_map[speaker] = speaker_colors[len(speaker_map) % len(speaker_colors)]
            color = speaker_map[speaker]
            transcript_html_lines.append(
                f'<div class="t-line"><span class="t-speaker" style="color:{color}; font-weight:700">{esc(speaker)}</span>'
                f' <span class="t-text">{esc(text)}</span></div>'
            )
        else:
            transcript_html_lines.append(f'<div class="t-line"><span class="t-text">{esc(raw_line)}</span></div>')
    transcript_block = "\n".join(transcript_html_lines)

    rendered = tpl.format(
        title=title,
        date=date,
        summary=summary,
        actions_block=actions_block,
        decisions_block=decisions_block,
        risks_block=risks_block,
        transcript=transcript_block,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^\w가-힣]+", "_", title)[:30] or "report"
    out = OUTDIR / f"{ts}_{safe}.html"
    out.write_text(rendered, encoding="utf-8")
    return out


def open_in_browser(path: Path) -> None:
    """한글·공백 포함 경로도 안전하게 기본 브라우저로 오픈."""
    resolved = path.resolve()
    if sys.platform == "darwin" and shutil.which("open"):
        subprocess.run(["open", str(resolved)], check=False)
        return
    if sys.platform.startswith("win"):
        os.startfile(str(resolved))  # type: ignore[attr-defined]
        return
    url = "file://" + quote(str(resolved))
    webbrowser.open(url)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run.py --record")
        print("  python run.py <audio.mp3 | transcript.txt>")
        sys.exit(1)

    if sys.argv[1] in {"--record", "-r", "record"}:
        src = record_audio()
    else:
        src = Path(sys.argv[1])
        if not src.exists():
            sys.exit(f"❌ 파일 없음: {src}")

    print(f"📥 입력: {src.name}")
    print(
        "📝 전사 + 화자 분리..."
        if src.suffix.lower() not in {".txt", ".md"}
        else "📄 텍스트 로드..."
    )
    transcript = transcribe(src)
    print(f"   ↳ {len(transcript):,}자")

    print("🤖 Claude 요약 + 액션 추출...")
    data = summarize(transcript)

    print("🎨 HTML 렌더링 (화자별 색상)...")
    out = render(data, transcript)
    print(f"✅ 완료: {out}")

    open_in_browser(out)


if __name__ == "__main__":
    main()
