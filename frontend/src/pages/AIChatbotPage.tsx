import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  MessageSquare,
  Plus,
  MoreVertical,
  Trash2,
  Archive,
  Sparkles,
  Command,
  TrendingUp,
  AlertCircle,
  Settings,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

// Types
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    context_used?: boolean;
    relevant_tags?: string[];
    processing_time_ms?: number;
  };
  feedback?: 'helpful' | 'not_helpful';
}

interface Conversation {
  id: string;
  title: string;
  message_count: number;
  last_message_at?: string;
  is_active: boolean;
  created_at: string;
}

const AIChatbotPage: React.FC = () => {
  // State
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [includeContext, setIncludeContext] = useState(true);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation messages when selected
  useEffect(() => {
    if (currentConversation) {
      loadMessages(currentConversation);
    }
  }, [currentConversation]);

  // API calls (mock for now - replace with actual API calls)
  const loadConversations = async () => {
    // Mock data
    setConversations([
      {
        id: 'conv-1',
        title: 'Analyzing reactor temperature trends',
        message_count: 12,
        last_message_at: new Date().toISOString(),
        is_active: true,
        created_at: new Date(Date.now() - 86400000).toISOString()
      },
      {
        id: 'conv-2',
        title: 'Equipment maintenance schedule',
        message_count: 8,
        last_message_at: new Date(Date.now() - 3600000).toISOString(),
        is_active: true,
        created_at: new Date(Date.now() - 172800000).toISOString()
      }
    ]);
  };

  const loadMessages = async (conversationId: string) => {
    // Mock messages
    setMessages([
      {
        id: 'msg-1',
        role: 'user',
        content: 'What is the current status of reactor temperature?',
        timestamp: new Date().toISOString()
      },
      {
        id: 'msg-2',
        role: 'assistant',
        content: 'Based on the latest data, the reactor temperature is currently at 76.8°C, which is within the normal operating range of 70-85°C. The 24-hour average is 75.5°C with a standard deviation of 3.2°C, indicating stable performance.\n\nThe temperature has been trending slightly upward over the past 2 hours (+1.5°C), but this is normal for this time of day based on historical patterns.',
        timestamp: new Date().toISOString(),
        metadata: {
          context_used: true,
          relevant_tags: ['reactor_temp_001'],
          processing_time_ms: 523
        }
      }
    ]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: getSimulatedResponse(inputMessage),
        timestamp: new Date().toISOString(),
        metadata: {
          context_used: includeContext,
          relevant_tags: ['reactor_temp_001', 'pump_flow_002'],
          processing_time_ms: 487
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const getSimulatedResponse = (input: string): string => {
    const lower = input.toLowerCase();

    if (lower.includes('temperature') || lower.includes('temp')) {
      return 'The reactor temperature is currently at 76.8°C, which is within normal range. I\'ve analyzed the past 24 hours and noticed a gradual upward trend of approximately 0.5°C per hour. This is consistent with the typical daily cycle.\n\n📊 Key Metrics:\n- Current: 76.8°C\n- 24h Average: 75.5°C ± 3.2°C\n- Trend: Stable with minor fluctuations\n- Status: ✅ Normal';
    }

    if (lower.includes('optimize') || lower.includes('improve')) {
      return '🎯 Optimization Recommendations:\n\n1. **Energy Efficiency**\n   - Reduce reactor setpoint to 82°C during off-peak hours\n   - Estimated savings: 8% energy consumption\n\n2. **Throughput**\n   - Increase batch size by 5%\n   - Optimize material feed rate to 125 kg/h\n\n3. **Quality**\n   - Fine-tune PID parameters for better temperature stability\n   - Current overshoot: 2.3°C, Target: <1.5°C';
    }

    if (lower.includes('anomaly') || lower.includes('problem')) {
      return '🔍 Anomaly Analysis:\n\nI\'ve detected 2 anomalies in the past 24 hours:\n\n⚠️ **Pump B Flow Rate** (6 hours ago)\n- Sudden drop of 15% from baseline\n- Root cause: Possible filter clogging\n- Recommendation: Inspect and clean filter\n\n⚠️ **Pressure Sensor 3** (2 hours ago)\n- Reading spikes outside normal range\n- Likely cause: Sensor drift or calibration issue\n- Action: Schedule calibration check';
    }

    if (lower.includes('forecast') || lower.includes('predict')) {
      return '📈 24-Hour Forecast:\n\nBased on historical patterns and current trends:\n\n**Next 6 hours:** Production rate expected to increase by 12%\n**Peak expected:** Tomorrow 2:00 PM (estimated 425 units/hour)\n**Confidence:** 87%\n\n🎯 Recommendations:\n- Ensure adequate raw material inventory\n- Schedule quality checks during peak production\n- Monitor equipment performance closely';
    }

    return 'I\'m here to help you analyze your industrial process data. I can assist with:\n\n- 📊 Real-time data analysis\n- 🔍 Anomaly detection and troubleshooting\n- 📈 Forecasting and predictions\n- ⚙️ Optimization recommendations\n- 🔧 Equipment health monitoring\n\nTry asking about specific tags, or use commands like `/analyze`, `/forecast`, `/anomalies`, or `/optimize`.';
  };

  const createNewConversation = () => {
    const newConv: Conversation = {
      id: `conv-${Date.now()}`,
      title: 'New Conversation',
      message_count: 0,
      is_active: true,
      created_at: new Date().toISOString()
    };

    setConversations(prev => [newConv, ...prev]);
    setCurrentConversation(newConv.id);
    setMessages([]);
  };

  const deleteConversation = (id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentConversation === id) {
      setCurrentConversation(null);
      setMessages([]);
    }
  };

  const provideFeedback = (messageId: string, feedback: 'helpful' | 'not_helpful') => {
    setMessages(prev =>
      prev.map(msg =>
        msg.id === messageId ? { ...msg, feedback } : msg
      )
    );
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const commands = [
    { cmd: '/analyze', desc: 'Analyze a specific tag', icon: <TrendingUp size={16} /> },
    { cmd: '/forecast', desc: 'Generate forecast', icon: <Sparkles size={16} /> },
    { cmd: '/anomalies', desc: 'List recent anomalies', icon: <AlertCircle size={16} /> },
    { cmd: '/optimize', desc: 'Get optimization tips', icon: <Settings size={16} /> },
    { cmd: '/maintenance', desc: 'Check equipment health', icon: <Command size={16} /> },
  ];

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar - Conversations */}
      <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Bot className="w-6 h-6 text-blue-500" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                AI Assistant
              </h1>
            </div>
            <button
              onClick={createNewConversation}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Plus size={20} className="text-gray-600 dark:text-gray-400" />
            </button>
          </div>

          <button
            onClick={() => setShowCommands(!showCommands)}
            className="w-full px-3 py-2 text-sm text-left flex items-center space-x-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
          >
            <Command size={16} />
            <span>Quick Commands</span>
          </button>

          {showCommands && (
            <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg space-y-2">
              {commands.map((c, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setInputMessage(c.cmd + ' ');
                    setShowCommands(false);
                    inputRef.current?.focus();
                  }}
                  className="w-full px-2 py-1.5 text-xs text-left flex items-center space-x-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  {c.icon}
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{c.cmd}</div>
                    <div className="text-gray-500 dark:text-gray-400">{c.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {conversations.map(conv => (
            <button
              key={conv.id}
              onClick={() => setCurrentConversation(conv.id)}
              className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 transition-colors ${
                currentConversation === conv.id ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-500' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <MessageSquare size={16} className="text-gray-400 flex-shrink-0" />
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {conv.title}
                    </h3>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {conv.message_count} messages
                    {conv.last_message_at && ` · ${formatTimestamp(conv.last_message_at)}`}
                  </p>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                >
                  <Trash2 size={14} className="text-gray-400" />
                </button>
              </div>
            </button>
          ))}

          {conversations.length === 0 && (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
              <Bot size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-sm">No conversations yet</p>
              <p className="text-xs mt-2">Start a new conversation to get insights!</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentConversation || messages.length > 0 ? (
          <>
            {/* Chat Header */}
            <div className="px-6 py-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {conversations.find(c => c.id === currentConversation)?.title || 'AI Assistant'}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Get insights about your industrial processes
                </p>
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                  <input
                    type="checkbox"
                    checked={includeContext}
                    onChange={(e) => setIncludeContext(e.target.checked)}
                    className="rounded"
                  />
                  <span>Include Context</span>
                </label>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex space-x-3 max-w-3xl ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    {/* Avatar */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      msg.role === 'user'
                        ? 'bg-blue-500'
                        : 'bg-gradient-to-br from-purple-500 to-pink-500'
                    }`}>
                      {msg.role === 'user' ? (
                        <User size={18} className="text-white" />
                      ) : (
                        <Bot size={18} className="text-white" />
                      )}
                    </div>

                    {/* Message Content */}
                    <div className={`flex-1 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className={`inline-block px-4 py-3 rounded-2xl ${
                        msg.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm border border-gray-200 dark:border-gray-700'
                      }`}>
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      </div>

                      {/* Metadata */}
                      <div className={`mt-1 text-xs text-gray-500 dark:text-gray-400 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                        {formatTimestamp(msg.timestamp)}
                        {msg.metadata?.context_used && msg.role === 'assistant' && (
                          <span className="ml-2">· Using context</span>
                        )}
                      </div>

                      {/* Feedback (Assistant messages only) */}
                      {msg.role === 'assistant' && (
                        <div className="mt-2 flex items-center space-x-2">
                          <button
                            onClick={() => provideFeedback(msg.id, 'helpful')}
                            className={`p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                              msg.feedback === 'helpful' ? 'bg-green-100 dark:bg-green-900/30 text-green-600' : 'text-gray-400'
                            }`}
                          >
                            <ThumbsUp size={14} />
                          </button>
                          <button
                            onClick={() => provideFeedback(msg.id, 'not_helpful')}
                            className={`p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                              msg.feedback === 'not_helpful' ? 'bg-red-100 dark:bg-red-900/30 text-red-600' : 'text-gray-400'
                            }`}
                          >
                            <ThumbsDown size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex space-x-3 max-w-3xl">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                      <Bot size={18} className="text-white" />
                    </div>
                    <div className="bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 px-4 py-3 rounded-2xl">
                      <div className="flex space-x-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-end space-x-3">
                <div className="flex-1">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                    placeholder="Ask about your process data, or type / for commands..."
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isLoading}
                  />
                </div>
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white rounded-xl transition-colors flex items-center space-x-2"
                >
                  <Send size={18} />
                  <span>Send</span>
                </button>
              </div>
            </div>
          </>
        ) : (
          /* Empty State */
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center">
                <Bot size={48} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                Welcome to OptiFlow AI Assistant
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                I'm here to help you analyze process data, detect anomalies, generate forecasts, and optimize your operations.
              </p>
              <button
                onClick={createNewConversation}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-colors inline-flex items-center space-x-2"
              >
                <Plus size={20} />
                <span>Start New Conversation</span>
              </button>

              <div className="mt-8 grid grid-cols-2 gap-3">
                {commands.map((c, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-left">
                    <div className="flex items-center space-x-2 mb-1">
                      {c.icon}
                      <span className="text-sm font-medium text-gray-900 dark:text-white">{c.cmd}</span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{c.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIChatbotPage;
