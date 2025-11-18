-- Atualização de Tags para Português
-- OptiFlow AI - Terminal Graneleiro

-- ============================================
-- CORREIA 01 (CORR01) - Transportador 01
-- ============================================

UPDATE tags SET 
    description = 'Correia 01 - Corrente Elétrica do Motor',
    unit = 'A',
    min_value = 0,
    max_value = 200
WHERE name = 'CORR01.current_a';

UPDATE tags SET 
    description = 'Correia 01 - Vazão de Material',
    unit = 't/h',
    min_value = 0,
    max_value = 1000
WHERE name = 'CORR01.flow_tph';

UPDATE tags SET 
    description = 'Correia 01 - Carga do Transportador',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'CORR01.load_pct';

UPDATE tags SET 
    description = 'Correia 01 - Desalinhamento da Correia',
    unit = 'mm',
    min_value = 0,
    max_value = 50
WHERE name = 'CORR01.misalignment';

UPDATE tags SET 
    description = 'Correia 01 - Potência Consumida',
    unit = 'kW',
    min_value = 0,
    max_value = 500
WHERE name = 'CORR01.power_kw';

UPDATE tags SET 
    description = 'Correia 01 - Status Operacional',
    unit = '',
    min_value = 0,
    max_value = 1
WHERE name = 'CORR01.running';

UPDATE tags SET 
    description = 'Correia 01 - Velocidade da Correia',
    unit = 'm/s',
    min_value = 0,
    max_value = 10
WHERE name = 'CORR01.speed_mps';

UPDATE tags SET 
    description = 'Correia 01 - Temperatura do Rolamento',
    unit = '°C',
    min_value = 0,
    max_value = 150
WHERE name = 'CORR01.temp_c';

-- ============================================
-- CORREIA 02 (CORR02) - Transportador 02
-- ============================================

UPDATE tags SET 
    description = 'Correia 02 - Corrente Elétrica do Motor',
    unit = 'A',
    min_value = 0,
    max_value = 200
WHERE name = 'CORR02.current_a';

UPDATE tags SET 
    description = 'Correia 02 - Vazão de Material',
    unit = 't/h',
    min_value = 0,
    max_value = 1000
WHERE name = 'CORR02.flow_tph';

UPDATE tags SET 
    description = 'Correia 02 - Carga do Transportador',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'CORR02.load_pct';

UPDATE tags SET 
    description = 'Correia 02 - Desalinhamento da Correia',
    unit = 'mm',
    min_value = 0,
    max_value = 50
WHERE name = 'CORR02.misalignment';

UPDATE tags SET 
    description = 'Correia 02 - Potência Consumida',
    unit = 'kW',
    min_value = 0,
    max_value = 500
WHERE name = 'CORR02.power_kw';

UPDATE tags SET 
    description = 'Correia 02 - Status Operacional',
    unit = '',
    min_value = 0,
    max_value = 1
WHERE name = 'CORR02.running';

UPDATE tags SET 
    description = 'Correia 02 - Velocidade da Correia',
    unit = 'm/s',
    min_value = 0,
    max_value = 10
WHERE name = 'CORR02.speed_mps';

UPDATE tags SET 
    description = 'Correia 02 - Temperatura do Rolamento',
    unit = '°C',
    min_value = 0,
    max_value = 150
WHERE name = 'CORR02.temp_c';

-- ============================================
-- CORREIA 03 (CORR03) - Transportador 03
-- ============================================

UPDATE tags SET 
    description = 'Correia 03 - Corrente Elétrica do Motor',
    unit = 'A',
    min_value = 0,
    max_value = 200
WHERE name = 'CORR03.current_a';

UPDATE tags SET 
    description = 'Correia 03 - Vazão de Material',
    unit = 't/h',
    min_value = 0,
    max_value = 1000
WHERE name = 'CORR03.flow_tph';

UPDATE tags SET 
    description = 'Correia 03 - Carga do Transportador',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'CORR03.load_pct';

UPDATE tags SET 
    description = 'Correia 03 - Desalinhamento da Correia',
    unit = 'mm',
    min_value = 0,
    max_value = 50
WHERE name = 'CORR03.misalignment';

