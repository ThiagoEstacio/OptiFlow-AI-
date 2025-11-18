/**
 * ChatMessage component - Renders a single chat message with Markdown support
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message, MessageRole } from '../types/chat';
import { Bot, User } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === MessageRole.USER;
  const isAssistant = message.role === MessageRole.ASSISTANT;

  return (
    <div
      className={`flex gap-3 mb-4 ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gradient-to-br from-purple-500 to-pink-500 text-white'
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      {/* Message content */}
      <div
        className={`flex-1 max-w-[75%] ${
          isUser ? 'text-right' : 'text-left'
        }`}
      >
        <div
          className={`inline-block px-4 py-2 rounded-lg ${
            isUser
              ? 'bg-blue-500 text-white rounded-tr-none'
              : 'bg-gray-100 text-gray-900 rounded-tl-none border border-gray-200'
          }`}
        >
          {/* Render Markdown for assistant messages, plain text for user */}
          {isAssistant ? (
            <div className="prose prose-sm max-w-none
              prose-headings:font-bold prose-headings:mt-3 prose-headings:mb-2
              prose-h2:text-lg prose-h3:text-base prose-h4:text-sm
              prose-p:my-1 prose-p:leading-relaxed
              prose-strong:font-semibold prose-strong:text-gray-900
              prose-ul:my-2 prose-ul:pl-4 prose-li:my-0.5
              prose-a:text-blue-600 prose-a:underline hover:prose-a:text-blue-800
              [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div
          className={`text-xs text-gray-500 mt-1 ${
            isUser ? 'text-right' : 'text-left'
          }`}
        >
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
