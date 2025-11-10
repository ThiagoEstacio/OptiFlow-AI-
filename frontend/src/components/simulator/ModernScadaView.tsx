/**
 * Modern SCADA View - Terminal Exportador de Grãos
 *
 * Interface industrial moderna com:
 * - Animações SVG suaves e realísticas
 * - Cores dinâmicas por status
 * - Fluxo de material animado
 * - Indicadores em tempo real
 * - Design tipo PI ProcessBook / Wonderware
 */

import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Chip, Stack, Tooltip, alpha } from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as OkIcon,
  Speed as SpeedIcon,
  Thermostat as TempIcon,
  Power as PowerIcon,
  Build as MaintenanceIcon,
} from '@mui/icons-material';

interface ModernScadaViewProps {
  status: any;
  onEquipmentClick?: (equipmentId: string) => void;
}

// Cores industriais modernas
const COLORS = {
  background: '#0a0e27',
  panel: '#1a1f3a',
  equipment: {
    stopped: '#374151',
    running: '#10b981',
    warning: '#f59e0b',
    alarm: '#ef4444',
    fault: '#b91c1c',
  },
  belt: {
    stopped: '#4b5563',
    running: '#3b82f6',
  },
  material: '#fbbf24',
  flow: '#f59e0b',
  text: '#e5e7eb',
  textDim: '#9ca3af',
  accent: '#8b5cf6',
};

