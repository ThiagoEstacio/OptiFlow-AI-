/**
 * Realistic Tags for Port Grain Terminal
 *
 * Simulates a complete grain export terminal with:
 * - Truck reception and unloading
 * - Conveyor and elevator systems
 * - Storage silos
 * - Ship loading (shiploader)
 * - Quality control
 * - Utilities and support systems
 */

export interface Tag {
  id: string;
  name: string;
  description: string;
  unit: string;
  category: string;
  min_value: number;
  max_value: number;
  data_type: string;
  normal_range?: { min: number; max: number };
  alarm_high?: number;
  alarm_low?: number;
  correlations?: string[]; // IDs of correlated tags
}

export const PORT_GRAIN_TERMINAL_TAGS: Tag[] = [
  // ===== TRUCK RECEPTION AREA (Área de Recebimento) =====
  {
    id: 'RCV_SCALE_01_WEIGHT',
    name: 'Balança 1 - Peso',
    description: 'Peso do caminhão na balança 1',
    unit: 'kg',
    category: 'Recepção',
    min_value: 0,
    max_value: 60000,
    data_type: 'float',
    normal_range: { min: 25000, max: 45000 },
    correlations: ['RCV_SCALE_01_STATUS', 'RCV_QUEUE_COUNT']
  },
  {
    id: 'RCV_SCALE_01_STATUS',
    name: 'Balança 1 - Status',
    description: 'Status da balança 1 (0=Vazia, 1=Pesando, 2=Completo)',
    unit: 'estado',
    category: 'Recepção',
    min_value: 0,
    max_value: 2,
    data_type: 'integer',
    correlations: ['RCV_SCALE_01_WEIGHT']
  },
  {
    id: 'RCV_SCALE_02_WEIGHT',
    name: 'Balança 2 - Peso',
    description: 'Peso do caminhão na balança 2',
    unit: 'kg',
    category: 'Recepção',
    min_value: 0,
    max_value: 60000,
    data_type: 'float',
    normal_range: { min: 25000, max: 45000 },
    correlations: ['RCV_SCALE_02_STATUS', 'RCV_QUEUE_COUNT']
  },
  {
    id: 'RCV_SCALE_02_STATUS',
    name: 'Balança 2 - Status',
    description: 'Status da balança 2',
    unit: 'estado',
    category: 'Recepção',
    min_value: 0,
    max_value: 2,
    data_type: 'integer'
  },
  {
    id: 'RCV_QUEUE_COUNT',
    name: 'Fila de Caminhões',
    description: 'Número de caminhões na fila',
    unit: 'caminhões',
    category: 'Recepção',
    min_value: 0,
    max_value: 50,
    data_type: 'integer',
    alarm_high: 30,
    correlations: ['RCV_SCALE_01_WEIGHT', 'RCV_SCALE_02_WEIGHT']
  },
  {
    id: 'RCV_HOPPER_01_LEVEL',
    name: 'Moega 1 - Nível',
    description: 'Nível da moega de recepção 1',
    unit: '%',
    category: 'Recepção',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 20, max: 80 },
    alarm_high: 90,
    alarm_low: 5,
    correlations: ['RCV_HOPPER_01_GATE', 'CONV_01_SPEED']
  },
  {
    id: 'RCV_HOPPER_01_GATE',
    name: 'Moega 1 - Abertura da Comporta',
    description: 'Abertura da comporta da moega 1',
    unit: '%',
    category: 'Recepção',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    correlations: ['RCV_HOPPER_01_LEVEL']
  },
  {
    id: 'RCV_HOPPER_02_LEVEL',
    name: 'Moega 2 - Nível',
    description: 'Nível da moega de recepção 2',
    unit: '%',
    category: 'Recepção',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 20, max: 80 },
    alarm_high: 90,
    alarm_low: 5,
    correlations: ['RCV_HOPPER_02_GATE', 'CONV_02_SPEED']
  },
  {
    id: 'RCV_HOPPER_02_GATE',
    name: 'RCV_HOPPER_02_GATE',
    description: 'Reception Hopper 2 - Gate Opening',
    unit: '%',
    category: 'Reception',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    correlations: ['RCV_HOPPER_02_LEVEL']
  },

  // ===== CONVEYOR SYSTEM (Sistema de Correias) =====
  {
    id: 'CONV_01_SPEED',
    name: 'CONV_01_SPEED',
    description: 'Conveyor Belt 1 - Speed',
    unit: 'm/s',
    category: 'Conveyor',
    min_value: 0,
    max_value: 3.5,
    data_type: 'float',
    normal_range: { min: 2.0, max: 3.2 },
    alarm_low: 1.5,
    correlations: ['CONV_01_MOTOR_CURRENT', 'CONV_01_FLOW_RATE']
  },
  {
    id: 'CONV_01_MOTOR_CURRENT',
    name: 'CONV_01_MOTOR_CURRENT',
    description: 'Conveyor Belt 1 - Motor Current',
    unit: 'A',
    category: 'Conveyor',
    min_value: 0,
    max_value: 350,
    data_type: 'float',
    normal_range: { min: 150, max: 280 },
    alarm_high: 320,
    correlations: ['CONV_01_SPEED', 'CONV_01_FLOW_RATE', 'CONV_01_MOTOR_TEMP']
  },
  {
    id: 'CONV_01_MOTOR_TEMP',
    name: 'CONV_01_MOTOR_TEMP',
    description: 'Conveyor Belt 1 - Motor Temperature',
    unit: '°C',
    category: 'Conveyor',
    min_value: 20,
    max_value: 120,
    data_type: 'float',
    normal_range: { min: 40, max: 70 },
    alarm_high: 85,
    correlations: ['CONV_01_MOTOR_CURRENT']
  },
  {
    id: 'CONV_01_FLOW_RATE',
    name: 'CONV_01_FLOW_RATE',
    description: 'Conveyor Belt 1 - Flow Rate',
    unit: 't/h',
    category: 'Conveyor',
    min_value: 0,
    max_value: 800,
    data_type: 'float',
    normal_range: { min: 400, max: 700 },
    correlations: ['CONV_01_SPEED', 'CONV_01_MOTOR_CURRENT']
  },
  {
    id: 'CONV_02_SPEED',
    name: 'CONV_02_SPEED',
    description: 'Conveyor Belt 2 - Speed',
    unit: 'm/s',
    category: 'Conveyor',
    min_value: 0,
    max_value: 3.5,
    data_type: 'float',
    normal_range: { min: 2.0, max: 3.2 },
    alarm_low: 1.5,
    correlations: ['CONV_02_MOTOR_CURRENT', 'CONV_02_FLOW_RATE']
  },
  {
    id: 'CONV_02_MOTOR_CURRENT',
    name: 'CONV_02_MOTOR_CURRENT',
    description: 'Conveyor Belt 2 - Motor Current',
    unit: 'A',
    category: 'Conveyor',
    min_value: 0,
    max_value: 350,
    data_type: 'float',
    normal_range: { min: 150, max: 280 },
    alarm_high: 320,
    correlations: ['CONV_02_SPEED', 'CONV_02_FLOW_RATE']
  },
  {
    id: 'CONV_02_FLOW_RATE',
    name: 'CONV_02_FLOW_RATE',
    description: 'Conveyor Belt 2 - Flow Rate',
    unit: 't/h',
    category: 'Conveyor',
    min_value: 0,
    max_value: 800,
    data_type: 'float',
    normal_range: { min: 400, max: 700 },
    correlations: ['CONV_02_SPEED']
  },
  {
    id: 'CONV_03_SPEED',
    name: 'CONV_03_SPEED',
    description: 'Conveyor Belt 3 (Main Transfer) - Speed',
    unit: 'm/s',
    category: 'Conveyor',
    min_value: 0,
    max_value: 4.0,
    data_type: 'float',
    normal_range: { min: 2.5, max: 3.8 },
    correlations: ['CONV_03_MOTOR_CURRENT', 'CONV_03_FLOW_RATE']
  },
  {
    id: 'CONV_03_MOTOR_CURRENT',
    name: 'CONV_03_MOTOR_CURRENT',
    description: 'Conveyor Belt 3 - Motor Current',
    unit: 'A',
    category: 'Conveyor',
    min_value: 0,
    max_value: 450,
    data_type: 'float',
    normal_range: { min: 200, max: 380 },
    alarm_high: 420,
    correlations: ['CONV_03_SPEED']
  },
  {
    id: 'CONV_03_FLOW_RATE',
    name: 'CONV_03_FLOW_RATE',
    description: 'Conveyor Belt 3 - Flow Rate',
    unit: 't/h',
    category: 'Conveyor',
    min_value: 0,
    max_value: 1500,
    data_type: 'float',
    normal_range: { min: 800, max: 1300 },
    correlations: ['CONV_03_SPEED']
  },

  // ===== BUCKET ELEVATORS (Elevadores de Canecas) =====
  {
    id: 'ELEV_01_SPEED',
    name: 'ELEV_01_SPEED',
    description: 'Bucket Elevator 1 - Speed',
    unit: 'm/s',
    category: 'Elevator',
    min_value: 0,
    max_value: 2.5,
    data_type: 'float',
    normal_range: { min: 1.8, max: 2.3 },
    correlations: ['ELEV_01_MOTOR_CURRENT', 'ELEV_01_VIBRATION']
  },
  {
    id: 'ELEV_01_MOTOR_CURRENT',
    name: 'ELEV_01_MOTOR_CURRENT',
    description: 'Bucket Elevator 1 - Motor Current',
    unit: 'A',
    category: 'Elevator',
    min_value: 0,
    max_value: 500,
    data_type: 'float',
    normal_range: { min: 250, max: 420 },
    alarm_high: 470,
    correlations: ['ELEV_01_SPEED', 'ELEV_01_MOTOR_TEMP']
  },
  {
    id: 'ELEV_01_MOTOR_TEMP',
    name: 'ELEV_01_MOTOR_TEMP',
    description: 'Bucket Elevator 1 - Motor Temperature',
    unit: '°C',
    category: 'Elevator',
    min_value: 20,
    max_value: 130,
    data_type: 'float',
    normal_range: { min: 45, max: 75 },
    alarm_high: 90,
    correlations: ['ELEV_01_MOTOR_CURRENT']
  },
  {
    id: 'ELEV_01_VIBRATION',
    name: 'ELEV_01_VIBRATION',
    description: 'Bucket Elevator 1 - Vibration',
    unit: 'mm/s',
    category: 'Elevator',
    min_value: 0,
    max_value: 25,
    data_type: 'float',
    normal_range: { min: 0, max: 8 },
    alarm_high: 15,
    correlations: ['ELEV_01_SPEED']
  },
  {
    id: 'ELEV_02_SPEED',
    name: 'ELEV_02_SPEED',
    description: 'Bucket Elevator 2 - Speed',
    unit: 'm/s',
    category: 'Elevator',
    min_value: 0,
    max_value: 2.5,
    data_type: 'float',
    normal_range: { min: 1.8, max: 2.3 },
    correlations: ['ELEV_02_MOTOR_CURRENT']
  },
  {
    id: 'ELEV_02_MOTOR_CURRENT',
    name: 'ELEV_02_MOTOR_CURRENT',
    description: 'Bucket Elevator 2 - Motor Current',
    unit: 'A',
    category: 'Elevator',
    min_value: 0,
    max_value: 500,
    data_type: 'float',
    normal_range: { min: 250, max: 420 },
    alarm_high: 470,
    correlations: ['ELEV_02_SPEED']
  },

  // ===== STORAGE SILOS (Silos de Armazenagem) =====
  {
    id: 'SILO_01_LEVEL',
    name: 'SILO_01_LEVEL',
    description: 'Silo 1 - Level',
    unit: '%',
    category: 'Storage',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 30, max: 95 },
    alarm_high: 98,
    alarm_low: 10,
    correlations: ['SILO_01_WEIGHT', 'SILO_01_TEMP_AVG']
  },
  {
    id: 'SILO_01_WEIGHT',
    name: 'SILO_01_WEIGHT',
    description: 'Silo 1 - Total Weight',
    unit: 't',
    category: 'Storage',
    min_value: 0,
    max_value: 15000,
    data_type: 'float',
    correlations: ['SILO_01_LEVEL']
  },
  {
    id: 'SILO_01_TEMP_AVG',
    name: 'SILO_01_TEMP_AVG',
    description: 'Silo 1 - Average Temperature',
    unit: '°C',
    category: 'Storage',
    min_value: -10,
    max_value: 60,
    data_type: 'float',
    normal_range: { min: 15, max: 30 },
    alarm_high: 40,
    correlations: ['SILO_01_LEVEL', 'SILO_01_HUMIDITY']
  },
  {
    id: 'SILO_01_TEMP_TOP',
    name: 'SILO_01_TEMP_TOP',
    description: 'Silo 1 - Temperature Top',
    unit: '°C',
    category: 'Storage',
    min_value: -10,
    max_value: 60,
    data_type: 'float',
    alarm_high: 45,
    correlations: ['SILO_01_TEMP_AVG']
  },
  {
    id: 'SILO_01_TEMP_BOTTOM',
    name: 'SILO_01_TEMP_BOTTOM',
    description: 'Silo 1 - Temperature Bottom',
    unit: '°C',
    category: 'Storage',
    min_value: -10,
    max_value: 60,
    data_type: 'float',
    alarm_high: 45,
    correlations: ['SILO_01_TEMP_AVG']
  },
  {
    id: 'SILO_01_HUMIDITY',
    name: 'SILO_01_HUMIDITY',
    description: 'Silo 1 - Humidity',
    unit: '%',
    category: 'Storage',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 10, max: 14 },
    alarm_high: 16,
    correlations: ['SILO_01_TEMP_AVG']
  },
  {
    id: 'SILO_01_AERATION_FAN',
    name: 'SILO_01_AERATION_FAN',
    description: 'Silo 1 - Aeration Fan Status',
    unit: 'state',
    category: 'Storage',
    min_value: 0,
    max_value: 1,
    data_type: 'integer',
    correlations: ['SILO_01_TEMP_AVG', 'SILO_01_HUMIDITY']
  },
  {
    id: 'SILO_02_LEVEL',
    name: 'SILO_02_LEVEL',
    description: 'Silo 2 - Level',
    unit: '%',
    category: 'Storage',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 30, max: 95 },
    alarm_high: 98,
    alarm_low: 10,
    correlations: ['SILO_02_WEIGHT']
  },
  {
    id: 'SILO_02_WEIGHT',
    name: 'SILO_02_WEIGHT',
    description: 'Silo 2 - Total Weight',
    unit: 't',
    category: 'Storage',
    min_value: 0,
    max_value: 15000,
    data_type: 'float',
    correlations: ['SILO_02_LEVEL']
  },
  {
    id: 'SILO_02_TEMP_AVG',
    name: 'SILO_02_TEMP_AVG',
    description: 'Silo 2 - Average Temperature',
    unit: '°C',
    category: 'Storage',
    min_value: -10,
    max_value: 60,
    data_type: 'float',
    normal_range: { min: 15, max: 30 },
    alarm_high: 40,
    correlations: ['SILO_02_HUMIDITY']
  },
  {
    id: 'SILO_02_HUMIDITY',
    name: 'SILO_02_HUMIDITY',
    description: 'Silo 2 - Humidity',
    unit: '%',
    category: 'Storage',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 10, max: 14 },
    alarm_high: 16,
    correlations: ['SILO_02_TEMP_AVG']
  },
  {
    id: 'SILO_03_LEVEL',
    name: 'SILO_03_LEVEL',
    description: 'Silo 3 - Level',
    unit: '%',
    category: 'Storage',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 30, max: 95 },
    alarm_high: 98,
    alarm_low: 10,
    correlations: ['SILO_03_WEIGHT']
  },
  {
    id: 'SILO_03_WEIGHT',
    name: 'SILO_03_WEIGHT',
    description: 'Silo 3 - Total Weight',
    unit: 't',
    category: 'Storage',
    min_value: 0,
    max_value: 20000,
    data_type: 'float',
    correlations: ['SILO_03_LEVEL']
  },
  {
    id: 'SILO_03_TEMP_AVG',
    name: 'SILO_03_TEMP_AVG',
    description: 'Silo 3 - Average Temperature',
    unit: '°C',
    category: 'Storage',
    min_value: -10,
    max_value: 60,
    data_type: 'float',
    normal_range: { min: 15, max: 30 },
    alarm_high: 40
  },

  // ===== SHIPLOADER SYSTEM (Sistema de Carregamento de Navios) =====
  {
    id: 'SHIP_LOADER_BOOM_ANGLE',
    name: 'SHIP_LOADER_BOOM_ANGLE',
    description: 'Shiploader - Boom Angle',
    unit: '°',
    category: 'Shiploader',
    min_value: -20,
    max_value: 45,
    data_type: 'float',
    normal_range: { min: 0, max: 35 },
    correlations: ['SHIP_LOADER_FLOW_RATE']
  },
  {
    id: 'SHIP_LOADER_SLEW_ANGLE',
    name: 'SHIP_LOADER_SLEW_ANGLE',
    description: 'Shiploader - Slew Angle',
    unit: '°',
    category: 'Shiploader',
    min_value: -180,
    max_value: 180,
    data_type: 'float',
    correlations: ['SHIP_LOADER_BOOM_ANGLE']
  },
  {
    id: 'SHIP_LOADER_FLOW_RATE',
    name: 'SHIP_LOADER_FLOW_RATE',
    description: 'Shiploader - Flow Rate',
    unit: 't/h',
    category: 'Shiploader',
    min_value: 0,
    max_value: 3000,
    data_type: 'float',
    normal_range: { min: 1500, max: 2800 },
    correlations: ['SHIP_LOADER_MOTOR_CURRENT', 'SHIP_TOTAL_LOADED']
  },
  {
    id: 'SHIP_LOADER_MOTOR_CURRENT',
    name: 'SHIP_LOADER_MOTOR_CURRENT',
    description: 'Shiploader - Motor Current',
    unit: 'A',
    category: 'Shiploader',
    min_value: 0,
    max_value: 600,
    data_type: 'float',
    normal_range: { min: 200, max: 500 },
    alarm_high: 570,
    correlations: ['SHIP_LOADER_FLOW_RATE']
  },
  {
    id: 'SHIP_LOADER_VIBRATION',
    name: 'SHIP_LOADER_VIBRATION',
    description: 'Shiploader - Vibration',
    unit: 'mm/s',
    category: 'Shiploader',
    min_value: 0,
    max_value: 20,
    data_type: 'float',
    normal_range: { min: 0, max: 6 },
    alarm_high: 12,
    correlations: ['SHIP_LOADER_FLOW_RATE']
  },
  {
    id: 'SHIP_TOTAL_LOADED',
    name: 'SHIP_TOTAL_LOADED',
    description: 'Ship - Total Loaded',
    unit: 't',
    category: 'Shiploader',
    min_value: 0,
    max_value: 100000,
    data_type: 'float',
    correlations: ['SHIP_LOADER_FLOW_RATE', 'SHIP_LOADING_PROGRESS']
  },
  {
    id: 'SHIP_LOADING_PROGRESS',
    name: 'SHIP_LOADING_PROGRESS',
    description: 'Ship - Loading Progress',
    unit: '%',
    category: 'Shiploader',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    correlations: ['SHIP_TOTAL_LOADED']
  },
  {
    id: 'SHIP_DRAFT_FORE',
    name: 'SHIP_DRAFT_FORE',
    description: 'Ship - Draft Forward',
    unit: 'm',
    category: 'Shiploader',
    min_value: 0,
    max_value: 20,
    data_type: 'float',
    correlations: ['SHIP_TOTAL_LOADED', 'SHIP_DRAFT_AFT']
  },
  {
    id: 'SHIP_DRAFT_AFT',
    name: 'SHIP_DRAFT_AFT',
    description: 'Ship - Draft Aft',
    unit: 'm',
    category: 'Shiploader',
    min_value: 0,
    max_value: 20,
    data_type: 'float',
    correlations: ['SHIP_TOTAL_LOADED', 'SHIP_DRAFT_FORE']
  },
  {
    id: 'SHIP_DUST_SUPPRESSION',
    name: 'SHIP_DUST_SUPPRESSION',
    description: 'Shiploader - Dust Suppression Water Flow',
    unit: 'L/min',
    category: 'Shiploader',
    min_value: 0,
    max_value: 500,
    data_type: 'float',
    normal_range: { min: 100, max: 300 },
    correlations: ['SHIP_LOADER_FLOW_RATE']
  },

  // ===== QUALITY CONTROL (Controle de Qualidade) =====
  {
    id: 'QC_MOISTURE_CONTENT',
    name: 'QC_MOISTURE_CONTENT',
    description: 'Quality Control - Moisture Content',
    unit: '%',
    category: 'Quality',
    min_value: 0,
    max_value: 25,
    data_type: 'float',
    normal_range: { min: 12, max: 14 },
    alarm_high: 15,
    correlations: ['SILO_01_HUMIDITY', 'SILO_02_HUMIDITY']
  },
  {
    id: 'QC_IMPURITIES',
    name: 'QC_IMPURITIES',
    description: 'Quality Control - Impurities',
    unit: '%',
    category: 'Quality',
    min_value: 0,
    max_value: 10,
    data_type: 'float',
    normal_range: { min: 0, max: 2 },
    alarm_high: 3
  },
  {
    id: 'QC_BROKEN_GRAINS',
    name: 'QC_BROKEN_GRAINS',
    description: 'Quality Control - Broken Grains',
    unit: '%',
    category: 'Quality',
    min_value: 0,
    max_value: 15,
    data_type: 'float',
    normal_range: { min: 0, max: 4 },
    alarm_high: 6
  },
  {
    id: 'QC_PROTEIN_CONTENT',
    name: 'QC_PROTEIN_CONTENT',
    description: 'Quality Control - Protein Content',
    unit: '%',
    category: 'Quality',
    min_value: 0,
    max_value: 20,
    data_type: 'float',
    normal_range: { min: 11, max: 13 }
  },
  {
    id: 'QC_TEST_WEIGHT',
    name: 'QC_TEST_WEIGHT',
    description: 'Quality Control - Test Weight',
    unit: 'kg/hL',
    category: 'Quality',
    min_value: 60,
    max_value: 85,
    data_type: 'float',
    normal_range: { min: 75, max: 82 }
  },

  // ===== UTILITIES (Utilidades) =====
  {
    id: 'UTIL_POWER_CONSUMPTION',
    name: 'UTIL_POWER_CONSUMPTION',
    description: 'Total Power Consumption',
    unit: 'kW',
    category: 'Utilities',
    min_value: 0,
    max_value: 5000,
    data_type: 'float',
    normal_range: { min: 1500, max: 3500 },
    correlations: ['CONV_01_MOTOR_CURRENT', 'CONV_02_MOTOR_CURRENT', 'ELEV_01_MOTOR_CURRENT']
  },
  {
    id: 'UTIL_COMPRESSOR_01_PRESSURE',
    name: 'UTIL_COMPRESSOR_01_PRESSURE',
    description: 'Compressor 1 - Air Pressure',
    unit: 'bar',
    category: 'Utilities',
    min_value: 0,
    max_value: 10,
    data_type: 'float',
    normal_range: { min: 6, max: 8 },
    alarm_low: 5,
    alarm_high: 9
  },
  {
    id: 'UTIL_COMPRESSOR_01_TEMP',
    name: 'UTIL_COMPRESSOR_01_TEMP',
    description: 'Compressor 1 - Temperature',
    unit: '°C',
    category: 'Utilities',
    min_value: 0,
    max_value: 150,
    data_type: 'float',
    normal_range: { min: 60, max: 90 },
    alarm_high: 110
  },
  {
    id: 'UTIL_DUST_COLLECTOR_01_PRESSURE',
    name: 'UTIL_DUST_COLLECTOR_01_PRESSURE',
    description: 'Dust Collector 1 - Differential Pressure',
    unit: 'mmH2O',
    category: 'Utilities',
    min_value: 0,
    max_value: 250,
    data_type: 'float',
    normal_range: { min: 50, max: 150 },
    alarm_high: 200
  },
  {
    id: 'UTIL_DUST_COLLECTOR_02_PRESSURE',
    name: 'UTIL_DUST_COLLECTOR_02_PRESSURE',
    description: 'Dust Collector 2 - Differential Pressure',
    unit: 'mmH2O',
    category: 'Utilities',
    min_value: 0,
    max_value: 250,
    data_type: 'float',
    normal_range: { min: 50, max: 150 },
    alarm_high: 200
  },

  // ===== ENVIRONMENTAL (Ambiental) =====
  {
    id: 'ENV_OUTDOOR_TEMP',
    name: 'ENV_OUTDOOR_TEMP',
    description: 'Outdoor Temperature',
    unit: '°C',
    category: 'Environmental',
    min_value: -20,
    max_value: 50,
    data_type: 'float',
    correlations: ['SILO_01_TEMP_AVG', 'SILO_02_TEMP_AVG']
  },
  {
    id: 'ENV_OUTDOOR_HUMIDITY',
    name: 'ENV_OUTDOOR_HUMIDITY',
    description: 'Outdoor Humidity',
    unit: '%',
    category: 'Environmental',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    correlations: ['SILO_01_HUMIDITY', 'SILO_02_HUMIDITY']
  },
  {
    id: 'ENV_WIND_SPEED',
    name: 'ENV_WIND_SPEED',
    description: 'Wind Speed',
    unit: 'km/h',
    category: 'Environmental',
    min_value: 0,
    max_value: 150,
    data_type: 'float',
    alarm_high: 50,
    correlations: ['SHIP_LOADER_BOOM_ANGLE']
  },
  {
    id: 'ENV_WIND_DIRECTION',
    name: 'ENV_WIND_DIRECTION',
    description: 'Wind Direction',
    unit: '°',
    category: 'Environmental',
    min_value: 0,
    max_value: 360,
    data_type: 'float'
  },
  {
    id: 'ENV_RAINFALL',
    name: 'ENV_RAINFALL',
    description: 'Rainfall Intensity',
    unit: 'mm/h',
    category: 'Environmental',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    alarm_high: 20,
    correlations: ['SHIP_LOADER_FLOW_RATE']
  },

  // ===== PRODUCTION METRICS (Métricas de Produção) =====
  {
    id: 'PROD_TOTAL_RECEIVED_TODAY',
    name: 'PROD_TOTAL_RECEIVED_TODAY',
    description: 'Total Received Today',
    unit: 't',
    category: 'Production',
    min_value: 0,
    max_value: 50000,
    data_type: 'float',
    correlations: ['RCV_SCALE_01_WEIGHT', 'RCV_SCALE_02_WEIGHT']
  },
  {
    id: 'PROD_TOTAL_SHIPPED_TODAY',
    name: 'PROD_TOTAL_SHIPPED_TODAY',
    description: 'Total Shipped Today',
    unit: 't',
    category: 'Production',
    min_value: 0,
    max_value: 50000,
    data_type: 'float',
    correlations: ['SHIP_TOTAL_LOADED']
  },
  {
    id: 'PROD_INVENTORY_TOTAL',
    name: 'PROD_INVENTORY_TOTAL',
    description: 'Total Inventory',
    unit: 't',
    category: 'Production',
    min_value: 0,
    max_value: 50000,
    data_type: 'float',
    correlations: ['SILO_01_WEIGHT', 'SILO_02_WEIGHT', 'SILO_03_WEIGHT']
  },
  {
    id: 'PROD_EFFICIENCY',
    name: 'PROD_EFFICIENCY',
    description: 'Overall Equipment Efficiency (OEE)',
    unit: '%',
    category: 'Production',
    min_value: 0,
    max_value: 100,
    data_type: 'float',
    normal_range: { min: 75, max: 95 },
    alarm_low: 70
  }
];

// Helper function to get tags by category
export function getTagsByCategory(category: string): Tag[] {
  return PORT_GRAIN_TERMINAL_TAGS.filter(tag => tag.category === category);
}

// Helper function to get all categories
export function getAllCategories(): string[] {
  return Array.from(new Set(PORT_GRAIN_TERMINAL_TAGS.map(tag => tag.category)));
}

// Helper function to find tag by ID
export function getTagById(id: string): Tag | undefined {
  return PORT_GRAIN_TERMINAL_TAGS.find(tag => tag.id === id);
}

export default PORT_GRAIN_TERMINAL_TAGS;