UPDATE tags SET 
    description = 'Correia 03 - Potência Consumida',
    unit = 'kW',
    min_value = 0,
    max_value = 500
WHERE name = 'CORR03.power_kw';

UPDATE tags SET 
    description = 'Correia 03 - Status Operacional',
    unit = '',
    min_value = 0,
    max_value = 1
WHERE name = 'CORR03.running';

UPDATE tags SET 
    description = 'Correia 03 - Velocidade da Correia',
    unit = 'm/s',
    min_value = 0,
    max_value = 10
WHERE name = 'CORR03.speed_mps';

UPDATE tags SET 
    description = 'Correia 03 - Temperatura do Rolamento',
    unit = '°C',
    min_value = 0,
    max_value = 150
WHERE name = 'CORR03.temp_c';

-- ============================================
-- SILOS (SILO01, SILO02, SILO03)
-- ============================================

-- SILO01
UPDATE tags SET 
    description = 'Silo 01 - Umidade dos Grãos',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'SILO01.humidity_pct';

UPDATE tags SET 
    description = 'Silo 01 - Nível de Enchimento',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'SILO01.level_pct';

UPDATE tags SET 
    description = 'Silo 01 - Pressão Interna',
    unit = 'Pa',
    min_value = 0,
    max_value = 5000
WHERE name = 'SILO01.pressure_pa';

UPDATE tags SET 
    description = 'Silo 01 - Temperatura dos Grãos',
    unit = '°C',
    min_value = -10,
    max_value = 60
WHERE name = 'SILO01.temp_grain_c';

UPDATE tags SET 
    description = 'Silo 01 - Peso Total Armazenado',
    unit = 't',
    min_value = 0,
    max_value = 10000
WHERE name = 'SILO01.weight_t';

-- SILO02
UPDATE tags SET 
    description = 'Silo 02 - Umidade dos Grãos',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'SILO02.humidity_pct';

UPDATE tags SET 
    description = 'Silo 02 - Nível de Enchimento',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'SILO02.level_pct';

UPDATE tags SET 
    description = 'Silo 02 - Pressão Interna',
    unit = 'Pa',
    min_value = 0,
    max_value = 5000
WHERE name = 'SILO02.pressure_pa';

UPDATE tags SET 
    description = 'Silo 02 - Temperatura dos Grãos',
    unit = '°C',
    min_value = -10,
    max_value = 60
WHERE name = 'SILO02.temp_grain_c';

UPDATE tags SET 
    description = 'Silo 02 - Peso Total Armazenado',
    unit = 't',
    min_value = 0,
    max_value = 10000
WHERE name = 'SILO02.weight_t';

-- SILO03
UPDATE tags SET 
    description = 'Silo 03 - Umidade dos Grãos',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'SILO03.humidity_pct';

UPDATE tags SET 
    description = 'Silo 03 - Nível de Enchimento',
    unit = '%',
    min_value = 0,
    max_value = 100
WHERE name = 'SILO03.level_pct';

UPDATE tags SET 
    description = 'Silo 03 - Pressão Interna',
    unit = 'Pa',
    min_value = 0,
    max_value = 5000
WHERE name = 'SILO03.pressure_pa';

UPDATE tags SET 
    description = 'Silo 03 - Temperatura dos Grãos',
    unit = '°C',
    min_value = -10,
    max_value = 60
WHERE name = 'SILO03.temp_grain_c';

UPDATE tags SET 
    description = 'Silo 03 - Peso Total Armazenado',
    unit = 't',
    min_value = 0,
    max_value = 10000
WHERE name = 'SILO03.weight_t';

-- ============================================
-- Verificação Final
-- ============================================

SELECT 
    'Tags Atualizados' as status,
    COUNT(*) as total_tags,
    COUNT(CASE WHEN description IS NOT NULL AND description != '' THEN 1 END) as com_descricao,
    COUNT(CASE WHEN unit IS NOT NULL AND unit != '' THEN 1 END) as com_unidade
FROM tags;

-- Mostra alguns exemplos
SELECT name, description, unit, min_value, max_value 
FROM tags 
WHERE description IS NOT NULL 
ORDER BY name 
LIMIT 10;
