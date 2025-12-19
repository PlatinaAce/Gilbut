package com.gilbut.llmService.Service;

import com.gilbut.llmService.DTO.LlmMessageDTO.*;
import com.gilbut.llmService.DTO.RosMessageDTO.RosMessageDTO;
import com.gilbut.llmService.DTO.SttMessageDTO.SttMessageDTO;
import com.gilbut.llmService.DTO.SttMessageDTO.SttStatusType;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsMessageDTO;
import com.gilbut.llmService.DTO.TtsMessageDTO.TtsStatusType;
import com.gilbut.llmService.Domain.Location;
import com.gilbut.llmService.Service.Tts.PronunciationResolver;
import com.gilbut.llmService.Service.Tts.TtsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;

/*
 * 서비스들의 동작 분기 결정하는 오케스트레이션 서비스
 * 핸들러가 사용한다.
 *
 * 다음과 같은 기능을 수행
 * 1. 텍스트를 LLM 처리
 * 2. LLM 처리한 데이터를 타입에 따라 ROS, TTS 로 응답
 * 3. 예외 발생시 ROS, TTS 로 오류 메시지 전송
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class SttOrchestrationService {
    private final RosService rosService;
    private final TtsService ttsService;
    private final GeminiService geminiService;
    private final LocationService locationService;
    private final HintService hintService;
    private final PronunciationResolver pronunciationResolver;

    public void handle(SttMessageDTO sttMessageDTO) {
        // STT 서버로부터 ERROR 가 온 경우
        if (sttMessageDTO.getStatus() == SttStatusType.ERROR) {
            log.info("[STT - SttOrchestrationService] STT 서버의 ERROR 요청 수신");
            return;
        }

        String userPrompt = sttMessageDTO.getText();

        // LLM 처리
        Optional<LlmMessageDTO> llmMsgOptional = geminiService.ask(userPrompt);

        if (llmMsgOptional.isEmpty()) {
            // 오류 메시지 송신
            rosService.sendErrorMessageToROS();
            ttsService.sendErrorMessageToTts();
            return;
        }

        // geminiService.ask() 가 정상 동작했다면
        LlmMessageDTO llmMessageDTO = llmMsgOptional.get();

        log.info("[HANDLER - SttOrchestrationService] LLM 메시지 수신: {}", llmMessageDTO.toString());

        RosMessageDTO rosMessageDTO = null;
        TtsMessageDTO ttsMessageDTO = null;
        String locationCode = null;

        // NAVIGATION_EXACT 처리
        if (llmMessageDTO instanceof NavigationExactDTO navExactDTO) {
            locationCode = navExactDTO.getLocationCode();
            rosMessageDTO = locationService.getROSMessageDTO(locationCode);

            // TTS 처리
            ttsMessageDTO = new TtsMessageDTO(TtsStatusType.SUCCESS, navExactDTO.getMessage());
        }
        // NAVIGATION_DESCRIBE 처리
        else if (llmMessageDTO instanceof NavigationDescribeDTO navDescribeDTO) {
            Optional<Location> optionalLocation = hintService.inferLocation(navDescribeDTO);
            if (optionalLocation.isPresent()) {// 묘사의 대상을 선정했다면
                Location location = optionalLocation.get();
                locationCode = location.getLocationCode();
                rosMessageDTO = locationService.getROSMessageDTO(locationCode);

                // TTS 처리
                ttsMessageDTO = new TtsMessageDTO(TtsStatusType.SUCCESS, "말씀하신 장소는 " + pronunciationResolver.resolve(location.getLocationCode()) + "인 것 같아요. 안내를 시작할게요.");
            } else {// 묘사의 대상을 제대로 선정하지 못했다면
                // TTS 처리
                ttsMessageDTO = new TtsMessageDTO(TtsStatusType.SUCCESS, "말씀하신 장소가 어디인지 잘 모르겠어요. 다시 말씀해주세요.");
            }
        }
        // CHAT 처리
        else if (llmMessageDTO instanceof ChatDTO chatDTO) {
            // TTS 처리
            ttsMessageDTO = new TtsMessageDTO(TtsStatusType.SUCCESS, chatDTO.getMessage());
        }
        // ERROR 처리
        else if (llmMessageDTO instanceof ErrorDTO errorDTO){
            // TTS 처리
            ttsMessageDTO = new TtsMessageDTO(TtsStatusType.SUCCESS, errorDTO.getMessage());
        }

        // NAVIGATION_EXACT | NAVIGATION_DESCRIBE 요청이라면 ROS 로 메시지 송신 (RosStatusType == ERROR 도 송신)
        if (rosMessageDTO != null) {
            if (locationCode != null) {
                log.info("[HANDLER - SttOrchestrationService] 장소 코드: {}의 정보를 ROS 로 전송합니다.", locationCode);
            }
            rosService.send(rosMessageDTO);
        }

        // TTS 송신
        if (ttsMessageDTO != null) {
            log.info("[HANDLER - SttOrchestrationService] TTS 메시지를 전송합니다.");
            ttsService.send(ttsMessageDTO);
        }
    }
}
