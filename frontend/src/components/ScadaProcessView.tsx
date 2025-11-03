/**
 * SCADA Process View - Visualização Lateral com Equipamentos Detalhados
 * 
 * Vista lateral do processo com:
 * - Motores elétricos animados (rotação)
 * - Correias transportadoras em movimento
 * - Instrumentação detalhada (sensores, medidores)
 * - Status de proteções e interlocks
 * - Painéis de controle por equipamento
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Stack,
  IconButton,
  Divider,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  Speed,
  Thermostat,
  ElectricBolt,
  Build,
  Warning,
  CheckCircle,
  Cancel,
  RotateRight,
  OpenInFull,
} from '@mui/icons-material';

interface ScadaProcessViewProps {
  status: any;
  onEquipmentClick?: (equipmentId: string) => void;
}

interface Motor {
  rpm: number;
  current: number;
  voltage: number;
  power: number;
  temperature: number;
  running: boolean;
  alarm: boolean;
}

const COLORS = {
  background: '#0d1117',
  equipment: '#1f2937',
  equipmentActive: '#065f46',
  motor: '#374151',
  motorRunning: '#10b981',
  belt: '#4b5563',
  beltRunning: '#6366f1',
  material: '#fbbf24',
  pipe: '#6b7280',
  structure: '#374151',
  text: '#f9fafb',
  textDim: '#9ca3af',
  alarm: '#ef4444',
  warning: '#f59e0b',
  ok: '#10b981',
  grid: '#1f2937',
  panel: '#111827',
  sensor: '#3b82f6',
};

export const ScadaProcessView: React.FC<ScadaProcessViewProps> = ({
  status,
  onEquipmentClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [motorAngles, setMotorAngles] = useState<{ [key: string]: number }>({});

  const CANVAS_WIDTH = 1600;
  const CANVAS_HEIGHT = 900;

  // Atualiza ângulos dos motores
  useEffect(() => {
    const interval = setInterval(() => {
      setMotorAngles((prev) => {
        const newAngles: { [key: string]: number } = {};
        Object.keys(prev).forEach((key) => {
          const speed = getMotorSpeed(key);
          newAngles[key] = (prev[key] + speed) % 360;
        });
        // Inicializa novos motores
        ['CORR01', 'CORR02', 'CORR03', 'ELV01', 'SLD01'].forEach((id) => {
          if (!(id in prev)) {
            newAngles[id] = 0;
          }
        });
        return { ...prev, ...newAngles };
      });
    }, 50);

    return () => clearInterval(interval);
  }, [status]);

  const getMotorSpeed = (motorId: string): number => {
    if (motorId === 'CORR01' && status?.belts?.CORR01?.running) return 5;
    if (motorId === 'CORR02' && status?.belts?.CORR02?.running) return 4;
    if (motorId === 'CORR03' && status?.belts?.CORR03?.running) return 6;
    if (motorId === 'ELV01' && status?.elevator?.running) return 8;
    if (motorId === 'SLD01' && status?.shiploader?.running) return 3;
    return 0;
  };

  // Desenha motor elétrico
  const drawMotor = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    size: number,
    motorId: string,
    running: boolean,
    alarm: boolean
  ) => {
    const angle = motorAngles[motorId] || 0;

    // Base do motor
    ctx.fillStyle = running ? COLORS.motorRunning : COLORS.motor;
    ctx.fillRect(x - size, y - size / 2, size * 2, size);
    
    // Borda
    ctx.strokeStyle = alarm ? COLORS.alarm : running ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 3;
    ctx.strokeRect(x - size, y - size / 2, size * 2, size);

    // Eixo rotativo
    if (running) {
      ctx.save();
      ctx.translate(x + size, y);
      ctx.rotate((angle * Math.PI) / 180);
      
      // Eixo
      ctx.fillStyle = '#fbbf24';
      ctx.fillRect(-5, -3, 40, 6);
      
      // Polia
      ctx.beginPath();
      ctx.arc(30, 0, 12, 0, Math.PI * 2);
      ctx.fillStyle = '#374151';
      ctx.fill();
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // Marcador de rotação
      ctx.beginPath();
      ctx.moveTo(30, 0);
      ctx.lineTo(30 + 10, 0);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 3;
      ctx.stroke();
      
      ctx.restore();
    }

    // Aletas de ventilação
    for (let i = 0; i < 4; i++) {
      ctx.fillStyle = '#1f2937';
      ctx.fillRect(x - size + 5 + i * 10, y - size / 2 + 5, 6, size - 10);
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.fillText(motorId, x - size / 2, y - size / 2 - 10);

    // Status indicator
    ctx.beginPath();
    ctx.arc(x + size + 10, y - size / 2 - 5, 5, 0, Math.PI * 2);
    ctx.fillStyle = alarm ? COLORS.alarm : running ? COLORS.ok : COLORS.textDim;
    ctx.fill();
  };

  // Desenha correia transportadora
  const drawBelt = (
    ctx: CanvasRenderingContext2D,
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    width: number,
    running: boolean,
    materialLevel: number = 0
  ) => {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const angle = Math.atan2(dy, dx);
    const length = Math.sqrt(dx * dx + dy * dy);

    ctx.save();
    ctx.translate(x1, y1);
    ctx.rotate(angle);

    // Estrutura da correia (base)
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, -width / 2 - 10, length, width + 20);

    // Correia
    ctx.fillStyle = running ? COLORS.beltRunning : COLORS.belt;
    ctx.fillRect(0, -width / 2, length, width);

    // Bordas laterais
    ctx.strokeStyle = '#4b5563';
    ctx.lineWidth = 3;
    ctx.strokeRect(0, -width / 2, length, width);

    // Roletes (idlers)
    const numRollers = Math.floor(length / 100);
    for (let i = 0; i <= numRollers; i++) {
      const rx = (i * length) / numRollers;
      ctx.fillStyle = '#374151';
      ctx.beginPath();
      ctx.arc(rx, width / 2 + 8, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(rx, -width / 2 - 8, 6, 0, Math.PI * 2);
      ctx.fill();
    }

    // Material na correia
    if (running && materialLevel > 0) {
      const offset = (Date.now() / 20) % 30;
      const numPiles = Math.floor(length / 30);
      
      for (let i = 0; i < numPiles; i++) {
        const px = (i * 30 + offset) % length;
        const pileHeight = (materialLevel / 100) * (width / 2);
        
        // Pilha de material
        ctx.fillStyle = COLORS.material;
        ctx.beginPath();
        ctx.moveTo(px - 10, 0);
        ctx.lineTo(px, -pileHeight);
        ctx.lineTo(px + 10, 0);
        ctx.closePath();
        ctx.fill();
      }
    }

    // Linhas de movimento
    if (running) {
      ctx.strokeStyle = 'rgba(251, 191, 36, 0.3)';
      ctx.lineWidth = 2;
      const animOffset = (Date.now() / 30) % 20;
      for (let x = -animOffset; x < length; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, -width / 4);
        ctx.lineTo(x + 10, width / 4);
        ctx.stroke();
      }
    }

    ctx.restore();
  };

  // Desenha comporta (gate)
  const drawGate = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    openPct: number,
    flow: number
  ) => {
    const gateWidth = 60;
    const gateHeight = 80;

    // Estrutura do silo
    ctx.fillStyle = '#374151';
    ctx.fillRect(x - gateWidth, y - 100, gateWidth * 2, 100);
    ctx.strokeStyle = '#6b7280';
    ctx.lineWidth = 2;
    ctx.strokeRect(x - gateWidth, y - 100, gateWidth * 2, 100);

    // Comporta móvel
    const gatePos = (openPct / 100) * gateHeight;
    ctx.fillStyle = openPct > 5 ? '#10b981' : '#4b5563';
    ctx.fillRect(x - gateWidth / 2, y - gatePos, gateWidth, 8);
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    ctx.strokeRect(x - gateWidth / 2, y - gatePos, gateWidth, 8);

    // Fluxo de material
    if (flow > 0.1) {
      const particles = 8;
      for (let i = 0; i < particles; i++) {
        const offset = (Date.now() / 20 + i * 10) % 100;
        const px = x + (Math.random() - 0.5) * 30;
        const py = y + offset;
        
        ctx.fillStyle = COLORS.material;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Label de abertura
    ctx.fillStyle = COLORS.text;
    ctx.font = '12px monospace';
    ctx.fillText(`${openPct.toFixed(0)}%`, x - 15, y - gatePos - 15);
  };

  // Desenha sensor
  const drawSensor = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    type: string,
    value: string,
    alarm: boolean
  ) => {
    // Corpo do sensor
    ctx.fillStyle = alarm ? COLORS.alarm : COLORS.sensor;
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = COLORS.text;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Ícone do tipo
    ctx.fillStyle = COLORS.text;
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    const icon = type === 'temp' ? 'T' : type === 'speed' ? 'V' : type === 'level' ? 'L' : 'S';
    ctx.fillText(icon, x, y + 4);

    // Linha de conexão
    ctx.strokeStyle = alarm ? COLORS.alarm : COLORS.sensor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + 30, y - 20);
    ctx.stroke();

    // Valor
    ctx.fillStyle = COLORS.text;
    ctx.font = '11px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(value, x + 35, y - 20);
  };

  // Desenha o processo completo
  const drawProcess = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Limpa canvas
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Grid de fundo
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    for (let x = 0; x < CANVAS_WIDTH; x += 100) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, CANVAS_HEIGHT);
      ctx.stroke();
    }
    for (let y = 0; y < CANVAS_HEIGHT; y += 100) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(CANVAS_WIDTH, y);
      ctx.stroke();
    }

    // ========== WAREHOUSE (SILO) ==========
    const siloX = 100;
    const siloY = 200;
    const siloWidth = 150;
    const siloHeight = 300;

    // Corpo do silo
    ctx.fillStyle = COLORS.equipment;
    ctx.fillRect(siloX, siloY, siloWidth, siloHeight);
    ctx.strokeStyle = COLORS.textDim;
    ctx.lineWidth = 3;
    ctx.strokeRect(siloX, siloY, siloWidth, siloHeight);

    // Nível de material
    const fillLevel = (status?.warehouse_inventory_t || 0) / 10000;
    const fillHeight = siloHeight * Math.min(fillLevel, 1);
    ctx.fillStyle = COLORS.material;
    ctx.fillRect(siloX, siloY + siloHeight - fillHeight, siloWidth, fillHeight);

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 16px monospace';
    ctx.fillText('WAREHOUSE', siloX + 10, siloY - 10);
    ctx.font = '14px monospace';
    ctx.fillText(`${(status?.warehouse_inventory_t || 0).toFixed(0)} t`, siloX + 20, siloY + 30);

    // Sensor de nível
    drawSensor(ctx, siloX + siloWidth + 20, siloY + 50, 'level', `${(fillLevel * 100).toFixed(0)}%`, fillLevel > 0.9);

    // ========== GATE 1 ==========
    const gate1X = siloX + siloWidth / 2;
    const gate1Y = siloY + siloHeight;
    const gate1Data = status?.gates?.[0];
    drawGate(ctx, gate1X, gate1Y, gate1Data?.open_pct || 0, gate1Data?.flow_tph || 0);

    // ========== CORREIA 01 (CORR01) ==========
    const corr01StartX = gate1X;
    const corr01StartY = gate1Y + 100;
    const corr01EndX = 600;
    const corr01EndY = corr01StartY;
    const corr01Running = status?.belts?.CORR01?.running || false;
    const corr01Flow = gate1Data?.flow_tph || 0;

    // Motor CORR01
    drawMotor(ctx, corr01StartX - 100, corr01StartY, 25, 'CORR01', corr01Running, false);

    // Correia CORR01
    drawBelt(
      ctx,
      corr01StartX,
      corr01StartY,
      corr01EndX,
      corr01EndY,
      40,
      corr01Running,
      corr01Flow > 0 ? 60 : 0
    );

    // Sensores CORR01
    const corr01Speed = status?.belts?.CORR01?.speed_mps || 0;
    drawSensor(ctx, corr01StartX + 150, corr01StartY - 80, 'speed', `${corr01Speed.toFixed(2)} m/s`, false);
    drawSensor(ctx, corr01StartX + 300, corr01StartY - 80, 'temp', '42°C', false);

    // ========== CORREIA 02 (CORR02) - Vertical ==========
    const corr02StartX = corr01EndX;
    const corr02StartY = corr01EndY;
    const corr02EndX = corr02StartX;
    const corr02EndY = 250;
    const corr02Running = status?.belts?.CORR02?.running || false;

    // Motor CORR02
    drawMotor(ctx, corr02StartX + 80, corr02StartY, 25, 'CORR02', corr02Running, false);

    // Correia CORR02
    drawBelt(
      ctx,
      corr02StartX,
      corr02StartY,
      corr02EndX,
      corr02EndY,
      40,
      corr02Running,
      corr01Flow > 0 ? 50 : 0
    );

    // ========== ELEVATOR ==========
    const elevX = corr02EndX;
    const elevY = corr02EndY;
    const elevEndY = 100;
    const elevRunning = status?.elevator?.running || false;

    // Estrutura do elevador
    ctx.fillStyle = COLORS.equipment;
    ctx.fillRect(elevX - 40, elevEndY, 80, elevY - elevEndY);
    ctx.strokeStyle = elevRunning ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 3;
    ctx.strokeRect(elevX - 40, elevEndY, 80, elevY - elevEndY);

    // Motor do elevador
    drawMotor(ctx, elevX + 100, elevY - 50, 30, 'ELV01', elevRunning, false);

    // Caçambas do elevador
    if (elevRunning) {
      const numBuckets = 8;
      const bucketSpacing = (elevY - elevEndY) / numBuckets;
      const offset = ((Date.now() / 50) % bucketSpacing);
      
      for (let i = 0; i < numBuckets; i++) {
        const by = elevY - offset - i * bucketSpacing;
        if (by >= elevEndY && by <= elevY) {
          ctx.fillStyle = '#fbbf24';
          ctx.fillRect(elevX - 20, by, 40, 15);
          ctx.strokeStyle = '#d97706';
          ctx.lineWidth = 2;
          ctx.strokeRect(elevX - 20, by, 40, 15);
        }
      }
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 14px monospace';
    ctx.fillText('ELEVATOR', elevX - 35, elevEndY - 10);

    // Sensores
    const elevSpeed = status?.elevator?.speed_mps || 0;
    drawSensor(ctx, elevX + 60, elevY - 150, 'speed', `${elevSpeed.toFixed(2)} m/s`, false);

    // ========== CORREIA 03 (CORR03) - Superior ==========
    const corr03StartX = elevX;
    const corr03StartY = elevEndY;
    const corr03EndX = 1200;
    const corr03EndY = corr03StartY;
    const corr03Running = status?.belts?.CORR03?.running || false;

    // Motor CORR03
    drawMotor(ctx, corr03StartX + 80, corr03StartY - 60, 28, 'CORR03', corr03Running, false);

    // Correia CORR03
    drawBelt(
      ctx,
      corr03StartX,
      corr03StartY,
      corr03EndX,
      corr03EndY,
      40,
      corr03Running,
      corr01Flow > 0 ? 55 : 0
    );

    // Sensores CORR03
    const corr03Speed = status?.belts?.CORR03?.speed_mps || 0;
    drawSensor(ctx, corr03StartX + 250, corr03StartY - 80, 'speed', `${corr03Speed.toFixed(2)} m/s`, false);

    // ========== BALANCE ==========
    const balanceX = corr03StartX + 400;
    const balanceY = corr03StartY;
    const balanceWeight = status?.balance?.weight_t || 0;

    // Estrutura da balança
    ctx.fillStyle = COLORS.equipment;
    ctx.fillRect(balanceX - 40, balanceY - 20, 80, 60);
    ctx.strokeStyle = balanceWeight > 0.1 ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 3;
    ctx.strokeRect(balanceX - 40, balanceY - 20, 80, 60);

    // Display da balança
    ctx.fillStyle = '#000000';
    ctx.fillRect(balanceX - 30, balanceY - 10, 60, 30);
    ctx.fillStyle = '#00ff00';
    ctx.font = 'bold 14px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`${balanceWeight.toFixed(1)}t`, balanceX, balanceY + 10);

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('BALANCE', balanceX, balanceY - 35);

    // ========== SHIPLOADER ==========
    const shiploadX = corr03EndX;
    const shiploadY = corr03EndY;
    const shiploadRunning = status?.shiploader?.running || false;
    const shiploadFlow = status?.shiploader?.flow_tph || 0;

    // Estrutura do shiploader
    ctx.fillStyle = COLORS.equipment;
    ctx.fillRect(shiploadX - 50, shiploadY - 40, 100, 180);
    ctx.strokeStyle = shiploadRunning ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 3;
    ctx.strokeRect(shiploadX - 50, shiploadY - 40, 100, 180);

    // Motor do shiploader
    drawMotor(ctx, shiploadX - 150, shiploadY + 20, 30, 'SLD01', shiploadRunning, false);

    // Braço do shiploader
    ctx.strokeStyle = COLORS.structure;
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(shiploadX, shiploadY);
    ctx.lineTo(shiploadX + 120, shiploadY + 180);
    ctx.stroke();

    // Fluxo de material caindo
    if (shiploadRunning && shiploadFlow > 0) {
      for (let i = 0; i < 15; i++) {
        const offset = (Date.now() / 20 + i * 15) % 200;
        const px = shiploadX + 120 + (Math.random() - 0.5) * 20;
        const py = shiploadY + 180 + offset;
        
        ctx.fillStyle = COLORS.material;
        ctx.beginPath();
        ctx.arc(px, py, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 14px monospace';
    ctx.textAlign = 'left';
    ctx.fillText('SHIPLOADER', shiploadX - 45, shiploadY - 50);
    ctx.font = '12px monospace';
    ctx.fillText(`${shiploadFlow.toFixed(0)} t/h`, shiploadX - 45, shiploadY - 30);

    // ========== NAVIO ==========
    const shipX = shiploadX + 150;
    const shipY = shiploadY + 380;

    // Casco do navio
    ctx.fillStyle = '#1e40af';
    ctx.fillRect(shipX - 50, shipY, 400, 120);
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 3;
    ctx.strokeRect(shipX - 50, shipY, 400, 120);

    // Porões
    for (let i = 0; i < 4; i++) {
      const holdX = shipX + i * 90;
      ctx.strokeStyle = '#60a5fa';
      ctx.lineWidth = 2;
      ctx.strokeRect(holdX, shipY + 20, 70, 90);
      
      // Material carregado
      const loadPct = 0.35; // TODO: conectar com dados reais
      ctx.fillStyle = COLORS.material;
      ctx.fillRect(holdX, shipY + 110 - loadPct * 90, 70, loadPct * 90);
    }

    // Nome do navio
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 16px monospace';
    ctx.fillText('MV PACIFIC GLORY', shipX, shipY - 10);

    // ========== HUD SUPERIOR ==========
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(0, 0, CANVAS_WIDTH, 50);

    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 18px monospace';
    ctx.textAlign = 'left';
    ctx.fillText('⚡ OPTIFLOW SMARTPORT - PROCESS VIEW', 20, 30);

    // Status
    const running = status?.running || false;
    ctx.fillStyle = running ? COLORS.ok : COLORS.alarm;
    ctx.fillText(running ? '● RUNNING' : '● STOPPED', CANVAS_WIDTH - 250, 30);

    // Tempo
    ctx.fillStyle = COLORS.text;
    ctx.font = '14px monospace';
    const timeS = status?.time_s || 0;
    const hours = Math.floor(timeS / 3600);
    const mins = Math.floor((timeS % 3600) / 60);
    const secs = Math.floor(timeS % 60);
    ctx.fillText(
      `⏱ ${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`,
      CANVAS_WIDTH - 550,
      30
    );
  };

  useEffect(() => {
    const animate = () => {
      drawProcess();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [status, motorAngles]);

  // Dados dos equipamentos para os painéis laterais
  const equipmentData = [
    {
      id: 'CORR01',
      name: 'Correia 01',
      type: 'Belt Conveyor',
      motor: {
        power: 75,
        current: status?.belts?.CORR01?.running ? 142 : 0,
        voltage: 380,
        rpm: status?.belts?.CORR01?.running ? 1750 : 0,
        temp: status?.belts?.CORR01?.running ? 65 : 25,
      },
      speed: status?.belts?.CORR01?.speed_mps || 0,
      running: status?.belts?.CORR01?.running || false,
    },
    {
      id: 'ELV01',
      name: 'Elevador',
      type: 'Bucket Elevator',
      motor: {
        power: 225,
        current: status?.elevator?.running ? 380 : 0,
        voltage: 380,
        rpm: status?.elevator?.running ? 980 : 0,
        temp: status?.elevator?.running ? 72 : 28,
      },
      speed: status?.elevator?.speed_mps || 0,
      running: status?.elevator?.running || false,
    },
    {
      id: 'SLD01',
      name: 'Shiploader',
      type: 'Ship Loader',
      motor: {
        power: 320,
        current: status?.shiploader?.running ? 520 : 0,
        voltage: 380,
        rpm: status?.shiploader?.running ? 750 : 0,
        temp: status?.shiploader?.running ? 68 : 26,
      },
      flow: status?.shiploader?.flow_tph || 0,
      running: status?.shiploader?.running || false,
    },
  ];

  return (
    <Grid container spacing={2} sx={{ height: '100%', p: 2, bgcolor: '#0a0e14' }}>
      {/* Canvas Principal */}
      <Grid size={{ xs: 12, md: 9 }}>
        <Paper
          elevation={3}
          sx={{
            bgcolor: COLORS.background,
            p: 2,
            borderRadius: 2,
            border: '2px solid #1f2937',
            height: '900px',
            overflow: 'auto',
          }}
        >
          <canvas
            ref={canvasRef}
            width={CANVAS_WIDTH}
            height={CANVAS_HEIGHT}
            style={{
              display: 'block',
              imageRendering: 'crisp-edges',
            }}
          />
        </Paper>
      </Grid>

      {/* Painéis de Equipamentos */}
      <Grid size={{ xs: 12, md: 3 }}>
        <Stack spacing={2}>
          {equipmentData.map((equip) => (
            <Card
              key={equip.id}
              sx={{
                bgcolor: COLORS.panel,
                border: equip.running ? `2px solid ${COLORS.ok}` : `1px solid ${COLORS.textDim}`,
              }}
            >
              <CardContent>
                <Stack spacing={1}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="h6" sx={{ color: COLORS.text, fontSize: '14px' }}>
                      {equip.name}
                    </Typography>
                    <Chip
                      size="small"
                      icon={equip.running ? <CheckCircle /> : <Cancel />}
                      label={equip.running ? 'RUN' : 'STOP'}
                      color={equip.running ? 'success' : 'default'}
                    />
                  </Stack>

                  <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                    {equip.type}
                  </Typography>

                  <Divider sx={{ bgcolor: COLORS.textDim, my: 1 }} />

                  {/* Motor Data */}
                  <Typography variant="caption" sx={{ color: COLORS.text, fontWeight: 'bold' }}>
                    MOTOR
                  </Typography>

                  <Grid container spacing={1}>
                    <Grid size={{ xs: 6 }}>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <ElectricBolt sx={{ fontSize: 14, color: COLORS.warning }} />
                        <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                          {equip.motor.power} kW
                        </Typography>
                      </Stack>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                      <Typography variant="caption" sx={{ color: COLORS.text }}>
                        {equip.motor.current.toFixed(0)} A
                        </Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <RotateRight sx={{ fontSize: 14, color: COLORS.sensor }} />
                        <Typography variant="caption" sx={{ color: COLORS.text }}>
                          {equip.motor.rpm} rpm
                        </Typography>
                      </Stack>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <Thermostat sx={{ fontSize: 14, color: equip.motor.temp > 70 ? COLORS.alarm : COLORS.ok }} />
                        <Typography variant="caption" sx={{ color: COLORS.text }}>
                          {equip.motor.temp}°C
                        </Typography>
                      </Stack>
                    </Grid>
                  </Grid>

                  {/* Speed/Flow */}
                  {equip.speed !== undefined && (
                    <>
                      <Divider sx={{ bgcolor: COLORS.textDim, my: 0.5 }} />
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                          Speed:
                        </Typography>
                        <Typography variant="caption" sx={{ color: COLORS.text }}>
                          {equip.speed.toFixed(2)} m/s
                        </Typography>
                      </Stack>
                    </>
                  )}

                  {equip.flow !== undefined && (
                    <>
                      <Divider sx={{ bgcolor: COLORS.textDim, my: 0.5 }} />
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                          Flow:
                        </Typography>
                        <Typography variant="caption" sx={{ color: COLORS.text }}>
                          {equip.flow.toFixed(0)} t/h
                        </Typography>
                      </Stack>
                    </>
                  )}

                  {/* Temperatura do motor como progress bar */}
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                      Temperature
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={(equip.motor.temp / 100) * 100}
                      sx={{
                        height: 6,
                        borderRadius: 1,
                        bgcolor: '#374151',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: equip.motor.temp > 70 ? COLORS.alarm : equip.motor.temp > 60 ? COLORS.warning : COLORS.ok,
                        },
                      }}
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          ))}

          {/* Alarms & Interlocks */}
          <Card sx={{ bgcolor: COLORS.panel, border: `1px solid ${COLORS.textDim}` }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: COLORS.text, fontSize: '14px', mb: 1 }}>
                System Status
              </Typography>
              <Stack spacing={1}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                    Alarms:
                  </Typography>
                  <Chip
                    size="small"
                    label={Array.isArray(status?.alarms) ? status.alarms.filter((a: any) => a.active).length : 0}
                    color="error"
                  />
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                    Interlocks:
                  </Typography>
                  <Chip
                    size="small"
                    label={status?.interlocks?.active_count || 0}
                    color="warning"
                  />
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" sx={{ color: COLORS.textDim }}>
                    DEM Particles:
                  </Typography>
                  <Typography variant="caption" sx={{ color: COLORS.text }}>
                    {status?.dem_physics?.particle_count || 0}
                  </Typography>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Grid>
    </Grid>
  );
};

export default ScadaProcessView;
