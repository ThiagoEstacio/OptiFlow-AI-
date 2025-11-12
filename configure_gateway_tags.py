#!/usr/bin/env python3
"""
Configure Gateway Tags
Creates tag configurations in PostgreSQL for OPC UA data collection
"""

import asyncio
import asyncpg
import os
from datetime import datetime

# Database configuration
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "optiflow")
DB_USER = os.getenv("POSTGRES_USER", "optiflow")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "optiflow123")


# Tag configurations to create
# Format: (tag_name, description, node_id, data_type, unit, sample_interval_ms)
TAGS_TO_CREATE = [
    # System status
    ("SYSTEM.RUNNING.PV", "Sistema em execução", "ns=2;i=2", "boolean", "", 1000),
    
    # Armazém - Inventário e Nível
    ("ARZ.INVENTARIO.PV", "Inventário do armazém (ton)", "ns=2;i=3", "float", "ton", 2000),
    ("ARZ.NIVEL.PV", "Nível do armazém (%)", "ns=2;i=4", "float", "%", 2000),
    
    # Portões principais (GATE01-04 estão ativos com vazão ~151 ton/h)
    ("ARZ.GATES.GATE01.POSICAO.PV", "Portão 1 - Posição", "ns=2;i=8", "float", "%", 1000),
    ("ARZ.GATES.GATE01.VAZAO.PV", "Portão 1 - Vazão", "ns=2;i=10", "float", "ton/h", 1000),
    ("ARZ.GATES.GATE01.ENTUPIDO.AL", "Portão 1 - Alarme Entupido", "ns=2;i=11", "boolean", "", 1000),
    
    ("ARZ.GATES.GATE02.POSICAO.PV", "Portão 2 - Posição", "ns=2;i=13", "float", "%", 1000),
    ("ARZ.GATES.GATE02.VAZAO.PV", "Portão 2 - Vazão", "ns=2;i=15", "float", "ton/h", 1000),
    
    ("ARZ.GATES.GATE03.POSICAO.PV", "Portão 3 - Posição", "ns=2;i=18", "float", "%", 1000),
    ("ARZ.GATES.GATE03.VAZAO.PV", "Portão 3 - Vazão", "ns=2;i=20", "float", "ton/h", 1000),
    
    # Correias transportadoras (3 ativas)
    ("ARZ.CORR01.LIGADO.FB", "Correia 1 - Ligada", "ns=2;i=58", "boolean", "", 1000),
    ("ARZ.CORR01.VAZAO.PV", "Correia 1 - Vazão", "ns=2;i=61", "float", "ton/h", 1000),
    ("ARZ.CORR01.RPM.PV", "Correia 1 - RPM", "ns=2;i=59", "float", "rpm", 2000),
    ("ARZ.CORR01.CARGA.PV", "Correia 1 - Carga", "ns=2;i=62", "float", "%", 2000),
    ("ARZ.CORR01.POTENCIA.PV", "Correia 1 - Potência", "ns=2;i=64", "float", "kW", 2000),
    ("ARZ.CORR01.TEMP_MANCAL.PV", "Correia 1 - Temp Mancal", "ns=2;i=65", "float", "°C", 3000),
    
    ("ARZ.CORR02.LIGADO.FB", "Correia 2 - Ligada", "ns=2;i=73", "boolean", "", 1000),
    ("ARZ.CORR02.VAZAO.PV", "Correia 2 - Vazão", "ns=2;i=76", "float", "ton/h", 1000),
    ("ARZ.CORR02.POTENCIA.PV", "Correia 2 - Potência", "ns=2;i=79", "float", "kW", 2000),
    
    ("ARZ.CORR03.LIGADO.FB", "Correia 3 - Ligada", "ns=2;i=88", "boolean", "", 1000),
    ("ARZ.CORR03.VAZAO.PV", "Correia 3 - Vazão", "ns=2;i=91", "float", "ton/h", 1000),
    ("ARZ.CORR03.POTENCIA.PV", "Correia 3 - Potência", "ns=2;i=94", "float", "kW", 2000),
    
    # Elevador
    ("ELV.ELV01.LIGADO.FB", "Elevador 1 - Ligado", "ns=2;i=104", "boolean", "", 1000),
    ("ELV.ELV01.VAZAO.PV", "Elevador 1 - Vazão", "ns=2;i=106", "float", "ton/h", 1000),
    ("ELV.ELV01.POTENCIA.PV", "Elevador 1 - Potência", "ns=2;i=108", "float", "kW", 2000),
    ("ELV.ELV01.TEMP_MOTOR.PV", "Elevador 1 - Temp Motor", "ns=2;i=109", "float", "°C", 3000),
    
    # Balança
    ("BAL.BAL01.LIGADO.FB", "Balança 1 - Ligada", "ns=2;i=115", "boolean", "", 1000),
    ("BAL.BAL01.PESO.PV", "Balança 1 - Peso Atual", "ns=2;i=116", "float", "kg", 500),
    ("BAL.BAL01.PESO.SP", "Balança 1 - Peso Setpoint", "ns=2;i=117", "float", "kg", 2000),
    ("BAL.BAL01.VAZAO.PV", "Balança 1 - Vazão", "ns=2;i=120", "float", "ton/h", 1000),
    ("BAL.BAL01.ESTADO.PV", "Balança 1 - Estado", "ns=2;i=121", "string", "", 1000),
    ("BAL.BAL01.CICLOS.TOT", "Balança 1 - Total Ciclos", "ns=2;i=118", "float", "", 5000),
    
    # Sistema de descarga (Ship Loader)
    ("SLD.SLD01.LIGADO.FB", "Ship Loader 1 - Ligado", "ns=2;i=124", "boolean", "", 1000),
    ("SLD.SLD01.VAZAO.PV", "Ship Loader 1 - Vazão", "ns=2;i=126", "float", "ton/h", 1000),
    ("SLD.SLD01.VAZAO.SP", "Ship Loader 1 - Vazão SP", "ns=2;i=125", "float", "ton/h", 2000),
    ("SLD.SLD01.POTENCIA.PV", "Ship Loader 1 - Potência", "ns=2;i=127", "float", "kW", 2000),
    ("SLD.SLD01.POEIRA.PV", "Ship Loader 1 - Nível Poeira", "ns=2;i=128", "float", "mg/m³", 5000),
    
    # KPIs gerais
    ("KPIs.ENERGIA_TOTAL.TOT", "Energia Total Consumida", "ns=2;i=130", "float", "kWh", 5000),
    ("KPIs.PRODUCAO_TOTAL.TOT", "Produção Total", "ns=2;i=131", "float", "ton", 5000),
    ("KPIs.EFICIENCIA_ENERGIA.PV", "Eficiência Energética", "ns=2;i=132", "float", "kWh/ton", 5000),
    ("KPIs.CUSTO_ENERGIA.TOT", "Custo Total Energia", "ns=2;i=133", "float", "R$", 10000),
    
    # Alarmes e Manutenção
    ("ALARMES.TOTAL.COUNT", "Total de Alarmes", "ns=2;i=174", "float", "", 2000),
    ("ALARMES.CRITICAL.COUNT", "Alarmes Críticos", "ns=2;i=175", "float", "", 1000),
    ("MANUTENCAO.HEALTH_MEDIA.PV", "Saúde Média Equipamentos", "ns=2;i=180", "float", "%", 5000),
]


