package com.gilbut.llmService.Service;

/*
 * SttOrchestrationService 의 Mocking 기반 유닛 테스트
 */

import com.gilbut.llmService.DTO.LlmMessageDTO.NavigationDescribeDTO;
import com.gilbut.llmService.DTO.LlmMessageDTO.NavigationExactDTO;
import com.gilbut.llmService.DTO.RosMessageDTO.RosMessageDTO;
import com.gilbut.llmService.DTO.SttMessageDTO.SttMessageDTO;
import com.gilbut.llmService.DTO.SttMessageDTO.SttStatusType;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsMessageDTO;
import com.gilbut.llmService.Domain.Location;
import com.gilbut.llmService.Log.LoggingTestExecutionOrderExtension;
import com.gilbut.llmService.Service.Tts.PronunciationResolver;
import com.gilbut.llmService.Service.Tts.TtsService;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.context.ActiveProfiles;

import java.util.*;

import static org.mockito.Mockito.*;

@TestMethodOrder(MethodOrderer.Random.class)
@ActiveProfiles("test")
@ExtendWith({
        LoggingTestExecutionOrderExtension.class,
        MockitoExtension.class
})
public class SttOrchestrationServiceTest {
    @Mock
    RosService rosService;

    @Mock
    TtsService ttsService;

    @Mock
    GeminiService geminiService;

    @Mock
    LocationService locationService;

    @Mock
    HintService hintService;

    @Mock
    PronunciationResolver pronunciationResolver;

    @InjectMocks
    SttOrchestrationService sttOrchestrationService;

    @Test
    void handle_sttERROR_test() {
        // given
        SttMessageDTO sttMessageDTO = new SttMessageDTO();
        sttMessageDTO.setStatus(SttStatusType.ERROR);

        // when
        sttOrchestrationService.handle(sttMessageDTO);

        // then
        verifyNoInteractions(
                geminiService,
                rosService,
                ttsService,
                locationService,
                hintService
        );
    }

    @Test
    void handle_llmError_test() {
        // given
        SttMessageDTO sttMessageDTO = new SttMessageDTO();
        sttMessageDTO.setStatus(SttStatusType.SUCCESS);
        sttMessageDTO.setText("가천관으로 가고 싶어");

        when(geminiService.ask(anyString())).thenReturn(Optional.empty());

        // when
        sttOrchestrationService.handle(sttMessageDTO);

        // then
        verify(rosService).sendErrorMessageToROS();
        verify(ttsService).sendErrorMessageToTts();
        verifyNoMoreInteractions(rosService, ttsService);
    }

    @Test
    void handle_navigationExact_test() {
        // given
        SttMessageDTO sttMessageDTO = new SttMessageDTO();
        sttMessageDTO.setStatus(SttStatusType.SUCCESS);
        sttMessageDTO.setText("가천관으로 가고 싶어");

        NavigationExactDTO llmMessageDTO = new NavigationExactDTO("GACHON_HALL", "가천관으로 안내하겠습니다.");

        when(geminiService.ask(anyString())).thenReturn(Optional.of(llmMessageDTO));

        RosMessageDTO rosMessageDTO = new RosMessageDTO();
        when(locationService.getROSMessageDTO("GACHON_HALL")).thenReturn(rosMessageDTO);

        // when
        sttOrchestrationService.handle(sttMessageDTO);

        // then
        verify(rosService).send(rosMessageDTO);
        verify(ttsService).send(any(TtsMessageDTO.class));
    }

    @Test
    void handle_navigationDescribe_test() {
        // given
        SttMessageDTO sttMessageDTO = new SttMessageDTO();
        sttMessageDTO.setStatus(SttStatusType.SUCCESS);
        sttMessageDTO.setText("교내에 스타버스가 있다고 들었는데, 어디야?");

        NavigationDescribeDTO llmMessageDTO =
                new NavigationDescribeDTO("말씀하신 내용을 기반으로 추론해볼게요!", null, null);

        when(geminiService.ask(anyString())).thenReturn(Optional.of(llmMessageDTO));

        Location location = new Location(null, "VISION_TOWER", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);

        when(hintService.inferLocation(llmMessageDTO)).thenReturn(Optional.of(location));

        when(locationService.getROSMessageDTO("VISION_TOWER")).thenReturn(new RosMessageDTO());

        when(pronunciationResolver.resolve("VISION_TOWER")).thenReturn("비전타워");

        // when
        sttOrchestrationService.handle(sttMessageDTO);

        // then
        verify(rosService).send(any());
        verify(ttsService).send(any());
    }
}
