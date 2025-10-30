import React, { useState } from 'react'
import ChatBot from './components/ChatBot'
import { Sparkles } from 'lucide-react'

function App() {
  const [showChat, setShowChat] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {!showChat ? (
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="text-center max-w-4xl">
            <div className="mb-8">
              <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
                OptiFlow AI Platform
              </h1>
              <p className="text-xl text-gray-700 mb-8">
                Industrial IoT Platform with AI-powered optimization
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-xl mb-8">
              <div className="flex items-center justify-center mb-6">
                <Sparkles className="text-purple-500 mr-2" size={32} />
                <h2 className="text-3xl font-semibold">AI Assistant Available!</h2>
              </div>

              <p className="text-gray-600 mb-6 text-lg">
                Experimente nosso assistente de IA para obter insights sobre seus dispositivos industriais
              </p>

              <button
                onClick={() => setShowChat(true)}
                className="px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-lg font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Abrir AI Assistant
              </button>

              <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg">
                  <p className="text-sm font-semibold text-green-800 mb-1">
                    ✓ Backend API Ready
                  </p>
                  <p className="text-xs text-green-600">
                    FastAPI com suporte assíncrono completo
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg">
                  <p className="text-sm font-semibold text-green-800 mb-1">
                    ✓ AI Chatbot Integration
                  </p>
                  <p className="text-xs text-green-600">
                    Assistente inteligente com insights em tempo real
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg">
                  <p className="text-sm font-semibold text-green-800 mb-1">
                    ✓ Database Models Created
                  </p>
                  <p className="text-xs text-green-600">
                    PostgreSQL + InfluxDB + Redis
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg">
                  <p className="text-sm font-semibold text-green-800 mb-1">
                    ✓ Time Series Integration
                  </p>
                  <p className="text-xs text-green-600">
                    InfluxDB para dados de alta frequência
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white/60 backdrop-blur-sm p-6 rounded-xl">
              <h3 className="text-lg font-semibold mb-3 text-gray-800">
                Recursos do AI Assistant
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="text-center p-3">
                  <div className="text-2xl mb-2">🤖</div>
                  <div className="font-semibold text-gray-700">Análise Inteligente</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Insights sobre dispositivos e dados
                  </div>
                </div>
                <div className="text-center p-3">
                  <div className="text-2xl mb-2">📊</div>
                  <div className="font-semibold text-gray-700">Monitoramento</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Status em tempo real de alarmes
                  </div>
                </div>
                <div className="text-center p-3">
                  <div className="text-2xl mb-2">💡</div>
                  <div className="font-semibold text-gray-700">Recomendações</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Sugestões de otimização
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="h-screen p-4">
          <div className="max-w-7xl mx-auto h-full flex flex-col">
            <div className="mb-4 flex justify-between items-center">
              <h1 className="text-2xl font-bold text-gray-800">
                OptiFlow AI Platform
              </h1>
              <button
                onClick={() => setShowChat(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Voltar
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <ChatBot />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
