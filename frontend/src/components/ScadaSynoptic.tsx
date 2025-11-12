/**
 * SCADA Synoptic Viewer - Interface Industrial para Simulador
 * 
 * Visualização tipo SCADA com:
 * - Layout do terminal portuário
 * - Animações de equipamentos em operação
 * - Fluxo de material em tempo real
 * - Indicadores e controles industriais
 */

import React, { useEffect, useRef, useState } from 'react';
import { Box, Paper, Typography, IconButton, Chip, Stack } from '@mui/material';
import {
  PlayArrow,
  Stop,
  Warning,
  Settings,
  Speed,
  Thermostat,
  Timeline,
} from '@mui/icons-material';
import apiClient from '../api/client';

interface ScadaSynopticProps {
  status: any;
  onCommand?: (command: string, params?: any) => void;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
}

export const ScadaSynoptic: React.FC<ScadaSynopticProps> = ({ status, onCommand }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const particlesRef = useRef<Particle[]>([]);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [shipLoadPct, setShipLoadPct] = useState<number>(0);
  const [totalMassLoaded, setTotalMassLoaded] = useState<number>(0);

  // Dimensões do canvas
  const CANVAS_WIDTH = 1400;
  const CANVAS_HEIGHT = 800;

  // Cores SCADA industriais
  const COLORS = {
    background: '#1a1a2e',
    equipment: '#16213e',
    equipmentActive: '#0f3460',
    belt: '#533483',
    beltActive: '#7c3aed',
    pipe: '#374151',
    material: '#fbbf24',
    materialFlow: '#f59e0b',
    text: '#e5e7eb',
    textDim: '#9ca3af',
    alarm: '#ef4444',
    warning: '#f59e0b',
    ok: '#10b981',
    grid: '#2d3748',
  };

  // Coordenadas dos equipamentos (proporcionais ao layout real)
  const LAYOUT = {
    warehouse: { x: 50, y: 200, width: 120, height: 180 },
    gates: [
      { id: 1, x: 170, y: 230, width: 30, height: 40 },
      { id: 2, x: 170, y: 280, width: 30, height: 40 },
      { id: 3, x: 170, y: 330, width: 30, height: 40 },
      { id: 4, x: 170, y: 380, width: 30, height: 40 },
    ],
    corr01: { x: 200, y: 300, x2: 450, y2: 300, width: 40 },
    corr02: { x: 450, y: 300, x2: 450, y2: 150, width: 40 },
    elevator: { x: 450, y: 150, x2: 450, y2: 50, width: 50 },
    corr03: { x: 450, y: 50, x2: 900, y2: 50, width: 40 },
    balance: { x: 700, y: 30, width: 60, height: 60 },
    shiploader: { x: 950, y: 20, width: 80, height: 100 },
    ship: { x: 1050, y: 50, width: 300, height: 200 },
  };

  // Inicializa partículas de fluxo
  const initParticles = () => {
    particlesRef.current = [];
  };

  // Fetch real-time data from tags
  const fetchRealTimeData = async () => {
    try {
      const tags = await apiClient.getTags();
      
      // Find TOTAL_MASS_T_PV tag for ship load
      const totalMassTag = tags.find(t => t.name === 'TOTAL_MASS_T_PV');
      if (totalMassTag && typeof totalMassTag.last_value === 'number') {
        setTotalMassLoaded(totalMassTag.last_value);
        
        // Calculate percentage (assuming 65,000t capacity)
        const shipCapacity = 65000;
        const loadPct = Math.min((totalMassTag.last_value / shipCapacity) * 100, 100);
        setShipLoadPct(loadPct / 100); // Normalize to 0-1
      }
    } catch (error) {
      console.error('Error fetching real-time data:', error);
    }
  };

  // Spawna novas partículas baseado no fluxo
  const spawnParticles = (
    x: number,
    y: number,
    vx: number,
    vy: number,
    count: number = 1
  ) => {
    for (let i = 0; i < count; i++) {
      particlesRef.current.push({
        x: x + Math.random() * 10 - 5,
        y: y + Math.random() * 10 - 5,
        vx: vx + Math.random() * 0.5 - 0.25,
        vy: vy + Math.random() * 0.5 - 0.25,
        size: 3 + Math.random() * 3,
        color: COLORS.material,
      });
    }

    // Limita número de partículas para performance
    if (particlesRef.current.length > 500) {
      particlesRef.current = particlesRef.current.slice(-500);
    }
  };

  // Atualiza posição das partículas
  const updateParticles = () => {
    particlesRef.current = particlesRef.current.filter((p) => {
      p.x += p.vx;
      p.y += p.vy;

      // Remove partículas fora do canvas
      return p.x >= 0 && p.x <= CANVAS_WIDTH && p.y >= 0 && p.y <= CANVAS_HEIGHT;
    });
  };

  // Desenha o synoptic
  const drawSynoptic = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Safety check: ensure status has basic structure
    if (!status) {
      // Draw empty/loading state
      ctx.fillStyle = COLORS.background;
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
      ctx.fillStyle = COLORS.text;
      ctx.font = '24px monospace';
      ctx.fillText('Loading...', CANVAS_WIDTH / 2 - 60, CANVAS_HEIGHT / 2);
      return;
    }

    // Limpa canvas
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Grid de fundo (estilo SCADA)
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    for (let x = 0; x < CANVAS_WIDTH; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, CANVAS_HEIGHT);
      ctx.stroke();
    }
    for (let y = 0; y < CANVAS_HEIGHT; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(CANVAS_WIDTH, y);
      ctx.stroke();
    }

    // ========== WAREHOUSE ==========
    const warehouse = LAYOUT.warehouse;
    const warehouseRunning = status?.running || false;
    ctx.fillStyle = warehouseRunning ? COLORS.equipmentActive : COLORS.equipment;
    ctx.fillRect(warehouse.x, warehouse.y, warehouse.width, warehouse.height);
    ctx.strokeStyle = warehouseRunning ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 2;
    ctx.strokeRect(warehouse.x, warehouse.y, warehouse.width, warehouse.height);

    // Nível do warehouse
    const fillLevel = (status?.warehouse_inventory_t || 0) / 10000; // 10000t max
    ctx.fillStyle = COLORS.material;
    const fillHeight = warehouse.height * Math.min(fillLevel, 1);
    ctx.fillRect(
      warehouse.x,
      warehouse.y + warehouse.height - fillHeight,
      warehouse.width,
      fillHeight
    );

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 14px monospace';
    ctx.fillText('WAREHOUSE', warehouse.x, warehouse.y - 10);
    ctx.font = '12px monospace';
    ctx.fillText(
      `${(status?.warehouse_inventory_t || 0).toFixed(0)}t`,
      warehouse.x + 10,
      warehouse.y + 20
    );

    // ========== GATES ==========
    if (Array.isArray(status?.gates)) {
      LAYOUT.gates.forEach((gate, idx) => {
        const gateData = status?.gates?.[idx];
        const openPct = gateData?.open_pct || 0;
        const flow = gateData?.flow_tph || 0;
        const isActive = flow > 0.1;

      // Gate body
      ctx.fillStyle = isActive ? COLORS.beltActive : COLORS.equipment;
      ctx.fillRect(gate.x, gate.y, gate.width, gate.height);
      ctx.strokeStyle = isActive ? COLORS.ok : COLORS.textDim;
      ctx.lineWidth = 2;
      ctx.strokeRect(gate.x, gate.y, gate.width, gate.height);

      // Abertura
      const openHeight = (gate.height * openPct) / 100;
      ctx.fillStyle = COLORS.materialFlow;
      ctx.fillRect(gate.x + 5, gate.y + gate.height - openHeight, gate.width - 10, 3);

      // Label
      ctx.fillStyle = COLORS.text;
      ctx.font = '10px monospace';
      ctx.fillText(`G${gate.id}`, gate.x + 8, gate.y + gate.height / 2);
      ctx.fillText(`${openPct.toFixed(0)}%`, gate.x + 5, gate.y + gate.height / 2 + 12);

      // Spawna partículas se gate ativa
      if (isActive && Math.random() < flow / 200) {
        spawnParticles(gate.x + gate.width, gate.y + gate.height - 5, 2, 0, 1);
      }
    });
    } // End if Array.isArray(status?.gates)

    // ========== CORREIA 01 (Horizontal) ==========
    const corr01 = LAYOUT.corr01;
    const belt01Running = status?.belts?.CORR01?.running;
    const belt01Speed = status?.belts?.CORR01?.speed_mps || 0;

    // Belt body
    ctx.fillStyle = belt01Running ? COLORS.beltActive : COLORS.belt;
    ctx.fillRect(corr01.x, corr01.y - corr01.width / 2, corr01.x2 - corr01.x, corr01.width);
    ctx.strokeStyle = belt01Running ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 2;
    ctx.strokeRect(
      corr01.x,
      corr01.y - corr01.width / 2,
      corr01.x2 - corr01.x,
      corr01.width
    );

    // Animação de movimento (linhas diagonais)
    if (belt01Running && belt01Speed > 0) {
      ctx.strokeStyle = COLORS.materialFlow;
      ctx.lineWidth = 2;
      const spacing = 20;
      const offset = (Date.now() / 50) % spacing;
      for (let x = corr01.x - offset; x < corr01.x2; x += spacing) {
        ctx.beginPath();
        ctx.moveTo(x, corr01.y - 15);
        ctx.lineTo(x + 10, corr01.y + 15);
        ctx.stroke();
      }
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.fillText('CORR01', corr01.x + 80, corr01.y - 30);
    ctx.font = '10px monospace';
    ctx.fillText(
      `${belt01Speed.toFixed(2)} m/s`,
      corr01.x + 80,
      corr01.y - 15
    );

    // ========== CORREIA 02 (Vertical) ==========
    const corr02 = LAYOUT.corr02;
    const belt02Running = status?.belts?.CORR02?.running;
    const belt02Speed = status?.belts?.CORR02?.speed_mps || 0;

    ctx.fillStyle = belt02Running ? COLORS.beltActive : COLORS.belt;
    ctx.fillRect(
      corr02.x - corr02.width / 2,
      corr02.y2,
      corr02.width,
      corr02.y - corr02.y2
    );
    ctx.strokeStyle = belt02Running ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 2;
    ctx.strokeRect(
      corr02.x - corr02.width / 2,
      corr02.y2,
      corr02.width,
      corr02.y - corr02.y2
    );

    // Animação
    if (belt02Running && belt02Speed > 0) {
      ctx.strokeStyle = COLORS.materialFlow;
      ctx.lineWidth = 2;
      const spacing = 20;
      const offset = (Date.now() / 50) % spacing;
      for (let y = corr02.y - offset; y > corr02.y2; y -= spacing) {
        ctx.beginPath();
        ctx.moveTo(corr02.x - 15, y);
        ctx.lineTo(corr02.x + 15, y - 10);
        ctx.stroke();
      }
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.fillText('CORR02', corr02.x + 30, corr02.y - 80);

    // ========== ELEVATOR ==========
    const elev = LAYOUT.elevator;
    const elevRunning = status?.elevator?.running;
    const elevSpeed = status?.elevator?.speed_mps || 0;

    ctx.fillStyle = elevRunning ? COLORS.equipmentActive : COLORS.equipment;
    ctx.fillRect(elev.x - elev.width / 2, elev.y2, elev.width, elev.y - elev.y2);
    ctx.strokeStyle = elevRunning ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 3;
    ctx.strokeRect(elev.x - elev.width / 2, elev.y2, elev.width, elev.y - elev.y2);

    // Caçambas subindo
    if (elevRunning && elevSpeed > 0) {
      ctx.fillStyle = COLORS.materialFlow;
      const numBuckets = 8;
      const offset = (Date.now() / 100) % ((elev.y - elev.y2) / numBuckets);
      for (let i = 0; i < numBuckets; i++) {
        const by = elev.y - offset - i * ((elev.y - elev.y2) / numBuckets);
        if (by > elev.y2 && by < elev.y) {
          ctx.fillRect(elev.x - 15, by, 30, 8);
        }
      }
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.fillText('ELEVATOR', elev.x - 35, elev.y2 - 10);
    ctx.font = '10px monospace';
    ctx.fillText(`${elevSpeed.toFixed(2)} m/s`, elev.x - 30, elev.y - 10);

    // ========== CORREIA 03 (Horizontal superior) ==========
    const corr03 = LAYOUT.corr03;
    const belt03Running = status?.belts?.CORR03?.running;
    const belt03Speed = status?.belts?.CORR03?.speed_mps || 0;

    ctx.fillStyle = belt03Running ? COLORS.beltActive : COLORS.belt;
    ctx.fillRect(corr03.x, corr03.y - corr03.width / 2, corr03.x2 - corr03.x, corr03.width);
    ctx.strokeStyle = belt03Running ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 2;
    ctx.strokeRect(
      corr03.x,
      corr03.y - corr03.width / 2,
      corr03.x2 - corr03.x,
      corr03.width
    );

    // Animação
    if (belt03Running && belt03Speed > 0) {
      ctx.strokeStyle = COLORS.materialFlow;
      ctx.lineWidth = 2;
      const spacing = 20;
      const offset = (Date.now() / 50) % spacing;
      for (let x = corr03.x - offset; x < corr03.x2; x += spacing) {
        ctx.beginPath();
        ctx.moveTo(x, corr03.y - 15);
        ctx.lineTo(x + 10, corr03.y + 15);
        ctx.stroke();
      }
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.fillText('CORR03', corr03.x + 180, corr03.y - 30);

    // ========== BALANCE ==========
    const balance = LAYOUT.balance;
    const balanceRunning = status?.balance?.running;
    const balanceWeight = status?.balance?.weight_t || 0;

    ctx.fillStyle = balanceRunning ? COLORS.equipmentActive : COLORS.equipment;
    ctx.fillRect(balance.x, balance.y, balance.width, balance.height);
    ctx.strokeStyle = balanceRunning ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 2;
    ctx.strokeRect(balance.x, balance.y, balance.width, balance.height);

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.fillText('BALANCE', balance.x - 10, balance.y - 10);
    ctx.font = '11px monospace';
    ctx.fillText(`${balanceWeight.toFixed(1)}t`, balance.x + 5, balance.y + 35);

    // ========== SHIPLOADER ==========
    const shiploader = LAYOUT.shiploader;
    const shipRunning = status?.shiploader?.running;
    const shipFlow = status?.shiploader?.flow_tph || 0;

    ctx.fillStyle = shipRunning ? COLORS.equipmentActive : COLORS.equipment;
    ctx.fillRect(shiploader.x, shiploader.y, shiploader.width, shiploader.height);
    ctx.strokeStyle = shipRunning ? COLORS.ok : COLORS.textDim;
    ctx.lineWidth = 3;
    ctx.strokeRect(shiploader.x, shiploader.y, shiploader.width, shiploader.height);

    // Braço do shiploader
    ctx.strokeStyle = shipRunning ? COLORS.beltActive : COLORS.belt;
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(shiploader.x + shiploader.width / 2, shiploader.y + 20);
    ctx.lineTo(shiploader.x + shiploader.width + 80, shiploader.y + 80);
    ctx.stroke();

    // Fluxo caindo
    if (shipRunning && shipFlow > 0) {
      ctx.strokeStyle = COLORS.materialFlow;
      ctx.lineWidth = 6;
      const particleCount = 5;
      for (let i = 0; i < particleCount; i++) {
        const offset = (Date.now() / 30 + i * 15) % 100;
        ctx.beginPath();
        ctx.moveTo(
          shiploader.x + shiploader.width + 80,
          shiploader.y + 80 + offset
        );
        ctx.lineTo(
          shiploader.x + shiploader.width + 80,
          shiploader.y + 80 + offset + 10
        );
        ctx.stroke();
      }
    }

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 12px monospace';
    ctx.fillText('SHIPLOADER', shiploader.x - 5, shiploader.y - 10);
    ctx.font = '10px monospace';
    ctx.fillText(`${shipFlow.toFixed(0)} t/h`, shiploader.x + 5, shiploader.y + 15);

    // ========== SHIP (NAVIO) ==========
    const ship = LAYOUT.ship;
    ctx.fillStyle = '#1e3a5f';
    ctx.fillRect(ship.x, ship.y, ship.width, ship.height);
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.strokeRect(ship.x, ship.y, ship.width, ship.height);

    // Porões (holds)
    for (let i = 0; i < 4; i++) {
      const holdX = ship.x + 20 + i * 70;
      ctx.strokeStyle = '#60a5fa';
      ctx.lineWidth = 1;
      ctx.strokeRect(holdX, ship.y + 30, 50, 150);
      
      // Nível de carga - usando dados reais do TOTAL_MASS_T_PV
      const loadedPct = shipLoadPct; // Connected to real-time data
      ctx.fillStyle = COLORS.material;
      const holdFill = 150 * loadedPct;
      ctx.fillRect(holdX, ship.y + 180 - holdFill, 50, holdFill);
    }

    // Label - usando massa real carregada
    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 14px monospace';
    ctx.fillText('MV PACIFIC GLORY', ship.x + 50, ship.y + 15);
    ctx.font = '11px monospace';
    const loadedTons = Math.round(totalMassLoaded);
    const loadPctDisplay = (shipLoadPct * 100).toFixed(1);
    ctx.fillText(
      `DWT: 65,000t | Loaded: ${loadedTons.toLocaleString()}t (${loadPctDisplay}%)`,
      ship.x + 20,
      ship.y + 220
    );

    // ========== PARTÍCULAS DE FLUXO ==========
    updateParticles();
    particlesRef.current.forEach((p) => {
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    });

    // ========== HUD - INFO GERAL ==========
    // Status bar superior
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(0, 0, CANVAS_WIDTH, 35);

    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 16px monospace';
    ctx.fillText('⚡ OPTIFLOW SMARTPORT - TERMINAL GRANELEIRO', 20, 23);

    // Status do sistema
    const running = status?.running || false;
    ctx.fillStyle = running ? COLORS.ok : COLORS.alarm;
    ctx.fillText(running ? '● RUNNING' : '● STOPPED', CANVAS_WIDTH - 200, 23);

    // Tempo de simulação
    ctx.fillStyle = COLORS.text;
    ctx.font = '12px monospace';
    const timeS = status?.time_s || 0;
    const hours = Math.floor(timeS / 3600);
    const mins = Math.floor((timeS % 3600) / 60);
    const secs = Math.floor(timeS % 60);
    ctx.fillText(
      `⏱ ${hours.toString().padStart(2, '0')}:${mins
        .toString()
        .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`,
      CANVAS_WIDTH - 400,
      23
    );

    // DEM particles count
    if (status?.dem_physics?.enabled) {
      ctx.fillStyle = COLORS.materialFlow;
      ctx.fillText(
        `🔬 DEM: ${status.dem_physics.particle_count} particles`,
        CANVAS_WIDTH - 650,
        23
      );
    }

    // Info lateral direita
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(CANVAS_WIDTH - 180, 50, 170, 700);

    ctx.fillStyle = COLORS.text;
    ctx.font = 'bold 14px monospace';
    ctx.fillText('DADOS OPERACIONAIS', CANVAS_WIDTH - 175, 75);

    ctx.font = '11px monospace';
    let yPos = 100;
    const lineHeight = 20;

    // KPIs
    const kpis = [
      { label: 'Throughput:', value: `${((status?.shiploader?.flow_tph || 0)).toFixed(0)} t/h` },
      { label: 'Target:', value: '1500 t/h' },
      { label: 'Warehouse:', value: `${(status?.warehouse_inventory_t || 0).toFixed(0)} t` },
      { label: 'Ship Load:', value: '30%' },
      { label: '', value: '' },
      { label: 'Clima:', value: 'Clear ☀️' },
      { label: 'Produto:', value: 'Soja' },
      { label: '', value: '' },
      { label: 'Alarmes:', value: (Array.isArray(status?.alarms) ? status.alarms.filter((a: any) => a.active)?.length : 0).toString() },
      { label: 'Interlocks:', value: (status?.interlocks?.active_count || 0).toString() },
    ];

    kpis.forEach((kpi) => {
      if (kpi.label) {
        ctx.fillStyle = COLORS.textDim;
        ctx.fillText(kpi.label, CANVAS_WIDTH - 170, yPos);
        ctx.fillStyle = COLORS.text;
        ctx.fillText(kpi.value, CANVAS_WIDTH - 70, yPos);
      }
      yPos += lineHeight;
    });
  };

  // Loop de animação
  useEffect(() => {
    initParticles();

    const animate = () => {
      drawSynoptic();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [status, shipLoadPct, totalMassLoaded]);

  // Fetch real-time data periodically
  useEffect(() => {
    fetchRealTimeData(); // Initial fetch
    
    const interval = setInterval(fetchRealTimeData, 5000); // Update every 5 seconds
    
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ width: '100%', height: '100%', bgcolor: '#0f172a', p: 2 }}>
      <Paper
        elevation={3}
        sx={{
          bgcolor: COLORS.background,
          p: 2,
          borderRadius: 2,
          border: '2px solid #334155',
        }}
      >
        {/* Header com controles */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }} alignItems="center">
          <Typography variant="h5" sx={{ color: COLORS.text, fontFamily: 'monospace', flexGrow: 1 }}>
            🖥️ SCADA - Terminal Synoptic View
          </Typography>

          <Chip
            icon={<Speed />}
            label={`${(status?.shiploader?.flow_tph || 0).toFixed(0)} t/h`}
            color={status?.running ? 'success' : 'default'}
            sx={{ fontFamily: 'monospace' }}
          />

          <Chip
            icon={<Thermostat />}
            label="Normal"
            color="info"
            sx={{ fontFamily: 'monospace' }}
          />

          <IconButton
            color={status?.running ? 'error' : 'success'}
            onClick={() => onCommand?.(status?.running ? 'stop' : 'start')}
          >
            {status?.running ? <Stop /> : <PlayArrow />}
          </IconButton>
        </Stack>

        {/* Canvas SCADA */}
        <Box
          sx={{
            position: 'relative',
            width: '100%',
            height: '800px',
            overflow: 'auto',
            bgcolor: COLORS.background,
            borderRadius: 1,
            border: '1px solid #475569',
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
        </Box>

        {/* Legenda */}
        <Stack direction="row" spacing={3} sx={{ mt: 2 }} justifyContent="center">
          <Chip label="● Running" sx={{ bgcolor: COLORS.ok, color: 'white' }} size="small" />
          <Chip label="● Stopped" sx={{ bgcolor: COLORS.textDim, color: 'white' }} size="small" />
          <Chip label="● Material Flow" sx={{ bgcolor: COLORS.materialFlow, color: 'white' }} size="small" />
          <Chip label="● Alarm" sx={{ bgcolor: COLORS.alarm, color: 'white' }} size="small" />
        </Stack>
      </Paper>
    </Box>
  );
};

export default ScadaSynoptic;