export const ModernScadaView: React.FC<ModernScadaViewProps> = ({ status, onEquipmentClick }) => {
  const [flowAnimation, setFlowAnimation] = useState(0);

  // Anima fluxo de material - DEVE estar antes do early return (regra dos Hooks)
  useEffect(() => {
    const interval = setInterval(() => {
      setFlowAnimation(prev => (prev + 1) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Retorna early se status não está disponível
  if (!status) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Typography color="white">Carregando status do simulador...</Typography>
      </Box>
    );
  }

  // Determina cor do equipamento baseado em status
  const getEquipmentColor = (equipment: any): string => {
    if (!equipment) return COLORS.equipment.stopped;
    if (equipment.failure || equipment.fault) return COLORS.equipment.fault;
    if (equipment.alarm) return COLORS.equipment.alarm;
    if (equipment.warning) return COLORS.equipment.warning;
    if (equipment.running) return COLORS.equipment.running;
    return COLORS.equipment.stopped;
  };

  // Calcula intensidade de fluxo para animação
  const getFlowIntensity = (flowTph: number): number => {
    return Math.min(flowTph / 1500, 1.0); // Normaliza baseado em 1500 t/h máximo
  };

  // Renderiza partículas de fluxo animadas
  const renderFlowParticles = (
    pathId: string,
    flowTph: number,
    particleCount: number = 20
  ) => {
    const intensity = getFlowIntensity(flowTph);
    if (intensity < 0.01) return null;

    // Não renderiza partículas se o path ainda não existe
    const pathElement = typeof document !== 'undefined' ? document.getElementById(pathId) : null;
    if (!pathElement) return null;

    const pathData = pathElement.getAttribute('d');
    if (!pathData) return null;

    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      const offset = (i / particleCount * 100) + (flowAnimation * intensity);
      particles.push(
        <circle
          key={`${pathId}-particle-${i}`}
          r="3"
          fill={COLORS.material}
          opacity={intensity * 0.8}
        >
          <animateMotion
            dur={`${2 / intensity}s`}
            repeatCount="indefinite"
            path={pathData}
            begin={`${-i * 0.1}s`}
          />
        </circle>
      );
    }
    return <g>{particles}</g>;
  };

  const running = status?.system?.running || false;
  const belts = status?.belts || {};
  const gates = status?.gates || [];
  const elevator = status?.elevator || {};
  const shiploader = status?.shiploader || {};
  const warehouse = status?.warehouse || {};

  return (
    <Paper
      elevation={3}
      sx={{
        bgcolor: COLORS.background,
        p: 2,
        borderRadius: 2,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Header com KPIs */}
      <Box sx={{ mb: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
          <Typography variant="h5" sx={{ color: COLORS.text, fontWeight: 600 }}>
            🏭 Terminal Exportador - Linha 1500 t/h
          </Typography>

          <Stack direction="row" spacing={2}>
            <Chip
              icon={<SpeedIcon />}
              label={`${(shiploader.flow_tph || 0).toFixed(0)} t/h`}
              sx={{
                bgcolor: alpha(COLORS.accent, 0.2),
                color: COLORS.text,
                fontWeight: 600,
                fontSize: '0.95rem',
              }}
            />
            <Chip
              icon={<PowerIcon />}
              label={`${(status?.energy?.total_power_kW || 0).toFixed(0)} kW`}
              sx={{
                bgcolor: alpha(COLORS.equipment.running, 0.2),
                color: COLORS.text,
                fontWeight: 600,
              }}
            />
            <Chip
              icon={running ? <OkIcon /> : <ErrorIcon />}
              label={running ? 'OPERANDO' : 'PARADO'}
              sx={{
                bgcolor: running
                  ? alpha(COLORS.equipment.running, 0.3)
                  : alpha(COLORS.equipment.stopped, 0.3),
                color: COLORS.text,
                fontWeight: 700,
              }}
            />
          </Stack>
        </Stack>
      </Box>

      {/* SVG Process View */}
      <Box
        sx={{
          width: '100%',
          height: '700px',
          position: 'relative',
          bgcolor: alpha(COLORS.panel, 0.5),
          borderRadius: 1,
          border: `1px solid ${alpha(COLORS.text, 0.1)}`,
        }}
      >
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 1600 700"
          style={{ display: 'block' }}
        >
          <defs>
            {/* Gradientes para efeitos visuais */}
            <linearGradient id="beltGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={COLORS.belt.running} stopOpacity="0.3" />
              <stop offset="50%" stopColor={COLORS.belt.running} stopOpacity="0.8" />
              <stop offset="100%" stopColor={COLORS.belt.running} stopOpacity="0.3" />
            </linearGradient>

            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>

            {/* Padrão para correias em movimento */}
            <pattern id="beltPattern" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
              <rect width="20" height="20" fill={COLORS.belt.stopped} />
              <line x1="0" y1="10" x2="20" y2="10" stroke={COLORS.belt.running} strokeWidth="1" opacity="0.5" />
            </pattern>

            {/* Paths para animação de partículas */}
            <path
              id="corr01Path"
              d="M 250 350 L 600 350"
              fill="none"
              stroke="none"
            />
            <path
              id="corr02Path"
              d="M 600 350 L 600 150"
              fill="none"
              stroke="none"
            />
            <path
              id="elevatorPath"
              d="M 600 150 L 600 80"
              fill="none"
              stroke="none"
            />
            <path
              id="corr03Path"
              d="M 600 80 L 1200 80"
              fill="none"
              stroke="none"
            />
          </defs>

          {/* Grid de fundo (opcional) */}
          <g opacity="0.05">
            {Array.from({ length: 35 }).map((_, i) => (
              <line
                key={`gridV-${i}`}
                x1={i * 50}
                y1="0"
                x2={i * 50}
                y2="700"
                stroke={COLORS.text}
                strokeWidth="1"
              />
            ))}
            {Array.from({ length: 15 }).map((_, i) => (
              <line
                key={`gridH-${i}`}
                x1="0"
                y1={i * 50}
                x2="1600"
                y2={i * 50}
                stroke={COLORS.text}
                strokeWidth="1"
              />
            ))}
          </g>

          {/* ===================== WAREHOUSE ===================== */}
          <g id="warehouse" onClick={() => onEquipmentClick?.('warehouse')}>
            <rect
              x="50"
              y="200"
              width="150"
              height="250"
              fill={alpha(COLORS.equipment.running, 0.2)}
              stroke={COLORS.equipment.running}
              strokeWidth="3"
              rx="5"
              style={{ cursor: 'pointer' }}
            />

            {/* Nível de estoque */}
            <rect
              x="60"
              y={200 + (250 * (1 - (warehouse.level_pct || 0) / 100))}
              width="130"
              height={250 * ((warehouse.level_pct || 0) / 100)}
              fill={alpha(COLORS.material, 0.6)}
            />

            <text x="125" y="315" textAnchor="middle" fill={COLORS.text} fontSize="16" fontWeight="600">
              ARMAZÉM
            </text>
            <text x="125" y="335" textAnchor="middle" fill={COLORS.material} fontSize="20" fontWeight="700">
              {(warehouse.level_pct || 0).toFixed(1)}%
            </text>
            <text x="125" y="355" textAnchor="middle" fill={COLORS.textDim} fontSize="12">
              {(warehouse.inventory_t || 0).toFixed(0)} t
            </text>
          </g>

          {/* ===================== GATES (Comportas) ===================== */}
          {gates.slice(0, 4).map((gate: any, idx: number) => {
            const yPos = 230 + idx * 60;
            const isActive = gate.open_pct > 5;
            const color = isActive ? COLORS.equipment.running : COLORS.equipment.stopped;

            return (
              <g
                key={`gate-${gate.id}`}
                onClick={() => onEquipmentClick?.(`gate-${gate.id}`)}
                style={{ cursor: 'pointer' }}
              >
                {/* Gate body */}
                <rect
                  x="200"
                  y={yPos}
                  width="40"
                  height="50"
                  fill={alpha(color, 0.3)}
                  stroke={color}
                  strokeWidth="2"
                  rx="2"
                />

                {/* Opening indicator */}
                <rect
                  x="205"
                  y={yPos + 50 - (gate.open_pct / 100 * 40)}
                  width="30"
                  height={(gate.open_pct / 100 * 40)}
                  fill={alpha(COLORS.material, 0.7)}
                />

                <text x="220" y={yPos + 28} textAnchor="middle" fill={COLORS.text} fontSize="10" fontWeight="600">
                  G{gate.id}
                </text>
                <text x="220" y={yPos + 40} textAnchor="middle" fill={COLORS.accent} fontSize="9">
                  {gate.open_pct?.toFixed(0)}%
                </text>
              </g>
            );
          })}

          {/* ===================== CORR01 (Belt 1) ===================== */}
          <g id="corr01" onClick={() => onEquipmentClick?.('CORR01')}>
            {/* Belt structure */}
            <rect
              x="250"
              y="330"
              width="350"
              height="40"
              fill={belts.CORR01?.running ? "url(#beltGradient)" : alpha(COLORS.belt.stopped, 0.3)}
              stroke={getEquipmentColor(belts.CORR01)}
              strokeWidth="3"
              rx="3"
              style={{ cursor: 'pointer' }}
            />

            {/* Belt animation when running */}
            {belts.CORR01?.running && (
              <rect
                x="250"
                y="330"
                width="350"
                height="40"
                fill="url(#beltPattern)"
                opacity="0.4"
              >
                <animateTransform
                  attributeName="transform"
                  type="translate"
                  from="0 0"
                  to="20 0"
                  dur="1s"
                  repeatCount="indefinite"
                />
              </rect>
            )}

            {/* Labels */}
            <text x="425" y="345" textAnchor="middle" fill={COLORS.text} fontSize="14" fontWeight="600">
              CORR01
            </text>
            <text x="425" y="360" textAnchor="middle" fill={COLORS.accent} fontSize="12" fontWeight="700">
              {(belts.CORR01?.flow_tph || 0).toFixed(0)} t/h
            </text>

            {/* Status indicators */}
            <circle
              cx="270"
              cy="340"
              r="5"
              fill={belts.CORR01?.running ? COLORS.equipment.running : COLORS.equipment.stopped}
              filter="url(#glow)"
            >
              {belts.CORR01?.running && (
                <animate attributeName="opacity" values="0.5;1;0.5" dur="1.5s" repeatCount="indefinite" />
              )}
            </circle>

            {/* Temperatura */}
            <text x="270" y="325" fill={COLORS.textDim} fontSize="10">
              🌡️ {(belts.CORR01?.temp_bearing_C || 0).toFixed(0)}°C
            </text>
          </g>

          {/* Flow particles CORR01 */}
          {running && renderFlowParticles('corr01Path', belts.CORR01?.flow_tph || 0)}

          {/* ===================== CORR02 (Belt 2 - Vertical) ===================== */}
          <g id="corr02" onClick={() => onEquipmentClick?.('CORR02')}>
            <rect
              x="580"
              y="150"
              width="40"
              height="200"
              fill={belts.CORR02?.running ? "url(#beltGradient)" : alpha(COLORS.belt.stopped, 0.3)}
              stroke={getEquipmentColor(belts.CORR02)}
              strokeWidth="3"
              rx="3"
              style={{ cursor: 'pointer' }}
            />

            <text x="600" y="245" textAnchor="middle" fill={COLORS.text} fontSize="12" fontWeight="600" transform="rotate(-90 600 245)">
              CORR02
            </text>
            <text x="600" y="260" textAnchor="middle" fill={COLORS.accent} fontSize="10" fontWeight="700" transform="rotate(-90 600 260)">
              {(belts.CORR02?.flow_tph || 0).toFixed(0)} t/h
            </text>
          </g>

          {/* Flow particles CORR02 */}
          {running && renderFlowParticles('corr02Path', belts.CORR02?.flow_tph || 0)}

          {/* ===================== ELEVATOR ===================== */}
          <g id="elevator" onClick={() => onEquipmentClick?.('ELV01')}>
            <rect
              x="575"
              y="80"
              width="50"
              height="70"
              fill={alpha(getEquipmentColor(elevator), 0.4)}
              stroke={getEquipmentColor(elevator)}
              strokeWidth="3"
              rx="3"
              style={{ cursor: 'pointer' }}
            />

            {/* Bucket animation */}
            {elevator.running && (
              <>
                <rect x="585" y="90" width="10" height="8" fill={COLORS.material}>
                  <animate attributeName="y" values="90;130;90" dur="2s" repeatCount="indefinite" />
                </rect>
                <rect x="605" y="110" width="10" height="8" fill={COLORS.material}>
                  <animate attributeName="y" values="110;140;110" dur="2s" begin="0.5s" repeatCount="indefinite" />
                </rect>
              </>
            )}

            <text x="600" y="110" textAnchor="middle" fill={COLORS.text} fontSize="11" fontWeight="600">
              ELV
            </text>
            <text x="600" y="125" textAnchor="middle" fill={COLORS.accent} fontSize="9">
              {(elevator.flow_tph || 0).toFixed(0)} t/h
            </text>
          </g>

          {/* Flow particles ELEVATOR */}
          {running && renderFlowParticles('elevatorPath', elevator.flow_tph || 0, 10)}

          {/* ===================== CORR03 (Belt 3 - Horizontal Top) ===================== */}
          <g id="corr03" onClick={() => onEquipmentClick?.('CORR03')}>
            <rect
              x="625"
              y="60"
              width="575"
              height="40"
              fill={belts.CORR03?.running ? "url(#beltGradient)" : alpha(COLORS.belt.stopped, 0.3)}
              stroke={getEquipmentColor(belts.CORR03)}
              strokeWidth="3"
              rx="3"
              style={{ cursor: 'pointer' }}
            />

            <text x="900" y="75" textAnchor="middle" fill={COLORS.text} fontSize="14" fontWeight="600">
              CORR03
            </text>
            <text x="900" y="90" textAnchor="middle" fill={COLORS.accent} fontSize="12" fontWeight="700">
              {(belts.CORR03?.flow_tph || 0).toFixed(0)} t/h
            </text>
          </g>

          {/* Flow particles CORR03 */}
          {running && renderFlowParticles('corr03Path', belts.CORR03?.flow_tph || 0)}

          {/* ===================== BALANCE (Balança) ===================== */}
          <g id="balance" onClick={() => onEquipmentClick?.('BAL01')}>
            <rect
              x="1050"
              y="45"
              width="80"
              height="70"
              fill={alpha(COLORS.equipment.running, 0.3)}
              stroke={COLORS.equipment.running}
              strokeWidth="3"
              rx="5"
              style={{ cursor: 'pointer' }}
            />

            <text x="1090" y="70" textAnchor="middle" fill={COLORS.text} fontSize="12" fontWeight="600">
              BALANÇA
            </text>
            <text x="1090" y="90" textAnchor="middle" fill={COLORS.material} fontSize="16" fontWeight="700">
              {(status?.balance?.current_mass_kg || 0).toFixed(0)} kg
            </text>
            <text x="1090" y="105" textAnchor="middle" fill={COLORS.textDim} fontSize="9">
              {status?.balance?.state || 'IDLE'}
            </text>
          </g>

          {/* ===================== SHIPLOADER ===================== */}
          <g id="shiploader" onClick={() => onEquipmentClick?.('SLD01')}>
            {/* Boom */}
            <line
              x1="1200"
              y1="80"
              x2="1350"
              y2="200"
              stroke={getEquipmentColor(shiploader)}
              strokeWidth="15"
              strokeLinecap="round"
            />

            {/* Tower */}
            <rect
              x="1180"
              y="40"
              width="40"
              height="120"
              fill={alpha(getEquipmentColor(shiploader), 0.5)}
              stroke={getEquipmentColor(shiploader)}
              strokeWidth="3"
              rx="3"
            />

            {/* Material falling animation */}
            {shiploader.running && (
              <g>
                {[0, 1, 2, 3].map(i => (
                  <circle
                    key={`fall-${i}`}
                    cx="1350"
                    cy="200"
                    r="4"
                    fill={COLORS.material}
                  >
                    <animate
                      attributeName="cy"
                      values="200;400"
                      dur="1.5s"
                      begin={`${i * 0.4}s`}
                      repeatCount="indefinite"
                    />
                    <animate
                      attributeName="opacity"
                      values="1;0"
                      dur="1.5s"
                      begin={`${i * 0.4}s`}
                      repeatCount="indefinite"
                    />
                  </circle>
                ))}
              </g>
            )}

            <text x="1200" y="25" textAnchor="middle" fill={COLORS.text} fontSize="14" fontWeight="600">
              SHIPLOADER
            </text>
            <text x="1200" y="180" textAnchor="middle" fill={COLORS.accent} fontSize="13" fontWeight="700">
              SP: {(shiploader.flow_sp_tph || 0).toFixed(0)} t/h
            </text>
          </g>

          {/* ===================== SHIP (Navio) ===================== */}
          <g id="ship">
            <ellipse
              cx="1450"
              cy="500"
              rx="130"
              ry="80"
              fill={alpha('#1e40af', 0.3)}
              stroke="#3b82f6"
              strokeWidth="3"
            />

            {/* Ship cargo hold */}
            <rect
              x="1360"
              y="450"
              width="180"
              height="60"
              fill={alpha(COLORS.material, 0.4)}
              stroke={COLORS.material}
              strokeWidth="2"
              rx="5"
            />

            <text x="1450" y="490" textAnchor="middle" fill={COLORS.text} fontSize="16" fontWeight="600">
              🚢 NAVIO
            </text>
            <text x="1450" y="510" textAnchor="middle" fill={COLORS.accent} fontSize="12">
              {(status?.ship?.loaded_t || 0).toFixed(0)} / {(status?.ship?.capacity_t || 0).toFixed(0)} t
            </text>
          </g>

        </svg>
      </Box>

      {/* Legend */}
      <Box sx={{ mt: 2 }}>
        <Stack direction="row" spacing={3} justifyContent="center">
          {[
            { label: 'Operando', color: COLORS.equipment.running },
            { label: 'Parado', color: COLORS.equipment.stopped },
            { label: 'Atenção', color: COLORS.equipment.warning },
            { label: 'Alarme', color: COLORS.equipment.alarm },
            { label: 'Falha', color: COLORS.equipment.fault },
          ].map(item => (
            <Stack key={item.label} direction="row" spacing={1} alignItems="center">
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  bgcolor: item.color,
                  borderRadius: '50%',
                  border: `2px solid ${alpha(item.color, 0.5)}`,
                }}
              />
              <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                {item.label}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </Box>
    </Paper>
  );
};

export default ModernScadaView;
