/**
 * NoDataAvailable Component
 * =========================
 *
 * Professional "no data" state component to replace fake/fallback data.
 * Ensures users can distinguish between "no data available" and "real data".
 *
 * CORR-001: Integridade de Dados - Sprint 1
 */
import React from 'react';
import { Card, Text, Title, Flex, Button, Callout } from '@tremor/react';
import {
  Database,
  AlertCircle,
  RefreshCw,
  Info,
  Settings,
  Clock,
  WifiOff,
} from 'lucide-react';

export type NoDataVariant =
  | 'default'      // Generic no data
  | 'loading'      // Data is loading
  | 'error'        // Error fetching data
  | 'empty'        // API returned empty
  | 'no-connection' // No connection to source
  | 'no-model'     // ML model not trained
  | 'pending';     // Waiting for data collection

interface NoDataAvailableProps {
  title?: string;
  description?: string;
  variant?: NoDataVariant;
  icon?: React.ElementType;
  onRetry?: () => void;
  onConfigure?: () => void;
  showCard?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const variantConfig: Record<NoDataVariant, {
  icon: React.ElementType;
  title: string;
  description: string;
  color: 'gray' | 'blue' | 'amber' | 'red';
}> = {
  default: {
    icon: Database,
    title: 'Sem Dados Disponíveis',
    description: 'Não há dados para exibir neste momento.',
    color: 'gray',
  },
  loading: {
    icon: RefreshCw,
    title: 'Carregando Dados',
    description: 'Aguarde enquanto os dados são carregados...',
    color: 'blue',
  },
  error: {
    icon: AlertCircle,
    title: 'Erro ao Carregar',
    description: 'Não foi possível carregar os dados. Tente novamente.',
    color: 'red',
  },
  empty: {
    icon: Database,
    title: 'Nenhum Dado Encontrado',
    description: 'A consulta não retornou resultados para o período selecionado.',
    color: 'gray',
  },
  'no-connection': {
    icon: WifiOff,
    title: 'Sem Conexão',
    description: 'Não foi possível conectar à fonte de dados.',
    color: 'amber',
  },
  'no-model': {
    icon: Settings,
    title: 'Modelo Não Treinado',
    description: 'O modelo ML ainda não foi treinado para este equipamento.',
    color: 'amber',
  },
  pending: {
    icon: Clock,
    title: 'Aguardando Coleta',
    description: 'Os dados estão sendo coletados. Disponível em breve.',
    color: 'blue',
  },
};

export const NoDataAvailable: React.FC<NoDataAvailableProps> = ({
  title,
  description,
  variant = 'default',
  icon,
  onRetry,
  onConfigure,
  showCard = true,
  className = '',
  size = 'md',
}) => {
  const config = variantConfig[variant];
  const IconComponent = icon || config.icon;

  const sizeClasses = {
    sm: { container: 'py-4', icon: 'w-8 h-8', title: 'text-sm', desc: 'text-xs' },
    md: { container: 'py-8', icon: 'w-12 h-12', title: 'text-base', desc: 'text-sm' },
    lg: { container: 'py-12', icon: 'w-16 h-16', title: 'text-lg', desc: 'text-base' },
  };

  const sizes = sizeClasses[size];

  const iconColors = {
    gray: 'text-gray-400',
    blue: 'text-blue-500',
    amber: 'text-amber-500',
    red: 'text-red-500',
  };

  const bgColors = {
    gray: 'bg-gray-100',
    blue: 'bg-blue-100',
    amber: 'bg-amber-100',
    red: 'bg-red-100',
  };

  const content = (
    <div className={`text-center ${sizes.container} ${className}`}>
      <div className={`mx-auto rounded-full ${bgColors[config.color]} p-4 w-fit mb-4`}>
        <IconComponent className={`${sizes.icon} ${iconColors[config.color]} ${variant === 'loading' ? 'animate-spin' : ''}`} />
      </div>

      <Title className={`${sizes.title} text-gray-700 mb-2`}>
        {title || config.title}
      </Title>

      <Text className={`${sizes.desc} text-gray-500 max-w-md mx-auto mb-4`}>
        {description || config.description}
      </Text>

      {(onRetry || onConfigure) && (
        <Flex justifyContent="center" className="gap-3 mt-4">
          {onRetry && (
            <Button
              size="xs"
              variant="secondary"
              icon={RefreshCw}
              onClick={onRetry}
            >
              Tentar Novamente
            </Button>
          )}
          {onConfigure && (
            <Button
              size="xs"
              variant="secondary"
              icon={Settings}
              onClick={onConfigure}
            >
              Configurar
            </Button>
          )}
        </Flex>
      )}

      {/* Data Integrity Indicator */}
      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-gray-400">
        <Info className="w-3 h-3" />
        <span>Este espaço mostrará dados reais quando disponíveis</span>
      </div>
    </div>
  );

  if (!showCard) {
    return content;
  }

  return (
    <Card className="border-dashed border-2 border-gray-200 bg-gray-50/50">
      {content}
    </Card>
  );
};

/**
 * NoMLPrediction - Specific component for missing ML predictions
 */
export const NoMLPrediction: React.FC<{
  equipmentName?: string;
  onTrain?: () => void;
}> = ({ equipmentName, onTrain }) => (
  <Callout
    title="Previsão ML Indisponível"
    icon={Settings}
    color="amber"
  >
    <Text className="text-sm">
      {equipmentName
        ? `O modelo de ML para "${equipmentName}" ainda não foi treinado.`
        : 'Modelo de ML não treinado para este equipamento.'
      }
    </Text>
    <Text className="text-xs text-amber-700 mt-1">
      São necessários pelo menos 1000 pontos de dados históricos para treinar o modelo.
    </Text>
    {onTrain && (
      <Button size="xs" variant="light" color="amber" className="mt-2" onClick={onTrain}>
        Treinar Modelo
      </Button>
    )}
  </Callout>
);

/**
 * NoInsightsAvailable - For empty ML insights
 */
export const NoInsightsAvailable: React.FC<{
  period?: string;
}> = ({ period }) => (
  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-center">
    <Database className="w-10 h-10 text-slate-400 mx-auto mb-2" />
    <Text className="font-medium text-slate-600">Sem Insights Disponíveis</Text>
    <Text className="text-sm text-slate-500 mt-1">
      Não há análises de causa raiz para {period || 'o período selecionado'}.
    </Text>
    <Text className="text-xs text-slate-400 mt-2">
      Insights são gerados automaticamente quando anomalias são detectadas.
    </Text>
  </div>
);

export default NoDataAvailable;
