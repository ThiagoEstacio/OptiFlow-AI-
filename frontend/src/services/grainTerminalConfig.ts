/**
 * Grain Terminal Configuration
 * Digital contract for the 1500 t/h export line simulator
 * Based on professional terminal specification
 */

export interface GrainTerminalConfig {
  project: {
    name: string;
    version: string;
    doc: string;
  };

  units: {
    length: string;
    volume: string;
    mass: string;
    flow: string;
    time: string;
    speed: string;
    power: string;
    energy: string;
    temp: string;
    percent: string;
  };

  assumptions: {
    shiploader_master_tph: number;
    practical_margin: number;
    belt_fill_factor: number;
    doc: string;
  };

  product: {
    name: string;
    bulk_density_t_m3: number;
    moisture_pct_range: [number, number];
    mu_internal: number;
    mu_belt_external: number;
    effects: {
      rho_by_moisture: string;
      capacity_penalty_by_moisture: string;
    };
    doc: string;
  };

  plant: {
    warehouse: {
      geometry: {
        length_m: number;
        width_m: number;
        height_m: number;
        volume_m3: number;
      };
      initial_inventory_t: number;
      doc: string;

      reclaim_belt: {
        id: string;
        width_m: number;
        speed_mps_nom: number;
        practical_capacity_tph: number;
        motor_kW: number;
        doc: string;
      };

      gates: {
        count: number;
        spacing_m: number;
        q_per_gate_tph_100pct: number;
        alpha_saturation: number;
        flow_curve: Array<{
          open_pct: number;
          h_norm_min: number;
          q_tph: number;
        }>;
        doc: string;
      };
    };

    route: {
      segments: Array<{
        id: string;
        name: string;
        width_m?: number;
        speed_mps?: number;
        slope_deg?: number;
        height_m?: number;
        belt_speed_mps?: number;
        buckets_per_m?: number;
        bucket_vol_L?: number;
        batch_target_kg?: number;
        tol_pct?: number;
        fill_s?: number;
        discharge_s?: number;
        avg_capacity_tph?: number;
        master_capacity_tph?: number;
        practical_capacity_tph: number;
        motor_kW: number;
        doc: string;
      }>;
      doc: string;
    };
  };

  mechanics: {
    belts: {
      mass_kg_per_m: { [key: string]: number };
      idler_per_m: number;
      drive_pulley_diameter_mm: number;
      chute_losses_pct: number;
      plugging: {
        alarm_pct: number;
        trip_pct: number;
        trip_hold_s: number;
      };
    };
    underspeed: {
      encoder_ppr: number;
      filter_ms: number;
      warn_pct_nominal: number;
      alarm_pct_nominal: number;
      trip_pct_motor_on: number;
      sensitivity_beta: number;
    };
    coefficients: {
      k_load: number;
      k_fric: number;
      k_wear: number;
    };
    doc: string;
  };

  electrical: {
    limits: {
      overcurrent_warn_factor: number;
      overcurrent_trip_factor: number;
      pf_min: number;
    };
    tariffs: {
      peak_R$_kWh: number;
      offpeak_R$_kWh: number;
    };
    doc: string;
  };

  thermal_limits: {
    [key: string]: {
      warn_C: number;
      alarm_C: number;
      trip_C: number;
    };
  };

  control: {
    setpoints_tph: { [key: string]: number };
    levels_pct: {
      target_low: number;
      target_high: number;
      high: number;
      highhigh: number;
    };
    gates_pi: {
      type: string;
      Kp: number;
      Ki: number;
      A_tot_limits: [number, number];
      gate_open_limits_pct: [number, number];
      start_strategy: {
        initial_gates: number;
        initial_open_pct: number;
      };
      ramp_pct_per_s: number;
      distribution: string;
      doc: string;
    };
    doc: string;
  };

  alarms_and_trips: {
    definitions: Array<{
      tag: string;
      severity: string;
      latch: boolean;
      delay_on_s?: number;
      action: string;
      doc: string;
    }>;
    doc: string;
  };

  interlocks: {
    matrix: Array<{
      cause: string;
      effect: string[];
      type: string;
      delay_s: number;
      reset: string;
      doc: string;
    }>;
    doc: string;
  };

  maintenance: {
    health_model: {
      equation: string;
      thresholds_pct: {
        warn: number;
        plan: number;
        trip: number;
      };
      k: {
        k_uso: number;
        k_choque: number;
      };
    };
    sensors: {
      vibration_mm_s: boolean;
      oil_temp_C: boolean;
      cycle_counter: boolean;
    };
    hours_counters: boolean;
    doc: string;
  };

  energy: {
    measurements_per_device: string[];
    kpis: string[];
    alarms: string[];
    doc: string;
  };

  simulation: {
    dt_s: number;
    T_final_s: number;
    outputs: string[];
    doc: string;
  };
}

