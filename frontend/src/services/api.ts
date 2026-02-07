// src/services/api.ts
import axios from 'axios';

const API_BASE = '/api/v1/audio'; // O Vite fará o proxy para o localhost:8000

export const api = {
  // Envia áudio bruto para transcrição (STT)
  async transcribe(audioBlob: Blob): Promise<string> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'user_voice.wav');
    const response = await axios.post(`${API_BASE}/transcribe`, formData);
    return response.data.text;
  },

  // Gera o áudio da resposta da IA (TTS)
  async getSpeechUrl(text: string): Promise<string> {
    const response = await axios.post(`${API_BASE}/speak`, { text });
    return response.data.audio_url;
  }
};
