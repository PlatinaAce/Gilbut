package com.gilbut.llmService.Service.TtsServiceTests;

/*
 * TtsService 의 Mocking 기반 유닛 테스트
 */

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsMessageDTO;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsStatusType;
import com.gilbut.llmService.Log.LoggingTestExecutionOrderExtension;
import com.gilbut.llmService.Properties.TtsProperties;
import com.gilbut.llmService.Service.Tts.TtsService;
import com.gilbut.llmService.WebSocketClient.Adapters.TtsWebSocketClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import static org.mockito.Mockito.*;

@TestMethodOrder(MethodOrderer.Random.class)
@ActiveProfiles("test")
@ExtendWith({
        LoggingTestExecutionOrderExtension.class,
        MockitoExtension.class
})
@Transactional
public class TtsServiceTest {
    @Mock
    private TtsWebSocketClient client;

    @Mock
    private TtsProperties ttsProperties;

    @Spy
    private ObjectMapper objectMapper = new ObjectMapper();

    @InjectMocks
    private TtsService ttsService;

    @BeforeEach
    void setUp() throws Exception {
        lenient().when(ttsProperties.getUri()).thenReturn("ws://localhost:7070/tts");
    }

    @Test
    void send_whenClientOpen_test() throws Exception {
        // given
        doNothing().when(client).connect();

        // 초기 연결
        ttsService.init();
        ttsService.setConnected(true);

        TtsMessageDTO ttsDTO = new TtsMessageDTO();
        ttsDTO.setStatus(TtsStatusType.SUCCESS);

        // when
        ttsService.send(ttsDTO);

        // then
        verify(client, times(1)).send(anyString());
        verify(client, never()).reconnect();
    }

    @Test
    void send_initConnectFail_test() throws Exception {
        // given
        // 초기 connect 실패
        doThrow(new RuntimeException()).when(client).connect();

        // 이후의 reconnect 성공
        doNothing().when(client).reconnect();

        // when
        ttsService.init();

        // 비동기 재연결 대기
        Thread.sleep(1200);

        // then
        verify(client, times(1)).connect();
    }

    @Test
    void send_connectFail_test() throws Exception {
        // given
        doNothing().when(client).connect();
        doNothing().when(client).reconnect();

        ttsService.init();
        ttsService.setConnected(true);

        // send 과정에서 오류 발생 >> 연결 끊김
        doThrow(new RuntimeException("[MOCK] send() 실패")).when(client).send(anyString());

        TtsMessageDTO ttsDTO = new TtsMessageDTO();
        ttsDTO.setStatus(TtsStatusType.SUCCESS);

        // when
        ttsService.send(ttsDTO);
        ttsService.onConnectionLost(1006);

        // 비동기 재연결 대기
        Thread.sleep(1200);

        // then
        verify(client, times(1)).send(anyString());
        verify(client, atLeastOnce()).reconnect();
    }
}