async def configure_tags():
    """Configure gateway tags in PostgreSQL"""
    
    print("\n" + "="*80)
    print("🔧 CONFIGURANDO TAGS DO GATEWAY")
    print("="*80 + "\n")
    
    try:
        # Connect to database
        print(f"📡 Conectando ao banco: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("✅ Conectado!\n")
        
        # Get gateway IDs
        gateways = await conn.fetch(
            "SELECT id, name FROM gateways WHERE type = 'opcua' ORDER BY id"
        )
        
        if not gateways:
            print("❌ Nenhum gateway OPC-UA encontrado!")
            return
        
        print(f"📋 Gateways encontrados:")
        for gw in gateways:
            print(f"   - ID {gw['id']}: {gw['name']}")
        
        # Use first gateway
        gateway_id = gateways[0]['id']
        gateway_name = gateways[0]['name']
        
        print(f"\n🎯 Configurando tags para gateway: {gateway_name} (ID: {gateway_id})\n")
        
        # Check existing tags
        existing = await conn.fetch(
            "SELECT tag_name FROM gateway_tags WHERE gateway_id = $1",
            gateway_id
        )
        existing_names = {row['tag_name'] for row in existing}
        
        if existing_names:
            print(f"⚠️  Encontradas {len(existing_names)} tags já configuradas")
            print("   Apenas novas tags serão adicionadas\n")
        
        # Insert tags
        created_count = 0
        skipped_count = 0
        
        for tag_name, description, node_id, data_type, unit, sample_interval in TAGS_TO_CREATE:
            if tag_name in existing_names:
                print(f"⏭️  Pulando: {tag_name} (já existe)")
                skipped_count += 1
                continue
            
            try:
                await conn.execute("""
                    INSERT INTO gateway_tags (
                        gateway_id, tag_name, description, 
                        node_id, data_type, unit, 
                        sample_interval_ms, enabled, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                    gateway_id, tag_name, description,
                    node_id, data_type, unit,
                    sample_interval, True, datetime.utcnow()
                )
                print(f"✅ Criado: {tag_name} - {description}")
                created_count += 1
            except Exception as e:
                print(f"❌ Erro criando {tag_name}: {e}")
        
        # Summary
        print("\n" + "="*80)
        print("📊 RESUMO:")
        print(f"   ✅ Tags criadas: {created_count}")
        print(f"   ⏭️  Tags existentes: {skipped_count}")
        print(f"   📝 Total configuradas: {created_count + len(existing_names)}")
        print("="*80 + "\n")
        
        # Show total tags for gateway
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM gateway_tags WHERE gateway_id = $1 AND enabled = true",
            gateway_id
        )
        print(f"🎯 Gateway '{gateway_name}' agora tem {total} tags ativas\n")
        
        await conn.close()
        
        print("✅ Configuração concluída!")
        print("\n💡 Próximo passo: Reinicie o gateway para carregar as novas tags")
        print("   comando: docker compose restart gateway\n")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(configure_tags())
