// src/components/chat/MessageList.tsx
import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { Message } from '../../types/chat';

export const MessageList = ({ messages }: { messages: Message[] }) => {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-none">
        {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} />
        ))}
        </div>
    );
};
