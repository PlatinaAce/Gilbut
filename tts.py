import os
import json
import tempfile
import websocket
from gtts import gTTS
from playsound import playsound

# playsound 1.2.2 

WS_URL = "" 


def tts_and_play(text : str):
    tts = gTTS(text=text, lang="ko")

    # 임시 mp3 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp: 
        tmp_path = fp.name
        tts.write_to_fp(fp)

    print("[INFO] 생성된 음성 파일 :", tmp_path)

    try:
        playsound(tmp_path, block=True)
    except Exception as e:
        print("[ERROR] 음성 재생 중 오류 :",e)
    finally: # 재생이 끝나면 임시파일 삭제
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def on_message(ws, message: str):
    print(f"[WEBSOCKET] 수신 메시지(JSON) : {message}")

    try:
        data = json.loads(message)
    except Exception as e:
        print(f"[ERROR] JSON 파싱 실패 : {e}")
        return

    text = data.get("text")
    if not text:
        print("[INFO] text가 비어있거나 없음")
        return

    tts_and_play(text)


def on_error(ws, error):
    print(f"[WEBSOCKET] 에러 발생 : {error}")


def on_close(ws, close_status_code, close_msg):
    print(f"[WEBSOCKET] 연결 종료 : code = {close_status_code}, msg = {close_msg}")


def on_open(ws):
    print("[WEBSOCKET] 서버와 WebSocket 연결 완료")


def main():
    print("[INFO] Spring boot 통신 시작!!")

    websocket.enableTrace(False)

    ws_app = websocket.WebSocketApp(
        WS_URL,
        on_open = on_open,
        on_message = on_message,
        on_error = on_error,
        on_close = on_close,
    )

    try:
        ws_app.run_forever()
    except KeyboardInterrupt:
        print("\n[INFO] 종료 요청")


if __name__ == "__main__":
    main()