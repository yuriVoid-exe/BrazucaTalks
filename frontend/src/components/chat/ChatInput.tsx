import React from 'react';
import { Send, Mic, Square, Loader2 } from 'lucide-react';

interface ChatInputProps {
    value: string;
    status: string;
    onChange: (val: string) => void;
    onSend: () => void;
    onVoiceStart: () => void;
    onVoiceEnd: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
    value,
    status,
    onChange,
    onSend,
    onVoiceStart,
    onVoiceEnd
}) => {
    const isIdle = status === 'IDLE';
    const isRecording = status === 'RECORDING';
    const isProcessing = status === 'PROCESSING';

    return (
        <div className="p-6 bg-[#020617]/50 border-t border-white/5">
        <div className="relative group">
        <input
        className="w-full bg-slate-900 border border-white/5 rounded-2xl p-4 pr-12 outline-none focus:border-teal-500/50 transition-all text-sm text-white placeholder:text-slate-600"
        placeholder="Ask anything in English..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSend()}
        disabled={!isIdle}
        />
        <button
        onClick={onSend}
        disabled={!isIdle || !value.trim()}
        className="absolute right-3 top-3.5 p-1 text-teal-500 hover:text-teal-400 disabled:opacity-30 transition-all"
        >
        {isProcessing ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
        </button>
        </div>

        <button
        onMouseDown={onVoiceStart}
        onMouseUp={onVoiceEnd}
        disabled={!isIdle && !isRecording}
        className={`w-full mt-3 p-4 rounded-2xl flex items-center justify-center gap-3 font-bold text-xs transition-all border ${
            isRecording
            ? 'bg-red-500/20 border-red-500/50 text-red-500 animate-pulse'
            : 'bg-slate-900 border-white/5 text-slate-400 hover:bg-slate-800'
        }`}
        >
        {isRecording ? <Square size={16} fill="currentColor" /> : <Mic size={16} />}
        {isRecording ? 'RELEASE TO SEND' : 'HOLD TO SPEAK'}
        </button>
        </div>
    );
};
