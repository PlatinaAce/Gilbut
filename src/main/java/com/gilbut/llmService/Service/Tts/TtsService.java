package com.gilbut.llmService.Service.Tts;

import com.fasterxml.jackson.core.JacksonException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsMessageDTO;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsStatusType;
import com.gilbut.llmService.Properties.TtsProperties;
import com.gilbut.llmService.WebSocketClient.Adapters.TtsWebSocketClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

@Slf4j
@Service
@RequiredArgsConstructor
public class TtsService {

    private final ObjectMapper objectMapper;
    private final TtsProperties rosProperties;
    private final TtsWebSocketClient client;

    // 비동기 연결 상태 추적
    private final AtomicBoolean connected = new AtomicBoolean(false);

    // 재연결 확인 플래그
    private final AtomicBoolean reconnecting = new AtomicBoolean(false);

    // 안정화 로직 관련
    private static final long MAX_RECONNECT_DELAY_MS = 60_000L;
    private static final long BASE_RECONNECT_DELAY_MS = 1000L;

    private final AtomicInteger reconnectAttempts = new AtomicInteger(0);

    // tryReconnection() 의 별도 스레드 동작 지원
    private final ExecutorService reconnectExecutor =
            Executors.newSingleThreadExecutor();

    @PreDestroy
    public void shutdown() {
        reconnectExecutor.shutdown();
    }

    @PostConstruct
    public void init() {
        // WebSocket 이벤트 처리
        client.setOnOpen(() -> {
            connected.set(true);
            reconnectAttempts.set(0);
            log.info("[TTS - TtsService] 연결 성공: {}", rosProperties.getUri());
        });
        client.setOnClose(code -> {
            connected.set(false);

            if (code == 1000) {
                log.info("[TTS - TtsService] 연결 종료");
                return;
            }

            log.warn("[TTS - TtsService] 비정상 종료 (Code: {}). 재연결 시도...", code);
            tryReconnectionAsync();
        });
        client.setOnError(ex -> {
            log.error("[TTS - TtsService] 연결 오류 발생", ex);
            connected.set(false);
        });

        try {
            // ROS 블로킹 연결
            this.client.connect();
        } catch (Exception e) {
            log.error("[TTS - TtsService] 초기 연결 실패... 재시도...", e);
            tryReconnectionAsync();
        }
    }

    public void send(TtsMessageDTO dto) {
        if (dto == null)
            return;

        if (!connected.get()) {
            log.warn("[TTS - TtsService] 연결 없음. 메시지 폐기");
            return;
        }

        try {
            String ttsJson = objectMapper.writeValueAsString(dto);
            client.send(ttsJson);
            log.info("[TTS - TtsService] 메시지 전송: {}", ttsJson);
        } catch (JacksonException e) {
            log.error("[TTS - TtsService] 메시지 전송 실패 >> Json 변환 실패", e);
        } catch (Exception e) {
            log.error("[TTS - TtsService] 메시지 전송 실패 >> 전송 오류", e);
        }
    }

    // ROS 연결 재시도 메서드
    private void tryReconnection() {
        // 현재
        if (!reconnecting.compareAndSet(false, true)) {
            return;
        }

        int attempt = reconnectAttempts.incrementAndGet();

        long exp = Math.min(attempt - 1, 10);
        long delay = Math.min(
                BASE_RECONNECT_DELAY_MS * (1L << exp),
                MAX_RECONNECT_DELAY_MS
        );

        log.warn("[TTS - TtsService] TTS 재연결 {}ms 후 {}회 시도", delay, attempt);

        try {
            Thread.sleep(delay);
            client.reconnect();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (Exception e) {
            log.error("[TTS - TtsService] 연결 재시도 실패", e);
        } finally {
            reconnecting.set(false);
        }
    }

    private void tryReconnectionAsync() {
        reconnectExecutor.submit(this::tryReconnection);
    }

    public void sendErrorMessageToTts() {
        // 오류 메시지 송신
        TtsMessageDTO ttsMessageDTO = new TtsMessageDTO(TtsStatusType.ERROR, "오류가 발생했어요. 다시 말씀해주세요.");
        this.send(ttsMessageDTO);
    }

    public boolean isConnected() {
        return connected.get();
    }

    // 테스트용 메서드
    public void setConnected(boolean connected) {
        this.connected.set(connected);
    }

    public void onConnectionLost(int code) {
        connected.set(false);

        if (code != 1000)
            tryReconnectionAsync();
    }
}
