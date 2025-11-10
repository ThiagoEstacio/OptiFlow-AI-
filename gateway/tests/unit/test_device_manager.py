"""
Testes Unitários - Gateway Device Manager
==========================================

Testa o gerenciador de devices do gateway seguindo TDD

Autor: OptiFlow AI Team
Data: 2025-11-10
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestDeviceManagerInitialization:
    """Testes de inicialização do DeviceManager"""
    
    def test_should_initialize_with_backend_client_and_buffer(self):
        """
        DADO backend_client e buffer
        QUANDO DeviceManager é inicializado
        ENTÃO deve armazenar referências corretas
        """
        from gateway.app.services.device_manager import DeviceManager
        
        mock_backend = MagicMock()
        mock_buffer = MagicMock()
        
        manager = DeviceManager(
            backend_client=mock_backend,
            buffer=mock_buffer
        )
        
        assert manager.backend == mock_backend
        assert manager.buffer == mock_buffer
        assert len(manager.devices) == 0
    
    def test_should_have_protocol_handlers_mapping(self):
        """
        DADO DeviceManager inicializado
        QUANDO verifico protocol_handlers
        ENTÃO deve ter mapeamento de protocolos suportados
        """
        from gateway.app.services.device_manager import DeviceManager
        
        manager = DeviceManager(
            backend_client=MagicMock(),
            buffer=MagicMock()
        )
        
        assert "opc_ua" in manager.protocol_handlers
        assert "modbus" in manager.protocol_handlers
        assert "mqtt" in manager.protocol_handlers


class TestDeviceManagerAddDevice:
    """Testes de adição de devices"""
    
    @pytest.mark.asyncio
    async def test_should_add_opcua_device_successfully(self):
        """
        DADO configuração válida de device OPC-UA
        QUANDO add_device() é chamado
        ENTÃO device deve ser adicionado e conectado
        """
        from gateway.app.services.device_manager import DeviceManager
        
        mock_backend = MagicMock()
        mock_buffer = MagicMock()
        
        manager = DeviceManager(mock_backend, mock_buffer)
        
        with patch('gateway.app.protocols.opcua_handler.OPCUAHandler') as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.connect.return_value = True
            mock_handler_class.return_value = mock_handler
            
            config = {
                "endpoint": "opc.tcp://localhost:4840",
                "namespace_index": 2
            }
            
            result = await manager.add_device(
                device_id="test-device-1",
                protocol="opc_ua",
                config=config
            )
            
            assert result is True
            assert "test-device-1" in manager.devices
            mock_handler.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_not_add_duplicate_device(self):
        """
        DADO device já existente
        QUANDO tento adicionar novamente
        ENTÃO não deve adicionar duplicata
        """
        from gateway.app.services.device_manager import DeviceManager
        
        manager = DeviceManager(MagicMock(), MagicMock())
        
        with patch('gateway.app.protocols.opcua_handler.OPCUAHandler') as mock_handler_class:
            mock_handler = AsyncMock()
            mock_handler.connect.return_value = True
            mock_handler_class.return_value = mock_handler
            
            config = {"endpoint": "opc.tcp://localhost:4840"}
            
            # Adicionar primeira vez
            await manager.add_device("device-1", "opc_ua", config)
            
            # Tentar adicionar novamente
            result = await manager.add_device("device-1", "opc_ua", config)
            
            assert result is False  # Não deve adicionar
    
    @pytest.mark.asyncio
    async def test_should_reject_unsupported_protocol(self):
        """
        DADO protocolo não suportado
        QUANDO add_device() é chamado
        ENTÃO deve rejeitar com erro
        """
        from gateway.app.services.device_manager import DeviceManager
        
        manager = DeviceManager(MagicMock(), MagicMock())
        
        result = await manager.add_device(
            device_id="test",
            protocol="unsupported_protocol",
            config={}
        )
        
        assert result is False


class TestDeviceManagerStartCollection:
    """Testes de início de coleta de dados"""
    
    @pytest.mark.asyncio
    async def test_should_start_collection_loop(self):
        """
        DADO device adicionado
        QUANDO start_collection() é chamado
        ENTÃO loop de coleta deve iniciar
        """
        from gateway.app.services.device_manager import DeviceManager
        
        manager = DeviceManager(MagicMock(), MagicMock())
        
        # Mock device handler
        mock_handler = AsyncMock()
        mock_handler.read_tags.return_value = [
            {"tag_id": "TAG01", "value": 42.0, "quality": "GOOD"}
        ]
        manager.devices["test-device"] = mock_handler
        
        tags = [
            {"tag_id": "TAG01", "tag_name": "Test Tag", "address": "ns=2;s=TAG01"}
        ]
        
        with patch.object(manager, '_collection_loop', new_callable=AsyncMock) as mock_loop:
            await manager.start_collection("test-device", tags, scan_rate=1000)
            
            # Verificar que loop foi iniciado
            assert "test-device" in manager._collection_tasks
    
    @pytest.mark.asyncio
    async def test_should_stop_existing_collection_before_starting_new(self):
        """
        DADO collection já rodando
        QUANDO start_collection() é chamado novamente
        ENTÃO deve parar collection anterior
        """
        pytest.skip("Implementar lógica de stop")


class TestDeviceManagerCollectionLoop:
    """Testes do loop de coleta"""
    
    @pytest.mark.asyncio
    async def test_should_read_tags_at_scan_rate(self):
        """
        DADO scan_rate de 1000ms
        QUANDO collection loop roda
        ENTÃO deve ler tags a cada 1 segundo
        """
        pytest.skip("Teste de timing - implementar com asyncio.sleep mock")
    
    @pytest.mark.asyncio
    async def test_should_send_data_to_backend_when_connected(self):
        """
        DADO backend conectado
        QUANDO tags são lidas
        ENTÃO dados devem ser enviados ao backend
        """
        from gateway.app.services.device_manager import DeviceManager
        
        mock_backend = AsyncMock()
        mock_backend.is_connected = True
        mock_backend.send_timeseries_batch.return_value = True
        
        mock_buffer = MagicMock()
        
        manager = DeviceManager(mock_backend, mock_buffer)
        
        # Simular leitura de tags
        mock_handler = AsyncMock()
        tag_values = [
            {"tag_id": "TAG01", "value": 42.0, "timestamp": datetime.utcnow()}
        ]
        mock_handler.read_tags.return_value = tag_values
        manager.devices["test-device"] = mock_handler
        
        # Simular um ciclo de collection
        tags = [{"tag_id": "TAG01", "address": "ns=2;s=TAG01"}]
        
        # Note: Este teste precisa ser adaptado para testar o loop real
        pytest.skip("Precisa adaptar para testar loop completo")
    
    @pytest.mark.asyncio
    async def test_should_buffer_data_when_backend_disconnected(self):
        """
        DADO backend desconectado
        QUANDO tags são lidas
        ENTÃO dados devem ser armazenados no buffer
        """
        from gateway.app.services.device_manager import DeviceManager
        
        mock_backend = MagicMock()
        mock_backend.is_connected = False  # Backend offline
        
        mock_buffer = MagicMock()
        mock_buffer.add.return_value = None
        
        manager = DeviceManager(mock_backend, mock_buffer)
        
        # Este teste verificaria se buffer.add() é chamado
        pytest.skip("Implementar teste de buffering")


class TestDeviceManagerRemoveDevice:
    """Testes de remoção de devices"""
    
    @pytest.mark.asyncio
    async def test_should_remove_device_and_disconnect(self):
        """
        DADO device conectado
        QUANDO remove_device() é chamado
        ENTÃO device deve ser desconectado e removido
        """
        from gateway.app.services.device_manager import DeviceManager
        
        manager = DeviceManager(MagicMock(), MagicMock())
        
        # Mock device
        mock_handler = AsyncMock()
        manager.devices["test-device"] = mock_handler
        
        result = await manager.remove_device("test-device")
        
        assert result is True
        assert "test-device" not in manager.devices
        mock_handler.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_stop_collection_before_removing(self):
        """
        DADO device com collection ativa
        QUANDO remove_device() é chamado
        ENTÃO collection deve ser parada antes de remover
        """
        pytest.skip("Implementar parada de collection")


class TestDeviceManagerHealthCheck:
    """Testes de health check"""
    
    @pytest.mark.asyncio
    async def test_should_check_all_devices_health(self):
        """
        DADO múltiplos devices
        QUANDO health_check_all() é chamado
        ENTÃO deve retornar status de cada device
        """
        from gateway.app.services.device_manager import DeviceManager
        
        manager = DeviceManager(MagicMock(), MagicMock())
        
        # Mock devices
        mock_device1 = AsyncMock()
        mock_device1.health_check.return_value = True
        
        mock_device2 = AsyncMock()
        mock_device2.health_check.return_value = False
        
        manager.devices["device-1"] = mock_device1
        manager.devices["device-2"] = mock_device2
        
        results = await manager.health_check_all()
        
        assert results["device-1"] is True
        assert results["device-2"] is False


class TestDeviceManagerOPCUADiscovery:
    """Testes de descoberta OPC-UA"""
    
    @pytest.mark.asyncio
    async def test_should_discover_opcua_tags(self):
        """
        DADO endpoint OPC-UA
        QUANDO discover_opcua_tags() é chamado
        ENTÃO deve retornar lista de tags disponíveis
        """
        from gateway.app.services.device_manager import DeviceManager
        
        manager = DeviceManager(MagicMock(), MagicMock())
        
        with patch('gateway.app.services.opcua_browser.OPCUABrowser') as mock_browser_class:
            mock_browser = AsyncMock()
            mock_browser.connect.return_value = True
            mock_browser.discover_all_tags.return_value = [
                {"tag_name": "TAG01", "node_id": "ns=2;i=1"},
                {"tag_name": "TAG02", "node_id": "ns=2;i=2"},
            ]
            mock_browser_class.return_value = mock_browser
            
            result = await manager.discover_opcua_tags(
                endpoint="opc.tcp://localhost:4840",
                namespace_index=2
            )
            
            assert "tags" in result
            assert len(result["tags"]) == 2
            mock_browser.connect.assert_called_once()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def device_manager():
    """Fixture que cria DeviceManager"""
    from gateway.app.services.device_manager import DeviceManager
    
    mock_backend = AsyncMock()
    mock_backend.is_connected = True
    
    mock_buffer = MagicMock()
    
    manager = DeviceManager(mock_backend, mock_buffer)
    return manager


@pytest.fixture
def sample_device_config():
    """Fixture com configuração de device de exemplo"""
    return {
        "device_id": "test-opcua-1",
        "protocol": "opc_ua",
        "config": {
            "endpoint": "opc.tcp://localhost:4840/optiflow/terminal",
            "namespace_index": 2,
            "timeout": 10
        },
        "tags": [
            {
                "tag_id": "tag-001",
                "tag_name": "CORR01.RPM.PV",
                "address": "ns=2;s=CORR01.RPM.PV",
                "data_type": "Double",
                "scan_rate": 1000
            }
        ]
    }


# ============================================================================
# INSTRUÇÕES PARA GREEN PHASE
# ============================================================================

"""
PRÓXIMOS PASSOS (GREEN PHASE):

1. Verificar gateway/app/services/device_manager.py
2. Executar testes: pytest gateway/tests/unit/test_device_manager.py -v
3. Implementar funcionalidades faltantes
4. Commit: test: adiciona testes para DeviceManager (RED)
5. Commit: feat: implementa funcionalidades DeviceManager (GREEN)
6. Medir cobertura: pytest --cov=gateway.app.services.device_manager
7. Target: ≥80% coverage
"""
