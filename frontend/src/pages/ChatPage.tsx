/**
 * Chat Page - AI Assistant Chat Interface
 */
import React from 'react';
import ChatBot from '../components/ChatBot';

export const ChatPage: React.FC = () => {
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-hidden">
        <ChatBot />
      </div>
    </div>
  );
};
