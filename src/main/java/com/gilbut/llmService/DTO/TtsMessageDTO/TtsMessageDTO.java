package com.gilbut.llmService.DTO.TtsMessageDTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TtsMessageDTO {
    private TtsStatusType status;
    private String tts_message;
    private long time = System.currentTimeMillis();

    public TtsMessageDTO(TtsStatusType status, String tts_message) {
        this.status = status;
        this.tts_message = tts_message;
        this.time = System.currentTimeMillis();
    }
}
