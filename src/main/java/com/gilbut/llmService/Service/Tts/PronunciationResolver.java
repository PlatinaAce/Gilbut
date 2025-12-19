package com.gilbut.llmService.Service.Tts;

import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class PronunciationResolver {
    private static final Map<String, String> MAP = Map.of(
            "AI_HALL", "AI공학관",
            "VISION_TOWER", "비전타워",
            "GACHON_HALL", "가천관",
            "MAIN_LIBRARY", "중앙도서관",
            "GLOBAL_CENTER", "글로벌센터"
    );

    public String resolve(String locationCode) {
        return MAP.getOrDefault(locationCode, "디폴트 장소");
    }
}
