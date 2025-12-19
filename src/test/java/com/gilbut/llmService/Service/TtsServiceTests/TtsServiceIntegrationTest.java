package com.gilbut.llmService.Service.TtsServiceTests;

import com.gilbut.llmService.DTO.TtsMessageDTO.TtsMessageDTO;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsStatusType;
import com.gilbut.llmService.Service.Tts.TtsService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

/*
 * TtsService 의 실제 서버 기반의 통합 테스트
 *
 * !!!!! 반드시 아래의 방법을 준수 !!!!!
 *
 * 테스트 방법
 * 1. SimpleTestServer 를 따로 실행한다.
 * 2. TtsIntegrationTest 를 테스트한다.
 * 3. SimpleTestServer 에 전송한 DTO 관련 정보가 출력되는 것을 확인한다.
 * 4. 만약, 테스트가 실패한다면, Thread.sleep(2000) 으로 변경
 */
@SpringBootTest
@ActiveProfiles("test")
public class TtsServiceIntegrationTest {
    @Autowired
    private TtsService ttsService;

    @Test
    void send_realWebSocketServer_test() throws Exception {

        TtsMessageDTO ttsDTO =
                new TtsMessageDTO(TtsStatusType.SUCCESS, "이건 테스트용 메시지입니다!");

        ttsService.setConnected(true);
        ttsService.send(ttsDTO);

        Thread.sleep(1000);

        assertTrue(true);
    }
}
