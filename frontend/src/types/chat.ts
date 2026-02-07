export interface Message {
  role: 'user' | 'assistant';
  content: string;
  audioUrl?: string;
  timestamp?: number;
}

export type StudentLevel = 'beginner' | 'intermediate' | 'advanced';
export type ChatStatus = 'IDLE' | 'RECORDING' | 'PROCESSING' | 'SPEAKING';

export interface ChatRequest {
  message: string;
  session_id: string;
  level: StudentLevel;
}
