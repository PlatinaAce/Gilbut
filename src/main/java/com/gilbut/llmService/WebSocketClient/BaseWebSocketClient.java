package com.gilbut.llmService.WebSocketClient;

import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.util.function.Consumer;

/*
 * ROS 에 응답을 보내기 위한 '웹 소켓 클라이언트'
 * ROS 와의 통신을 위해 'Java-WebSocket' dependency 를 사용
 */

@Slf4j
public abstract class BaseWebSocketClient extends WebSocketClient {

    private Runnable onOpenCallback = () -> {};
    private Consumer<Integer> onCloseCallback = code -> {};
    private Consumer<Exception> onErrorCallback = ex -> {};

    public BaseWebSocketClient(URI serverUri) {
        super(serverUri);
    }

    @Override
    public void onOpen(ServerHandshake handshakedata) {
        onOpenCallback.run();
    }

    @Override
    public void onMessage(String message) {
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        // reason 이 UTF-8 로 오지 않으면 로그가 깨지는 현상이 있음. 주의
        onCloseCallback.accept(code);
    }

    @Override
    public void onError(Exception ex) {
        ex.printStackTrace();
        onErrorCallback.accept(ex);
    }

    // 이벤트 등록 메서드
    public void setOnOpen(Runnable callback) {
        this.onOpenCallback = callback;
    }
    public void setOnClose(Consumer<Integer> callback) {
        this.onCloseCallback = callback;
    }
    public void setOnError(Consumer<Exception> callback) {
        this.onErrorCallback = callback;
    }
}
