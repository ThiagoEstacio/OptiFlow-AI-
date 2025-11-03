#!/usr/bin/env python3
"""
Test OPC-UA Connection Gateway
Simple gateway to test connection to OptiFlow Terminal Simulator
"""

import asyncio
import sys
from datetime import datetime
from asyncua import Client
from asyncua.common.node import Node


class OPCUATestGateway:
    """Simple OPC-UA test gateway"""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.client = None
        self.running = False

    async def connect(self) -> bool:
        """Connect to OPC-UA server"""
        try:
            print(f"\n{'='*70}")
            print("🔌 Conectando ao servidor OPC-UA...")
            print(f"   Endpoint: {self.endpoint}")
            print('='*70)

            self.client = Client(url=self.endpoint, timeout=10)
            await self.client.connect()

            # Verify connection
            namespaces = await self.client.get_namespace_array()
            print(f"\n✅ Conexão estabelecida com sucesso!")
            print(f"   Namespaces disponíveis: {len(namespaces)}")
            for i, ns in enumerate(namespaces):
                print(f"     [{i}] {ns}")

            return True

        except Exception as e:
            print(f"\n❌ Falha na conexão: {str(e)}")
            return False

    async def browse_tags(self):
        """Browse available OPC-UA tags"""
        try:
            print(f"\n{'='*70}")
            print("📂 Navegando tags disponíveis...")
            print('='*70)

            # Get root Objects folder (namespace 2 - OptiFlow)
            objects = self.client.get_objects_node()
            print(f"\n✓ Nó Objects encontrado: {objects}")

            # Browse children
            children = await objects.get_children()
            print(f"\n✓ Encontrados {len(children)} nós filho:")

            for child in children[:10]:  # Show first 10
                try:
                    browse_name = await child.read_browse_name()
                    node_id = child.nodeid.to_string()
                    print(f"   • {browse_name.Name} [{node_id}]")
                except:
                    pass

            return True

        except Exception as e:
            print(f"❌ Erro ao navegar tags: {str(e)}")
            return False

    async def read_sample_tags(self):
        """Read sample tags from simulator"""
        try:
            print(f"\n{'='*70}")
            print("📊 Lendo tags de teste...")
            print('='*70)

            # Define tags to read
            tags = [
                ("ns=2;s=TEAG.SYSTEM.RUNNING", "Sistema Rodando"),
                ("ns=2;s=TEAG.ARZ.ESTOQUE.PV", "Estoque Armazém (t)"),
                ("ns=2;s=TEAG.ARZ.NIVEL.PV", "Nível Armazém (%)"),
                ("ns=2;s=TEAG.ARZ.CORR01.VAZAO.PV", "Correia 01 Vazão (t/h)"),
                ("ns=2;s=TEAG.ELV.ELV01.VAZAO.PV", "Elevador Vazão (t/h)"),
                ("ns=2;s=TEAG.BAL.BAL01.PESO.PV", "Balança Peso (kg)"),
                ("ns=2;s=TEAG.SLD.SLD01.VAZAO.PV", "Shiploader Vazão (t/h)"),
                ("ns=2;s=TEAG.KPIs.ENERGIA_TOTAL.TOT", "Energia Total (kWh)"),
                ("ns=2;s=TEAG.KPIs.PRODUCAO_TOTAL.TOT", "Produção Total (t)"),
            ]

            print("\n")
            success_count = 0

            for node_id, description in tags:
                try:
                    node = self.client.get_node(node_id)
                    value = await node.read_value()
                    data_value = await node.read_data_value()

                    quality = "GOOD" if data_value.StatusCode.is_good() else "BAD"

                    print(f"✓ {description:<35} = {value:>12.2f}  [{quality}]")
                    success_count += 1

                except Exception as e:
                    print(f"✗ {description:<35} = ERRO: {str(e)[:40]}")

            print(f"\n{'='*70}")
            print(f"✅ Leitura concluída: {success_count}/{len(tags)} tags lidas com sucesso")
            print('='*70)

            return success_count > 0

        except Exception as e:
            print(f"❌ Erro ao ler tags: {str(e)}")
            return False

    async def continuous_monitoring(self, interval: int = 5):
        """Monitor tags continuously"""
        try:
            print(f"\n{'='*70}")
            print(f"📡 Iniciando monitoramento contínuo (intervalo: {interval}s)")
            print("   Pressione Ctrl+C para parar")
            print('='*70)

            # Key tags to monitor
            monitor_tags = [
                ("ns=2;s=TEAG.ARZ.CORR01.VAZAO.PV", "CORR01 Vazão", "t/h"),
                ("ns=2;s=TEAG.ELV.ELV01.VAZAO.PV", "ELV01 Vazão", "t/h"),
                ("ns=2;s=TEAG.BAL.BAL01.PESO.PV", "BAL01 Peso", "kg"),
                ("ns=2;s=TEAG.SLD.SLD01.VAZAO.PV", "SLD01 Vazão", "t/h"),
                ("ns=2;s=TEAG.KPIs.ENERGIA_TOTAL.TOT", "Energia Total", "kWh"),
            ]

            self.running = True
            iteration = 0

            while self.running:
                iteration += 1
                timestamp = datetime.now().strftime("%H:%M:%S")

                print(f"\n[{timestamp}] Iteração #{iteration}")
                print("-" * 70)

                for node_id, name, unit in monitor_tags:
                    try:
                        node = self.client.get_node(node_id)
                        value = await node.read_value()
                        print(f"  {name:<20} = {value:>10.2f} {unit}")
                    except Exception as e:
                        print(f"  {name:<20} = ERRO")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoramento interrompido pelo usuário")
            self.running = False
        except Exception as e:
            print(f"\n❌ Erro no monitoramento: {str(e)}")
            self.running = False

    async def disconnect(self):
        """Disconnect from OPC-UA server"""
        try:
            if self.client:
                await self.client.disconnect()
                print("\n🔌 Desconectado do servidor OPC-UA")
        except Exception as e:
            print(f"❌ Erro ao desconectar: {str(e)}")

    async def run_tests(self, continuous: bool = False):
        """Run complete test suite"""
        try:
            # 1. Connect
            if not await self.connect():
                return False

            # 2. Browse tags
            await self.browse_tags()

            # 3. Read sample tags
            await self.read_sample_tags()

            # 4. Continuous monitoring (optional)
            if continuous:
                await self.continuous_monitoring(interval=5)

            return True

        except Exception as e:
            print(f"\n❌ Erro nos testes: {str(e)}")
            return False
        finally:
            await self.disconnect()


async def main():
    """Main entry point"""
    print("\n" + "="*70)
    print(" 🚢  OPTIFLOW TERMINAL - GATEWAY DE TESTE OPC-UA")
    print("="*70)

    # Configuration
    endpoint = "opc.tcp://localhost:4840/optiflow/terminal"

    # Create gateway
    gateway = OPCUATestGateway(endpoint)

    # Run tests
    continuous = "--continuous" in sys.argv or "-c" in sys.argv

    try:
        await gateway.run_tests(continuous=continuous)
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido pelo usuário")
    finally:
        print("\n" + "="*70)
        print("✅  Teste concluído")
        print("="*70)
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
