-- Script para popular tag_labels com exemplos
-- Converte tags técnicas em nomes amigáveis organizados por área e equipamento

-- ============================================================================
-- SISTEMA DE ARMAZÉM (ARZ)
-- ============================================================================

-- Portões (GATES)
INSERT INTO tag_labels (id, tag_id, display_name, short_name, equipment_name, area_name, system_name, custom_description, is_visible, is_favorite)
SELECT 
    gen_random_uuid(),
    t.id,
    CASE t.name
        WHEN 'ARZ_GATES_GATE01_POSICAO_PV' THEN 'Posição do Portão 1'
        WHEN 'ARZ_GATES_GATE01_POSICAO_SP' THEN 'Setpoint Posição Portão 1'
        WHEN 'ARZ_GATES_GATE01_STATUS' THEN 'Status do Portão 1'
        WHEN 'ARZ_GATES_GATE02_POSICAO_PV' THEN 'Posição do Portão 2'
        WHEN 'ARZ_GATES_GATE02_POSICAO_SP' THEN 'Setpoint Posição Portão 2'
        WHEN 'ARZ_GATES_GATE02_STATUS' THEN 'Status do Portão 2'
    END,
    CASE t.name
        WHEN 'ARZ_GATES_GATE01_POSICAO_PV' THEN 'Portão 1 Pos'
        WHEN 'ARZ_GATES_GATE01_POSICAO_SP' THEN 'Portão 1 SP'
        WHEN 'ARZ_GATES_GATE01_STATUS' THEN 'Portão 1 Status'
        WHEN 'ARZ_GATES_GATE02_POSICAO_PV' THEN 'Portão 2 Pos'
        WHEN 'ARZ_GATES_GATE02_POSICAO_SP' THEN 'Portão 2 SP'
        WHEN 'ARZ_GATES_GATE02_STATUS' THEN 'Portão 2 Status'
    END,
    'Portões de Entrada',
    'Armazém 01',
    'Sistema de Acesso',
    CASE t.name
        WHEN 'ARZ_GATES_GATE01_POSICAO_PV' THEN 'Posição atual do portão 1 de entrada do armazém (0-100%)'
        WHEN 'ARZ_GATES_GATE01_POSICAO_SP' THEN 'Valor desejado para posição do portão 1 (0-100%)'
        WHEN 'ARZ_GATES_GATE01_STATUS' THEN 'Status operacional do portão 1 (0=fechado, 1=aberto, 2=em movimento)'
        WHEN 'ARZ_GATES_GATE02_POSICAO_PV' THEN 'Posição atual do portão 2 de entrada do armazém (0-100%)'
        WHEN 'ARZ_GATES_GATE02_POSICAO_SP' THEN 'Valor desejado para posição do portão 2 (0-100%)'
        WHEN 'ARZ_GATES_GATE02_STATUS' THEN 'Status operacional do portão 2 (0=fechado, 1=aberto, 2=em movimento)'
    END,
    true,
    t.name LIKE '%POSICAO_PV' -- Marca posições como favoritas
FROM tags t
WHERE t.name LIKE 'ARZ_GATES%'
ON CONFLICT (tag_id) DO NOTHING;

-- Correias Transportadoras (CORR)
INSERT INTO tag_labels (id, tag_id, display_name, short_name, equipment_name, area_name, system_name, custom_description, is_visible, is_favorite)
SELECT 
    gen_random_uuid(),
    t.id,
    CASE 
        WHEN t.name LIKE '%CORR01_VELOCIDADE_PV' THEN 'Velocidade Correia 01'
        WHEN t.name LIKE '%CORR01_VELOCIDADE_SP' THEN 'Setpoint Velocidade Correia 01'
        WHEN t.name LIKE '%CORR01_STATUS' THEN 'Status Correia 01'
        WHEN t.name LIKE '%CORR01_CORRENTE' THEN 'Corrente Motor Correia 01'
        WHEN t.name LIKE '%CORR02_VELOCIDADE_PV' THEN 'Velocidade Correia 02'
        WHEN t.name LIKE '%CORR02_VELOCIDADE_SP' THEN 'Setpoint Velocidade Correia 02'
        WHEN t.name LIKE '%CORR02_STATUS' THEN 'Status Correia 02'
        WHEN t.name LIKE '%CORR02_CORRENTE' THEN 'Corrente Motor Correia 02'
    END,
    CASE 
        WHEN t.name LIKE '%CORR01_VELOCIDADE_PV' THEN 'C01 Vel'
        WHEN t.name LIKE '%CORR01_VELOCIDADE_SP' THEN 'C01 SP'
        WHEN t.name LIKE '%CORR01_STATUS' THEN 'C01 Status'
        WHEN t.name LIKE '%CORR01_CORRENTE' THEN 'C01 Corrente'
        WHEN t.name LIKE '%CORR02_VELOCIDADE_PV' THEN 'C02 Vel'
        WHEN t.name LIKE '%CORR02_VELOCIDADE_SP' THEN 'C02 SP'
        WHEN t.name LIKE '%CORR02_STATUS' THEN 'C02 Status'
        WHEN t.name LIKE '%CORR02_CORRENTE' THEN 'C02 Corrente'
    END,
    CASE 
        WHEN t.name LIKE '%CORR01%' THEN 'Correia Transportadora 01'
        WHEN t.name LIKE '%CORR02%' THEN 'Correia Transportadora 02'
    END,
    'Armazém 01',
    'Sistema de Transporte',
    CASE 
        WHEN t.name LIKE '%VELOCIDADE_PV' THEN 'Velocidade atual da correia transportadora em m/min'
        WHEN t.name LIKE '%VELOCIDADE_SP' THEN 'Velocidade desejada para a correia transportadora'
        WHEN t.name LIKE '%STATUS' THEN 'Status operacional (0=parado, 1=em operação, 2=falha)'
        WHEN t.name LIKE '%CORRENTE' THEN 'Corrente elétrica do motor em amperes'
    END,
    true,
    t.name LIKE '%VELOCIDADE_PV' OR t.name LIKE '%STATUS'
