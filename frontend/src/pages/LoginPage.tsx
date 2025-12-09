/**
 * OptiFlow AI - Professional Login Page
 * Enterprise-grade Industrial IoT Platform
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useAppSelector } from '../store';
import { showErrorToast, showSuccessToast } from '../utils/toast';
import {
  Activity,
  Shield,
  Cpu,
  BarChart3,
  Zap,
  Factory,
  Eye,
  EyeOff,
  Lock,
  Mail,
  ArrowRight,
  AlertCircle,
  WifiOff
} from 'lucide-react';

// Animated background particles component
const ParticleBackground: React.FC = () => {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Gradient mesh */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900" />

      {/* Animated gradient orbs */}
      <div className="absolute top-0 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
      <div className="absolute top-0 -right-40 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
      <div className="absolute -bottom-40 left-20 w-80 h-80 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }}
      />

      {/* Floating particles */}
      <div className="absolute inset-0">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-blue-400 rounded-full opacity-30 animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${5 + Math.random() * 10}s`
            }}
          />
        ))}
      </div>
    </div>
  );
};

// Feature card component
const FeatureCard: React.FC<{ icon: React.ReactNode; title: string; description: string; delay: number }> = ({
  icon, title, description, delay
}) => (
  <div
    className="flex items-start gap-4 p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all duration-300 hover:scale-[1.02] hover:border-blue-500/30"
    style={{ animationDelay: `${delay}ms` }}
  >
    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
      {icon}
    </div>
    <div>
      <h3 className="text-white font-semibold text-sm">{title}</h3>
      <p className="text-blue-200/60 text-xs mt-1">{description}</p>
    </div>
  </div>
);

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [isFormFocused, setIsFormFocused] = useState(false);
  const { login, loading } = useAuth();
  const { error, isTimeout, isNetworkError } = useAppSelector((state) => state.auth);
  const navigate = useNavigate();

  // Clear local error when user starts typing
  useEffect(() => {
    if (username || password) {
      setLocalError('');
    }
  }, [username, password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');

    if (!username.trim()) {
      setLocalError('Por favor, insira seu email');
      return;
    }

    if (!password.trim()) {
      setLocalError('Por favor, insira sua senha');
      return;
    }

    try {
      const success = await login({ username, password });
      if (success) {
        showSuccessToast('Login realizado com sucesso!');
        navigate('/');
      } else {
        setRetryCount((prev) => prev + 1);
      }
    } catch (err) {
      console.error('Login error:', err);
      setRetryCount((prev) => prev + 1);
    }
  };

  useEffect(() => {
    if (error) {
      setLocalError(error);
      if (isTimeout) {
        showErrorToast(null, 'Tempo limite excedido. Verifique sua conexão.');
      } else if (isNetworkError) {
        showErrorToast(null, 'Não foi possível conectar ao servidor.');
      }
    }
  }, [error, isTimeout, isNetworkError]);

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding & Features */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden">
        <ParticleBackground />

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Logo & Brand */}
          <div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">OptiFlow</h1>
                <p className="text-blue-300/80 text-sm font-medium">AI Platform</p>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="max-w-lg">
            <h2 className="text-4xl font-bold text-white leading-tight mb-4">
              Plataforma Industrial
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                Inteligente
              </span>
            </h2>
            <p className="text-blue-200/70 text-lg mb-10">
              Transforme dados industriais em insights acionáveis com nossa plataforma de IoT e IA de última geração.
            </p>

            {/* Feature Cards */}
            <div className="grid gap-4">
              <FeatureCard
                icon={<Cpu className="w-5 h-5" />}
                title="Monitoramento em Tempo Real"
                description="Acompanhe todos os seus equipamentos e processos industriais instantaneamente"
                delay={100}
              />
              <FeatureCard
                icon={<BarChart3 className="w-5 h-5" />}
                title="Analytics Avançado"
                description="Dashboards executivos com KPIs, OEE e métricas de performance"
                delay={200}
              />
              <FeatureCard
                icon={<Zap className="w-5 h-5" />}
                title="Inteligência Artificial"
                description="Previsões, detecção de anomalias e otimização automática"
                delay={300}
              />
              <FeatureCard
                icon={<Shield className="w-5 h-5" />}
                title="Segurança Enterprise"
                description="Criptografia de ponta e conformidade com normas industriais"
                delay={400}
              />
            </div>
          </div>

        </div>

        {/* Decorative elements */}
        <div className="absolute bottom-0 right-0 w-96 h-96 opacity-10">
          <Factory className="w-full h-full text-blue-400" />
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="w-full lg:w-[45%] flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <div className="text-left">
                <h1 className="text-2xl font-bold text-gray-900">OptiFlow</h1>
                <p className="text-blue-600 text-sm font-medium">AI Platform</p>
              </div>
            </div>
          </div>

          {/* Welcome Text */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Bem-vindo de volta</h2>
            <p className="text-gray-600">Acesse sua conta para continuar</p>
          </div>

          {/* Connection Status */}
          {isNetworkError && (
            <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-center gap-3">
              <WifiOff className="w-5 h-5 text-amber-600 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800">Problema de conexão</p>
                <p className="text-xs text-amber-600 mt-0.5">Verifique sua internet e tente novamente</p>
              </div>
            </div>
          )}

          {/* Error Display */}
          {localError && !isNetworkError && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">{localError}</p>
                {retryCount > 2 && (
                  <p className="text-xs text-red-600 mt-1">
                    Verifique suas credenciais ou contate o suporte
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <div className={`relative rounded-xl transition-all duration-200 ${
                isFormFocused ? 'ring-2 ring-blue-500 ring-offset-2' : ''
              }`}>
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setIsFormFocused(true)}
                  onBlur={() => setIsFormFocused(false)}
                  className="block w-full pl-12 pr-4 py-3.5 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-all"
                  placeholder="admin@optiflow.com"
                  autoComplete="username"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Senha
                </label>
                <button
                  type="button"
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  onClick={() => {/* TODO: Implement forgot password */}}
                >
                  Esqueceu a senha?
                </button>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-12 pr-12 py-3.5 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-all"
                  placeholder="••••••••••"
                  autoComplete="current-password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center">
              <input
                id="remember"
                type="checkbox"
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="remember" className="ml-2 text-sm text-gray-600">
                Manter conectado
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="relative w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-4 px-6 rounded-xl font-semibold hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 group shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>Entrando...</span>
                </>
              ) : (
                <>
                  <span>Entrar</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-xs text-gray-500">
              © 2024 OptiFlow AI. Todos os direitos reservados.
            </p>
            <div className="mt-2 flex items-center justify-center gap-4 text-xs">
              <a href="#" className="text-gray-500 hover:text-blue-600 transition-colors">
                Termos de Uso
              </a>
              <span className="text-gray-300">•</span>
              <a href="#" className="text-gray-500 hover:text-blue-600 transition-colors">
                Privacidade
              </a>
              <span className="text-gray-300">•</span>
              <a href="#" className="text-gray-500 hover:text-blue-600 transition-colors">
                Suporte
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* CSS for animations */}
      <style>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(20px, -30px) scale(1.1); }
          50% { transform: translate(-20px, 20px) scale(0.9); }
          75% { transform: translate(30px, 30px) scale(1.05); }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0) translateX(0); opacity: 0.3; }
          50% { transform: translateY(-20px) translateX(10px); opacity: 0.6; }
        }

        .animate-blob {
          animation: blob 15s infinite;
        }

        .animation-delay-2000 {
          animation-delay: 2s;
        }

        .animation-delay-4000 {
          animation-delay: 4s;
        }

        .animate-float {
          animation: float 8s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};
