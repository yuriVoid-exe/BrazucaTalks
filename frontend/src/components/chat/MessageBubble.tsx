import React from 'react';
import { Bot, User } from 'lucide-react';
import { Message } from '../../types/chat';

interface Props {
    message: Message;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} animate-in fade-in slide-in-from-bottom-2`}>
            <div className={`p-2 h-fit rounded-lg ${isUser ? 'bg-teal-500/20 text-teal-400' : 'bg-slate-800 text-slate-400'}`}>
                {isUser ? <User size={18} /> : <Bot size={18} />}
            </div>

            <div className={`max-w-[85%] p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${
                isUser
                ? 'bg-teal-600 text-white rounded-tr-none'
                : 'bg-slate-800 text-slate-100 rounded-tl-none border border-white/5'
            }`}>
                {message.content}
            </div>
        </div>
    );
};