export const GRAIN_TERMINAL_CONFIG: GrainTerminalConfig = {
  project: {
    name: "Simulador Terminal Exportador - Linha de Embarque 1500 t/h",
    version: "1.0.0",
    doc: "Contrato digital do processo. Este JSON é lido pelo simulador para construir a planta, variáveis OPC-UA, controles (PI de vazadores), intertravamentos e KPIs de energia/manutenção."
  },

  units: {
    length: "m",
    volume: "m3",
    mass: "t",
    flow: "t/h",
    time: "s",
    speed: "m/s",
    power: "kW",
    energy: "kWh",
    temp: "C",
    percent: "%"
  },

  assumptions: {
    shiploader_master_tph: 1500,
    practical_margin: 1.10,
    belt_fill_factor: 0.70,
    doc: "O shiploader define o setpoint mestre de vazão (1500 t/h). Todas as capacidades de trecho devem ser ≥ 1,1× do mestre (folga)."
  },

  product: {
    name: "Graos (soja/milho)",
    bulk_density_t_m3: 0.75,
    moisture_pct_range: [12, 14],
    mu_internal: 0.40,
    mu_belt_external: 0.03,
    effects: {
      rho_by_moisture: "rho = 0.75 + 0.01 * moisture_pct",
      capacity_penalty_by_moisture: "cap_real = cap_nom * (1 - 0.25 * moisture_pct_norm)"
    },
    doc: "Define propriedades do material que impactam vazão e esforço mecânico/energético. 'effects' são fórmulas aplicadas a cada passo da simulação."
  },

  plant: {
    warehouse: {
      geometry: { length_m: 120, width_m: 30, height_m: 20, volume_m3: 72000 },
      initial_inventory_t: 50000,
      doc: "Armazém fonte do material. O inventário diminui conforme a soma das vazões dos vazadores. Mantém balanço de massa global do sistema.",

      reclaim_belt: {
        id: "ARZ_CORR_REC",
        width_m: 1.6,
        speed_mps_nom: 3.5,
        practical_capacity_tph: 1650,
        motor_kW: 225,
        doc: "Correia recuperadora sob o armazém. Recebe o material dos vazadores e alimenta a rota. Capacidade ≥ 1650 t/h para garantir folga."
      },

      gates: {
        count: 10,
        spacing_m: 12,
        q_per_gate_tph_100pct: 170,
        alpha_saturation: 0.10,
        flow_curve: [
          { open_pct: 0, h_norm_min: 0.0, q_tph: 0 },
          { open_pct: 25, h_norm_min: 0.3, q_tph: 42 },
          { open_pct: 50, h_norm_min: 0.4, q_tph: 85 },
          { open_pct: 75, h_norm_min: 0.5, q_tph: 136 },
          { open_pct: 100, h_norm_min: 0.6, q_tph: 170 }
        ],
        doc: "10 vazadores modulam a alimentação do sistema. Vazão por vazador depende de %abertura e nível local (h_norm). Penalização de saturação multi-vazador (alpha) reduz a soma ideal quando muitos abrem simultaneamente."
      }
    },

    route: {
      segments: [
        {
          id: "CORR01",
          name: "Correia 1 (Armazem → Elevador)",
          width_m: 1.5,
          speed_mps: 3.2,
          slope_deg: 6,
          practical_capacity_tph: 1650,
          motor_kW: 180,
          doc: "Recebe fluxo dos vazadores. Converte carga de material em esforço (torque/corrente). Sujeita a subvelocidade por sobrecarga e a alarmes de desalinhamento/temperatura."
        },
        {
          id: "ELV01",
          name: "Elevador de Canecas",
          height_m: 30,
          belt_speed_mps: 2.1,
          buckets_per_m: 5,
          bucket_vol_L: 9,
          practical_capacity_tph: 1650,
          motor_kW: 225,
          doc: "Eleva o material. Aplica modelo de slip, correia frouxa e travamento. Capacidade calculada por (caçambas×volume×rho×velocidade). Intertravamento crítico para upstream."
        },
        {
          id: "CORR02",
          name: "Correia 2 (Elevador → Balança)",
          width_m: 1.4,
          speed_mps: 3.0,
          slope_deg: 0,
          practical_capacity_tph: 1650,
          motor_kW: 150,
          doc: "Transfere material do elevador para a balança. Considera perdas em chutes e alarmes de entupimento."
        },
        {
          id: "BAL01",
          name: "Balança de Batelada",
          batch_target_kg: 1000,
          tol_pct: 0.5,
          fill_s: 12,
          discharge_s: 5,
          avg_capacity_tph: 1500,
          practical_capacity_tph: 1500,
          motor_kW: 50,
          doc: "Opera ciclos de enchimento/descarga para entregar média de 1500 t/h. Ajusta tempo de ciclo dinamicamente para seguir o mestre. Gera eventos de ciclo e alarmes de falha/timeout."
        },
        {
          id: "CORR03",
          name: "Correia 3 (Balança → Shiploader)",
          width_m: 1.6,
          speed_mps: 3.2,
          slope_deg: 8,
          practical_capacity_tph: 1650,
          motor_kW: 180,
          doc: "Leva a produção da balança até o shiploader. É a referência de vazão medida para controle (pode ser usada como PV do mestre)."
        },
        {
          id: "SLD01",
          name: "Shiploader",
          master_capacity_tph: 1500,
          practical_capacity_tph: 1500,
          motor_kW: 320,
          doc: "Define o setpoint mestre de vazão do sistema (1500 t/h). O simulador usa seu valor como referência para feedforward e comparação com PV (vazão medida)."
        }
      ],
      doc: "Encadeamento dos equipamentos de processo. A ordem define o fluxo e a lógica de intertravamento cascata (falha downstream reduz/para upstream)."
    }
  },

  mechanics: {
    belts: {
      mass_kg_per_m: { width_1_6m: 35, width_1_4m: 29, width_1_5m: 32 },
      idler_per_m: 0.30,
      drive_pulley_diameter_mm: 630,
      chute_losses_pct: 3,
      plugging: { alarm_pct: 15, trip_pct: 25, trip_hold_s: 10 }
    },
    underspeed: {
      encoder_ppr: 1024,
      filter_ms: 200,
      warn_pct_nominal: 90,
      alarm_pct_nominal: 80,
      trip_pct_motor_on: 20,
      sensitivity_beta: 0.60
    },
    coefficients: { k_load: 0.45, k_fric: 0.05, k_wear: 0.01 },
    doc: "Parâmetros mecânicos convertidos em esforço/corrente e condições de alarme. Subvelocidade usa encoder+filtro; chutes acumulam material e podem entalar."
  },

  electrical: {
    limits: {
      overcurrent_warn_factor: 0.90,
      overcurrent_trip_factor: 1.15,
      pf_min: 0.92
    },
    tariffs: { peak_R$_kWh: 1.50, offpeak_R$_kWh: 0.65 },
    doc: "Regras elétricas globais. O simulador calcula P=V·I·FP por equipamento, acumula kWh e monitora PF. Alarmes/trips elétricos seguem estes limites."
  },

  thermal_limits: {
    bearing: { warn_C: 60, alarm_C: 70, trip_C: 80 },
    belt: { warn_C: 50, alarm_C: 60, trip_C: 65 },
    drum: { warn_C: 55, alarm_C: 65, trip_C: 75 },
    motor: { warn_C: 85, alarm_C: 95, trip_C: 105 },
    gearbox: { warn_C: 70, alarm_C: 80, trip_C: 90 },
    elevator_inside: { warn_C: 40, alarm_C: 50, trip_C: 55 }
  },

  control: {
    setpoints_tph: { CORR01: 1500, ELV01: 1500, CORR02: 1500, BAL01: 1500, CORR03: 1500 },
    levels_pct: { target_low: 40, target_high: 60, high: 80, highhigh: 95 },
    gates_pi: {
      type: "PI_antiwindup",
      Kp: 0.12,
      Ki: 0.02,
      A_tot_limits: [0, 1000],
      gate_open_limits_pct: [10, 90],
      start_strategy: { initial_gates: 4, initial_open_pct: 50 },
      ramp_pct_per_s: 5,
      distribution: "equal",
      doc: "Controlador mestre de alimentação. Integra erro (SP−PV) e modula a abertura total equivalente dos vazadores. Distribuição igualitária entre os N abertos, respeitando rampas e limites."
    },
    doc: "Bloco de controle central. SPs por trecho seguem o mestre (shiploader). Buffer de nível nas caixas regula ações (fechar 1 gate em High; fechar quase todos em High-High)."
  },

  alarms_and_trips: {
    definitions: [
      { tag: "AL_CORRxx_DESALINHAMENTO", severity: "A", latch: true, delay_on_s: 1.0, action: "reduzir_fluxo", doc: "Correia desalinhada. Mantém operação, mas reduz abertura dos vazadores para aliviar carga." },
      { tag: "AL_CORRxx_SUBVELOCIDADE", severity: "A", latch: true, delay_on_s: 0.5, action: "fechar_um_vazador", doc: "RPM abaixo do nominal. Fecha um vazador para recuperar velocidade." },
      { tag: "TRIP_CORRxx_RASGO", severity: "E", latch: true, action: "parar_correia", doc: "Rasgo de correia. Para imediatamente a correia e bloqueia start até reset manual." },
      { tag: "TRIP_SOBRETEMP", severity: "E", latch: true, action: "parada_imediata", doc: "Temperatura crítica em correia/tambor/mancal/motor." },
      { tag: "AL_CHTxx_ACUMULO", severity: "A", latch: false, action: "alerta", doc: "Acúmulo de material em chute. Sinal de atenção; pode anteceder entalo." },
      { tag: "TRIP_CHTxx_ENTALO", severity: "E", latch: true, action: "parada_upstream", doc: "Entupimento confirmado. Para upstream para evitar derrames." },
      { tag: "AL_FP_BAIXO", severity: "B", latch: false, action: "alerta_energia", doc: "Fator de potência abaixo do mínimo. Sugere correção reativa." },
      { tag: "TRIP_SOBRECARGA", severity: "E", latch: true, action: "parada_equipamento", doc: "Sobrecorrente persistente. Proteção do motor/inversor." },
      { tag: "AL_MAN_PREVENTIVA", severity: "B", latch: false, action: "agendar_mp", doc: "Limite de saúde atingido. Recomendar manutenção preventiva." },
      { tag: "AL_MAN_AGENDAR", severity: "A", latch: true, action: "programar_parada", doc: "Saúde baixa. Programar janela de manutenção." }
    ],
    doc: "Catálogo de AL/TRIP com severidade, ação recomendada e comportamento de retenção. O simulador publica como eventos OPC-UA."
  },

  interlocks: {
    matrix: [
      {
        cause: "TRIP_CORR03_RASGO",
        effect: ["CMD_CORR03_DESLIGAR", "CMD_BAL01_PARAR", "CMD_CORR02_PARAR", "CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
        type: "hard_trip",
        delay_s: 0.0,
        reset: "manual",
        doc: "Rasgo na correia final. Para imediatamente toda a linha e fecha vazadores."
      },
      {
        cause: "AL_NIVEL_HH_CHT02",
        effect: ["GATE_CLOSE_ONE", "LIMIT_VELOCIDADES_80pct"],
        type: "alarm_action",
        delay_s: 0.0,
        reset: "auto_when_normal",
        doc: "Nível muito alto em chute. Fecha 1 vazador e limita velocidade até normalizar."
      },
      {
        cause: "AL_CORR01_SUBVELOCIDADE",
        effect: ["REDUZIR_A_TOT_20pct", "MANTER_BUFFER_60pct"],
        type: "alarm_action",
        delay_s: 0.5,
        reset: "auto_when_normal",
        doc: "Subvelocidade na primeira correia. Reduz abertura total dos vazadores para recuperar RPM."
      },
      {
        cause: "TRIP_ELV01_SOBRETEMP",
        effect: ["CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
        type: "hard_trip",
        delay_s: 0.0,
        reset: "manual",
        doc: "Superaquecimento no elevador. Para elevador, upstream e fecha vazadores."
      },
      {
        cause: "SEG_EMERG_GERAL",
        effect: ["CMD_ALL_STOP", "GATES_CLOSE_ALL"],
        type: "emergency",
        delay_s: 0.0,
        reset: "manual",
        doc: "Acionamento de emergência geral. Parada de toda a planta e fechamento imediato dos vazadores."
      }
    ],
    doc: "Matriz de causa-efeito. O simulador aplica as ações quando as causas são verdadeiras, respeitando delays e regras de reset."
  },

  maintenance: {
    health_model: {
      equation: "H_next = H - (k_uso*carga_rel) - (k_choque*eventos)",
      thresholds_pct: { warn: 80, plan: 60, trip: 40 },
      k: { k_uso: 0.002, k_choque: 0.02 }
    },
    sensors: { vibration_mm_s: true, oil_temp_C: true, cycle_counter: true },
    hours_counters: true,
    doc: "Modelo de saúde por ativo. Reduz saúde com carga e eventos. Gera alarmes de preventiva/planejamento e pode levar a trip de proteção de manutenção."
  },

  energy: {
    measurements_per_device: ["V_ll", "I", "P_kW", "Q_kvar", "S_kVA", "PF", "kWh", "kWh_per_ton"],
    kpis: ["tph", "kWh_per_ton", "cost_per_ship", "PF_avg"],
    alarms: ["AL_FP_BAIXO", "AL_SOBRECORRENTE", "TRIP_SOBRECARGA"],
    doc: "Camada energética completa. Cada equipamento publica grandezas elétricas e acumuladores. KPIs calculam eficiência e custo por navio."
  },

  simulation: {
    dt_s: 1,
    T_final_s: 3600,
    outputs: ["flows_tph", "levels_pct", "currents_A", "powers_kW", "temps_C", "alarms", "trips", "kWh", "kWh_per_t"],
    doc: "Parâmetros do integrador de tempo discreto. A cada dt_s, atualiza estados, aplica controles e registra variáveis e eventos."
  }
};
