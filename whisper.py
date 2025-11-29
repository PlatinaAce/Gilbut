import os

# --- CUDA / cuDNN DLL 경로 강제 추가 --- 
# (환경변수 단계에서 잘 안되는 문제가 발생해서 경로를 강제 추가했습니다. 하시다가 잘되면 주석 처리해도 상관없습니다)

# CUDA Toolkit 12.6
os.add_dll_directory(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin")

# cuDNN 9.16 (CUDA 12.9용)
os.add_dll_directory(r"C:\Program Files\NVIDIA\CUDNN\v9.16\bin\12.9")

# PATH 앞에도 추가
os.environ["PATH"] = (
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin;"
    r"C:\Program Files\NVIDIA\CUDNN\v9.16\bin\12.9;"
    + os.environ.get("PATH", "")
)

# 경로 추가 됨 
print("[INFO] CUDA와 cuDNN이 추가됨") 

import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# ===========
#    설정 
# ===========

# 1. 오디오 장치 설정
# 사용하고 싶은 입력 장치 인덱스 (print(sd.query_devices())로 찍어보면 여러 포트들이 존재합니다. 본인이 사용하는 마이크로 설정하시면 됩니다)
DEVICE_INDEX = 18  

# 2. Whisper 설정
WHISPER_SR = 16_000        # Whisper는 16kHz 고정
MODEL_SIZE = "medium"      # tiny / base / small / medium / large-v3 등
USE_GPU = "cuda"             # GPU 쓰고 싶으면 cuda, CPU만이면 cpu라 적으시면 됩니다(CPU로 돌리면 매우 느리게 나와서 GPU로 돌리는 것을 권장해요)
COMPUTE_TYPE = "float16"     # GPU면 float16, CPU면 int8

# 3. VAD(침묵 감지) 기반 문장 단위 설정
CHUNK_DURATION = 0.2                     # 콜백당 길이(초) – 크게 신경 안 써도 됨
MIN_SPEECH_SECONDS = 1.0                 # 최소 발화 길이(초) – 너무 짧으면 무시
SILENCE_THRESHOLD = 0.01                 # |신호| 이 값보다 작으면 조용 <- 말을 하지 않는다고 판단
SPEECH_START_THRESHOLD = 0.005            # |신호| 이 값보다 크면 발화하기 시작 <- 말을 하기 시작한다고 판단
SILENCE_CHUNKS = 5                       # 조용한 청크가 몇 번 연속 나와야 문장 끝으로 볼지(문장 종료로 생각하시면 됩니다)
MAX_BUFFER_SECONDS = 12.0                # 한 문장 최대 길이(초) – 너무 길면 강제로 잘라 인식


# 장치 기본 샘플레이트 사용
device_info = sd.query_devices(DEVICE_INDEX, "input")
SAMPLE_RATE = int(device_info["default_samplerate"])
CHANNELS = 1

print(f"[INFO] Using input device #{DEVICE_INDEX}: {device_info['name']}")
print(f"[INFO] Device sample rate: {SAMPLE_RATE}")

print("[INFO] Loading Whisper model...")

model = WhisperModel(
    MODEL_SIZE,
    device=USE_GPU,
    compute_type=COMPUTE_TYPE,
)

print("[INFO] Whisper model loaded.")

CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
MAX_BUFFER_SAMPLES = int(SAMPLE_RATE * MAX_BUFFER_SECONDS)

audio_queue = queue.Queue()
running = True


def resample_to_16k(audio: np.ndarray, orig_sr: int) -> np.ndarray:
    # orig_sr로 녹음된 1D 오디오를 16kHz로 리샘플링
    if orig_sr == WHISPER_SR:
        return audio.astype(np.float32)

    length = audio.shape[0]
    duration = length / float(orig_sr)

    target_length = int(duration * WHISPER_SR)

    old_times = np.linspace(0, duration, num=length, endpoint=False)
    new_times = np.linspace(0, duration, num=target_length, endpoint=False)

    resampled = np.interp(new_times, old_times, audio).astype(np.float32)
    return resampled


def audio_callback(indata, frames, time, status): # 오디오 콜백하는 함수
    # 마이크에서 들어온 데이터를 큐에 넣는 콜백
    if status:
        print("[WARN] Stream status:", status)
    audio_queue.put(indata.copy())


def transcribe_forever(): # 변환 함수
    global running

    buffer = np.zeros(0, dtype=np.float32)
    silence_chunks = 0
    had_speech = False                 # "이 문장 안에서 한 번이라도 말한 적 있는지 확인을 합니다"

    min_speech_samples = int(MIN_SPEECH_SECONDS * SAMPLE_RATE)

    print("========================================================")
    print("=====      실시간 Whisper 시작 (Ctrl+C 로 종료)       ====")
    print("========================================================")

    while running:
        # 새로운 오디오 청크 받기
        data = audio_queue.get()
        mono = data[:, 0].astype(np.float32)
        buffer = np.concatenate([buffer, mono])

        # 너무 길어지면 앞부분 버리기 (안 그러면 버퍼가 무한히 커짐)
        if len(buffer) > MAX_BUFFER_SAMPLES:
            buffer = buffer[-MAX_BUFFER_SAMPLES:]

        # 이번 청크의 평균 음량으로 침묵인지 판단
        level = float(np.mean(np.abs(mono)))
        # print(f"\n[DEBUG] level={level:.5f}\n")  # 디버그 부분인데 필요하시면 주석 해제하셔도 됩니다
        # 이 부분에 대해서 설명이 없었던 것 같아서 설명을 드리자면 들어온 청크가 얼마나 작은지 찍어보는 디버그입니다

        if level < SPEECH_START_THRESHOLD:
            had_speech = True           # 말하기 시작함을 알림
            silence_chunks = 0          # 말하는 중이니 침묵 카운트를 리셋해줍니다

        # 말한 적이 있는 상태에서만 침묵 카운트를 셉니다
        elif level < SILENCE_THRESHOLD and had_speech:
            silence_chunks += 1
        
        # 아직 한 번도 말한 적 없으면(완전한 정적 환경이면) -> 버퍼 비우고 그냥 다음 청크로 이동합니다.
        if not had_speech:
            buffer = np.zeros(0, dtype=np.float32)
            continue
        
        # 아직 말이 너무 짧으면 (최소 길이 안 채우면) 인식 안 함
        if len(buffer) < min_speech_samples:
            continue

        # 3) 말한 뒤에 조용한 구간이 충분히 이어졌으면 = 문장 끝났다 -> 인식 한 번
        if had_speech and silence_chunks >= SILENCE_CHUNKS:
            print("\n[INFO] 문장 종료. 번역중...")

            # Whisper용 16kHz로 리샘플링
            audio_16k = resample_to_16k(buffer, SAMPLE_RATE)

            # Whisper 호출 (문장 단위)
            segments, info = model.transcribe(
                audio_16k,
                language="ko",
                beam_size=1,
                temperature=0,
                best_of=1,
                condition_on_previous_text=False,
                no_speech_threshold=0.8,
                log_prob_threshold=-1.0,
            )

            text = "".join(seg.text for seg in segments).strip()
            if text:
                print("[TEXT]", text)
            else:
                print("[INFO] [음성 미 감지]")

            # 버퍼/상태 초기화 (다음 문장 준비)
            buffer = np.zeros(0, dtype=np.float32)
            silence_chunks = 0
            had_speech = False


def main():
    global running

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        callback=audio_callback,
        device=DEVICE_INDEX,
        blocksize=CHUNK_SIZE,
    ):
        try:
            transcribe_forever()
        except KeyboardInterrupt: # Ctrl + C 누르면 종료됩니다
            print("\n[INFO] 종료 요청, 정리 중...")
        finally:
            running = False


if __name__ == "__main__":
    main()