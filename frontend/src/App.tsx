// src/App.tsx
import React, { Suspense, useState, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { Environment, ContactShadows, Float } from '@react-three/drei';
import { useTutorStore } from './store/useTutorStore';
import Avatar from './components/canvas/Avatar';
import { Send, Mic, Square, Loader2 } from 'lucide-react';

// Importação das novas ferramentas de integração
import { useVoiceRecorder } from './hooks/useVoiceRecorder';
import { api } from './services/api';

const AVATAR_URL = "https://models.readyplayer.me/697e4cf83781699417f9548b.glb?morphTargets=ARKit,Oculus Visemes";
const ANIMATION_URL = "/models/tutor_animation.glb";

export default function App() {
  const { history, addMessage, status, setStatus, sessionId, studentLevel } = useTutorStore();
  const [text, setText] = useState('');
  const audioRef = useRef<HTMLAudioElement>(null);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);

  // Hook de gravação de voz
  const { isRecording, startRecording, stopRecording } = useVoiceRecorder();

  // --- FUNÇÃO CENTRAL DE PROCESSAMENTO (TEXTO -> STREAM -> TTS) ---
  const processConversation = async (userMsg: string) => {
    if (!userMsg.trim()) return;

    addMessage('user', userMsg);
    setStatus('PROCESSING');

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          session_id: sessionId,
          level: studentLevel || 'beginner'
        })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullResponse = "";

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;
        fullResponse += decoder.decode(value);
      }

      addMessage('assistant', fullResponse);

      // --- SOTA: Após o texto estar pronto, gera a VOZ automaticamente ---
      const audioPath = await api.getSpeechUrl(fullResponse);
      if (audioRef.current && audioPath) {
        // Prepara o sistema de áudio para o Lip-sync
        initAudio();
        // O proxy do Vite redireciona /static para o backend 8000
        audioRef.current.src = audioPath;
        audioRef.current.play();
        setStatus('SPEAKING');
      } else {
        setStatus('IDLE');
      }

    } catch (e) {
      console.error("Erro no processamento:", e);
      setStatus('IDLE');
    }
  };

  // Handler para envio de texto manual
  const handleSend = () => {
    const userText = text;
    setText('');
    processConversation(userText);
  };

  // --- HANDLERS DE VOZ (STT) ---
  const handleVoiceStart = async () => {
    if (status !== 'IDLE') return;
    try {
      await startRecording();
      setStatus('RECORDING');
    } catch (err) {
      alert("Erro ao acessar microfone.");
    }
  };

  const handleVoiceEnd = async () => {
    if (status !== 'RECORDING') return;
    setStatus('PROCESSING');
    try {
      const audioBlob = await stopRecording();
      const transcribedText = await api.transcribe(audioBlob);
      if (transcribedText) {
        processConversation(transcribedText);
      } else {
        setStatus('IDLE');
      }
    } catch (err) {
      console.error("Erro na transcrição:", err);
      setStatus('IDLE');
    }
  };

  const initAudio = () => {
    if (analyser || !audioRef.current) return;
    try {
      const AudioContextClass = (window.AudioContext || (window as any).webkitAudioContext);
      const ctx = new AudioContextClass();
      const src = ctx.createMediaElementSource(audioRef.current);
      const ans = ctx.createAnalyser();
      ans.fftSize = 256;
      src.connect(ans);
      ans.connect(ctx.destination);
      setAnalyser(ans);
    } catch (error) {
      console.error("Erro ao inicializar áudio:", error);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#020617] text-slate-200 font-sans overflow-hidden">

    {/* LADO ESQUERDO: VIEWPORT 3D */}
    <div className="flex-1 relative overflow-hidden bg-gradient-to-b from-[#0f172a] to-[#020617]">
    <Canvas
    dpr={[1, 1.5]}
    gl={{ antialias: false, powerPreference: "high-performance" }}
    camera={{ position: [0, 0.8, 4.5], fov: 40 }}
    >
    <ambientLight intensity={0.6} />
    <spotLight position={[5, 5, 5]} angle={0.15} penumbra={1} intensity={2} />
    <Suspense fallback={null}>
    <Float speed={1.5} rotationIntensity={0.1} floatIntensity={0.3}>
    <Avatar
    url={AVATAR_URL}
    animationUrl={ANIMATION_URL}
    audioAnalyser={analyser}
    />
    </Float>
    </Suspense>
    <Environment preset="city" />
    <ContactShadows opacity={0.4} scale={10} blur={2} far={4} />
    </Canvas>

    <div className="absolute top-6 left-6 flex items-center gap-3 bg-slate-900/50 backdrop-blur-md px-4 py-2 rounded-full border border-white/10">
    <div className={`w-2 h-2 rounded-full ${status === 'IDLE' ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
    <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{status}</span>
    </div>
    </div>

    {/* LADO DIREITO: INTERFACE DE CHAT */}
    <div className="w-[400px] flex flex-col bg-[#0b1120] border-l border-white/5 shadow-2xl">
    <div className="p-6 border-b border-white/5 bg-[#0b1120]/80 backdrop-blur-md">
    <h1 className="text-xl font-black bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent">
    BRAZUKATALKS <span className="text-[10px] text-slate-500 font-mono ml-2">v1.0</span>
    </h1>
    </div>

    <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
    {history.map((msg, i) => (
      <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2`}>
      <div className={`max-w-[85%] p-4 rounded-2xl text-sm shadow-sm ${
        msg.role === 'user'
        ? 'bg-teal-600 text-white rounded-tr-none'
        : 'bg-slate-800 text-slate-100 rounded-tl-none border border-white/5'
      }`}>
      {msg.content}
      </div>
      </div>
    ))}
    </div>

    <div className="p-6 bg-[#020617]/50 border-t border-white/5">
    <div className="relative group">
    <input
    className="w-full bg-slate-900 border border-white/5 rounded-2xl p-4 pr-12 outline-none focus:border-teal-500/50 transition-all text-sm"
    placeholder="Ask anything..."
    value={text}
    onChange={e => setText(e.target.value)}
    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
    disabled={status !== 'IDLE'}
    />
    <button onClick={handleSend} disabled={status !== 'IDLE'} className="absolute right-3 top-3.5 p-1 text-teal-500 hover:text-teal-400 disabled:opacity-30">
    {status === 'PROCESSING' ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
    </button>
    </div>

    {/* BOTÃO DE VOZ COM EVENTOS MOUSE DOWN/UP (ESTILO WALKIE-TALKIE) */}
    <button
    onMouseDown={handleVoiceStart}
    onMouseUp={handleVoiceEnd}
    disabled={status !== 'IDLE' && status !== 'RECORDING'}
    className={`w-full mt-3 p-4 rounded-2xl flex items-center justify-center gap-3 font-bold text-xs transition-all border ${
      status === 'RECORDING'
      ? 'bg-red-500/20 border-red-500/50 text-red-500 animate-pulse'
      : 'bg-slate-900 border-white/5 text-slate-400 hover:bg-slate-800'
    }`}
    >
    {status === 'RECORDING' ? <Square size={16} fill="currentColor" /> : <Mic size={16} />}
    {status === 'RECORDING' ? 'RELEASE TO SEND' : 'HOLD TO SPEAK'}
    </button>
    </div>
    </div>

    <audio ref={audioRef} onEnded={() => setStatus('IDLE')} />
    </div>
  );
}
