// src/hooks/useVoiceRecorder.ts
import { useState, useRef } from 'react';

export function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);
    chunks.current = [];

    mediaRecorder.current.ondataavailable = (e) => chunks.current.push(e.data);
    mediaRecorder.current.start();
    setIsRecording(true);
  };

  const stopRecording = (): Promise<Blob> => {
    return new Promise((resolve) => {
      if (!mediaRecorder.current) return;

      mediaRecorder.current.onstop = () => {
        const blob = new Blob(chunks.current, { type: 'audio/wav' });
        setIsRecording(false);
        mediaRecorder.current?.stream.getTracks().forEach(t => t.stop());
        resolve(blob);
      };
      mediaRecorder.current.stop();
    });
  };

  return { isRecording, startRecording, stopRecording };
}
