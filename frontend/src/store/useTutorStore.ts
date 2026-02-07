import { create } from 'zustand';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface TutorState {
  status: 'IDLE' | 'RECORDING' | 'PROCESSING' | 'SPEAKING';
  history: Message[];
  sessionId: string;
  studentLevel: string;
  setStatus: (status: TutorState['status']) => void;
  addMessage: (role: 'user' | 'assistant', content: string) => void;
}

export const useTutorStore = create<TutorState>((set) => ({
  status: 'IDLE',
  history: [{ role: 'assistant', content: 'Hello! I am Profe. How can I help you today?' }],
  sessionId: Math.random().toString(36).substring(7), // Fallback seguro para qualquer navegador
  studentLevel: 'beginner',
  setStatus: (status) => set({ status }),
  addMessage: (role, content) =>
  set((state) => ({ history: [...state.history, { role, content }] })),
}));