FROM tags t
WHERE t.name LIKE '%CORR0%'
ON CONFLICT (tag_id) DO NOTHING;

-- Inventário
INSERT INTO tag_labels (id, tag_id, display_name, short_name, equipment_name, area_name, system_name, custom_description, is_visible, is_favorite)
SELECT 
    gen_random_uuid(),
    t.id,
    'Nível de Inventário',
    'Inventário',
    'Sistema de Inventário',
    'Armazém 01',
    'Sistema de Gestão',
    'Nível atual do inventário no armazém em toneladas',
    true,
    true
FROM tags t
WHERE t.name = 'ARZ_INVENTARIO_PV'
ON CONFLICT (tag_id) DO NOTHING;

-- ============================================================================
-- SISTEMA GERAL
-- ============================================================================

-- Status do Sistema
INSERT INTO tag_labels (id, tag_id, display_name, short_name, equipment_name, area_name, system_name, custom_description, is_visible, is_favorite)
SELECT 
    gen_random_uuid(),
    t.id,
    CASE t.name
        WHEN 'SYSTEM_RUNNING_PV' THEN 'Sistema em Operação'
        WHEN 'SYSTEM_MODE' THEN 'Modo de Operação'
        WHEN 'SYSTEM_UPTIME' THEN 'Tempo de Atividade'
    END,
    CASE t.name
        WHEN 'SYSTEM_RUNNING_PV' THEN 'Sistema'
        WHEN 'SYSTEM_MODE' THEN 'Modo'
        WHEN 'SYSTEM_UPTIME' THEN 'Uptime'
    END,
    'Sistema Principal',
    'Geral',
    'Sistema de Controle',
    CASE t.name
        WHEN 'SYSTEM_RUNNING_PV' THEN 'Indica se o sistema está em operação (0=parado, 1=operando)'
        WHEN 'SYSTEM_MODE' THEN 'Modo atual do sistema (0=manual, 1=automático, 2=manutenção)'
        WHEN 'SYSTEM_UPTIME' THEN 'Tempo de atividade do sistema em horas'
    END,
    true,
    t.name = 'SYSTEM_RUNNING_PV'
FROM tags t
WHERE t.name LIKE 'SYSTEM_%'
ON CONFLICT (tag_id) DO NOTHING;

-- ============================================================================
-- ALARMES
-- ============================================================================

INSERT INTO tag_labels (id, tag_id, display_name, short_name, equipment_name, area_name, system_name, custom_description, is_visible, is_favorite)
SELECT 
    gen_random_uuid(),
    t.id,
    CASE t.name
        WHEN 'ALARMES_TOTAL_COUNT' THEN 'Total de Alarmes'
        WHEN 'ALARMES_CRITICAL_COUNT' THEN 'Alarmes Críticos'
        WHEN 'ALARMES_HIGH_COUNT' THEN 'Alarmes Altos'
        WHEN 'ALARMES_MEDIUM_COUNT' THEN 'Alarmes Médios'
        WHEN 'ALARMES_UNACKNOWLEDGED_COUNT' THEN 'Alarmes Não Reconhecidos'
    END,
    CASE t.name
        WHEN 'ALARMES_TOTAL_COUNT' THEN 'Total'
        WHEN 'ALARMES_CRITICAL_COUNT' THEN 'Críticos'
        WHEN 'ALARMES_HIGH_COUNT' THEN 'Altos'
        WHEN 'ALARMES_MEDIUM_COUNT' THEN 'Médios'
        WHEN 'ALARMES_UNACKNOWLEDGED_COUNT' THEN 'Não Recon.'
    END,
    'Sistema de Alarmes',
    'Geral',
    'Sistema de Monitoramento',
    CASE t.name
        WHEN 'ALARMES_TOTAL_COUNT' THEN 'Contagem total de alarmes ativos no sistema'
        WHEN 'ALARMES_CRITICAL_COUNT' THEN 'Número de alarmes críticos ativos (prioridade máxima)'
        WHEN 'ALARMES_HIGH_COUNT' THEN 'Número de alarmes de alta prioridade ativos'
        WHEN 'ALARMES_MEDIUM_COUNT' THEN 'Número de alarmes de média prioridade ativos'
        WHEN 'ALARMES_UNACKNOWLEDGED_COUNT' THEN 'Alarmes que ainda não foram reconhecidos pelos operadores'
    END,
    true,
    t.name IN ('ALARMES_CRITICAL_COUNT', 'ALARMES_UNACKNOWLEDGED_COUNT')
FROM tags t
WHERE t.name LIKE 'ALARMES_%'
ON CONFLICT (tag_id) DO NOTHING;

-- Seleciona estatísticas
SELECT 
    COUNT(*) as total_labels,
    COUNT(DISTINCT area_name) as total_areas,
    COUNT(DISTINCT equipment_name) as total_equipments,
    COUNT(DISTINCT system_name) as total_systems,
    SUM(CASE WHEN is_favorite THEN 1 ELSE 0 END) as favorites
FROM tag_labels;
