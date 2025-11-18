#!/usr/bin/env python3
"""
Script para atualizar tags com descrições em português
Mantém o relacionamento com InfluxDB através do campo 'name'
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurações do banco
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://optiflow:optiflow_password@localhost:5432/optiflow")

# Mapeamento de tags para descrições em português
TAG_DESCRIPTIONS = {
    # Transportadores (CORR = Correia / Belt)
    "current_a": {
        "description": "Corrente Elétrica do Motor",
        "unit": "A",
        "min": 0,
        "max": 200
    },
    "flow_tph": {
        "description": "Vazão de Material",
        "unit": "t/h",
        "min": 0,
        "max": 1000
    },
    "load_pct": {
        "description": "Carga do Transportador",
        "unit": "%",
        "min": 0,
        "max": 100
    },
    "misalignment": {
        "description": "Desalinhamento da Correia",
        "unit": "mm",
        "min": 0,
        "max": 50
    },
    "power_kw": {
        "description": "Potência Consumida",
        "unit": "kW",
        "min": 0,
        "max": 500
    },
    "running": {
        "description": "Status Operacional (Ligado/Desligado)",
        "unit": "",
        "min": 0,
        "max": 1
    },
    "speed_mps": {
        "description": "Velocidade da Correia",
        "unit": "m/s",
        "min": 0,
        "max": 10
    },
    "temp_c": {
        "description": "Temperatura do Rolamento",
        "unit": "°C",
        "min": 0,
        "max": 150
    },
    
    # Silos
    "level_pct": {
        "description": "Nível de Enchimento",
        "unit": "%",
        "min": 0,
        "max": 100
    },
    "temp_grain_c": {
        "description": "Temperatura dos Grãos",
        "unit": "°C",
        "min": -10,
        "max": 60
    },
    "humidity_pct": {
        "description": "Umidade dos Grãos",
        "unit": "%",
        "min": 0,
        "max": 100
    },
    "weight_t": {
        "description": "Peso Total Armazenado",
        "unit": "t",
        "min": 0,
        "max": 10000
    },
    "pressure_pa": {
        "description": "Pressão Interna",
        "unit": "Pa",
        "min": 0,
        "max": 5000
    },
    
    # Elevadores
    "bucket_speed_mps": {
        "description": "Velocidade dos Caçambas",
        "unit": "m/s",
        "min": 0,
        "max": 5
    },
    
    # Energia
    "grid_power_kw": {
        "description": "Potência Total da Rede",
        "unit": "kW",
        "min": 0,
        "max": 10000
    },
    "total_energy_kwh": {
        "description": "Energia Total Consumida",
        "unit": "kWh",
        "min": 0,
        "max": 1000000
    },
    "power_factor": {
        "description": "Fator de Potência",
        "unit": "",
        "min": 0,
        "max": 1
    },
    "grid_voltage_v": {
        "description": "Tensão da Rede Elétrica",
        "unit": "V",
        "min": 0,
        "max": 480
    },
}


def get_tag_info(tag_name):
    """
    Extrai informações do tag baseado no nome
    Formato: EQUIPMENT.variable ou just variable
    """
    # Separa equipamento e variável
    parts = tag_name.split('.')
    if len(parts) == 2:
        equipment, variable = parts
    else:
        equipment = ""
        variable = tag_name
    
    # Busca descrição da variável
    if variable in TAG_DESCRIPTIONS:
        info = TAG_DESCRIPTIONS[variable].copy()
        
        # Adiciona prefixo do equipamento na descrição
        if equipment:
            equipment_names = {
                "CORR01": "Correia 01 -",
                "CORR02": "Correia 02 -",
                "CORR03": "Correia 03 -",
                "CORR04": "Correia 04 -",
                "CORR05": "Correia 05 -",
                "ELEV01": "Elevador 01 -",
                "ELEV02": "Elevador 02 -",
                "SILO01": "Silo 01 -",
                "SILO02": "Silo 02 -",
                "SILO03": "Silo 03 -",
                "SILO04": "Silo 04 -",
                "SILO05": "Silo 05 -",
                "ENERGY": "Energia -",
            }
            prefix = equipment_names.get(equipment, f"{equipment} -")
            info["description"] = f"{prefix} {info['description']}"
        
        return info
    
    # Descrição padrão se não encontrar
    return {
        "description": f"Tag {tag_name}",
        "unit": "",
        "min": 0,
        "max": 100
    }


def update_tags():
    """Atualiza descrições dos tags no PostgreSQL"""
    print("=" * 60)
    print("Atualizando Tags com Descrições em Português")
    print("=" * 60)
    
    # Conecta ao banco
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Busca todos os tags
        result = session.execute(text("SELECT id, name FROM tags ORDER BY name"))
        tags = result.fetchall()
        
        print(f"\n📊 Total de tags encontrados: {len(tags)}")
        print("\nAtualizando...\n")
        
        updated_count = 0
        
        for tag_id, tag_name in tags:
            # Pega informações para este tag
            info = get_tag_info(tag_name)
            
            # Atualiza no banco
            update_query = text("""
                UPDATE tags 
                SET 
                    description = :description,
                    unit = :unit,
                    min_value = :min_value,
                    max_value = :max_value
                WHERE id = :id
            """)
            
            session.execute(update_query, {
                "id": tag_id,
                "description": info["description"],
                "unit": info["unit"],
                "min_value": info["min"],
                "max_value": info["max"]
            })
            
            print(f"✅ {tag_name:30} → {info['description']}")
            updated_count += 1
        
        session.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Atualização concluída! {updated_count} tags atualizados")
        print("=" * 60)
        
        # Mostra alguns exemplos
        print("\n📋 Exemplos de tags atualizados:\n")
        result = session.execute(text("""
            SELECT name, description, unit 
            FROM tags 
            WHERE description IS NOT NULL 
            ORDER BY name 
            LIMIT 10
        """))
        
        for name, desc, unit in result:
            unit_str = f" ({unit})" if unit else ""
            print(f"  {name:30} → {desc}{unit_str}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    update_tags()
