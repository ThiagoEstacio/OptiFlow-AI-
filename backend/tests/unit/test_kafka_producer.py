"""
Testes Unitários - Kafka Producer Service
==========================================

Testa o serviço de produção de mensagens Kafka seguindo TDD

Autor: OptiFlow AI Team
Data: 2025-11-10
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json


# ============================================================================
# RED PHASE: Testes que definem o comportamento esperado
# ============================================================================

class TestKafkaProducerInitialization:
    """Testes de inicialização do producer"""
    
    @pytest.mark.asyncio
    async def test_should_initialize_kafka_producer_with_config(self):
        """
        DADO configuração válida de Kafka
        QUANDO KafkaProducer é inicializado
        ENTÃO deve criar producer com configurações corretas
        """
        from app.services.kafka_producer import KafkaProducerService
        
        config = {
            "bootstrap_servers": "localhost:9092",
            "client_id": "optiflow-backend",
            "compression_type": "lz4"
        }
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService(config)
            await service.start()
            
            # Verificar que producer foi criado com config correta
            mock_producer_class.assert_called_once()
            call_kwargs = mock_producer_class.call_args[1]
            assert call_kwargs['bootstrap_servers'] == config['bootstrap_servers']
            assert call_kwargs['client_id'] == config['client_id']
            assert call_kwargs['compression_type'] == config['compression_type']
    
    @pytest.mark.asyncio
    async def test_should_start_producer_successfully(self):
        """
        DADO um producer configurado
        QUANDO start() é chamado
        ENTÃO deve iniciar producer sem erros
        """
        from app.services.kafka_producer import KafkaProducerService
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            
            mock_producer.start.assert_called_once()
            assert service.is_running is True


class TestKafkaProducerSendMessage:
    """Testes de envio de mensagens"""
    
    @pytest.mark.asyncio
    async def test_should_send_message_to_topic(self):
        """
        DADO um producer ativo
        QUANDO envio mensagem para tópico
        ENTÃO mensagem deve ser enviada com sucesso
        """
        from app.services.kafka_producer import KafkaProducerService
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            
            message = {"tag_name": "TAG01", "value": 42.0}
            await service.send("raw_tags", message)
            
            mock_producer.send.assert_called_once()
            call_args = mock_producer.send.call_args
            assert call_args[0][0] == "raw_tags"
            
            # Verificar que mensagem foi serializada
            sent_data = call_args[1]['value']
            assert isinstance(sent_data, bytes)
    
    @pytest.mark.asyncio
    async def test_should_send_message_with_key(self):
        """
        DADO um producer ativo
        QUANDO envio mensagem com key
        ENTÃO mensagem deve incluir key para particionamento
        """
        from app.services.kafka_producer import KafkaProducerService
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            
            await service.send("raw_tags", {"value": 42.0}, key="TAG01")
            
            call_args = mock_producer.send.call_args
            assert call_args[1]['key'] is not None
    
    @pytest.mark.asyncio
    async def test_should_serialize_datetime_in_message(self):
        """
        DADO mensagem com datetime
        QUANDO envio para Kafka
        ENTÃO datetime deve ser serializado para ISO format
        """
        from app.services.kafka_producer import KafkaProducerService
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            
            now = datetime.utcnow()
            message = {"timestamp": now, "value": 42.0}
            
            await service.send("raw_tags", message)
            
            # Verificar serialização
            call_args = mock_producer.send.call_args
            sent_bytes = call_args[1]['value']
            sent_data = json.loads(sent_bytes.decode('utf-8'))
            
            assert isinstance(sent_data['timestamp'], str)
            assert 'T' in sent_data['timestamp']  # ISO format


class TestKafkaProducerBatch:
    """Testes de envio em batch"""
    
    @pytest.mark.asyncio
    async def test_should_send_batch_of_messages(self):
        """
        DADO lista de mensagens
        QUANDO envio em batch
        ENTÃO todas mensagens devem ser enviadas
        """
        from app.services.kafka_producer import KafkaProducerService
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            
            messages = [
                {"tag": "TAG01", "value": 1.0},
                {"tag": "TAG02", "value": 2.0},
                {"tag": "TAG03", "value": 3.0},
            ]
            
            await service.send_batch("raw_tags", messages)
            
            # Verificar que send foi chamado 3 vezes
            assert mock_producer.send.call_count == 3


class TestKafkaProducerErrorHandling:
    """Testes de tratamento de erros"""
    
    @pytest.mark.asyncio
    async def test_should_handle_connection_error(self):
        """
        DADO producer com falha de conexão
        QUANDO tento enviar mensagem
        ENTÃO deve retornar erro apropriado
        """
        from app.services.kafka_producer import KafkaProducerService
        from aiokafka.errors import KafkaConnectionError
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer.send.side_effect = KafkaConnectionError("Connection failed")
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            
            with pytest.raises(KafkaConnectionError):
                await service.send("raw_tags", {"value": 42.0})
    
    @pytest.mark.asyncio
    async def test_should_retry_on_timeout(self):
        """
        DADO producer com timeout temporário
        QUANDO envio mensagem
        ENTÃO deve fazer retry automático
        """
        pytest.skip("Implementar retry logic")


class TestKafkaProducerShutdown:
    """Testes de shutdown"""
    
    @pytest.mark.asyncio
    async def test_should_flush_pending_messages_on_stop(self):
        """
        DADO producer com mensagens pendentes
        QUANDO stop() é chamado
        ENTÃO deve fazer flush antes de fechar
        """
        from app.services.kafka_producer import KafkaProducerService
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            await service.stop()
            
            mock_producer.flush.assert_called_once()
            mock_producer.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_mark_as_not_running_after_stop(self):
        """
        DADO producer rodando
        QUANDO stop() é chamado
        ENTÃO is_running deve ser False
        """
        from app.services.kafka_producer import KafkaProducerService
        
        with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            service = KafkaProducerService({})
            await service.start()
            assert service.is_running is True
            
            await service.stop()
            assert service.is_running is False


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def kafka_producer_service():
    """Fixture que cria e inicia KafkaProducerService mockado"""
    with patch('app.services.kafka_producer.AIOKafkaProducer') as mock_producer_class:
        mock_producer = AsyncMock()
        mock_producer_class.return_value = mock_producer
        
        from app.services.kafka_producer import KafkaProducerService
        service = KafkaProducerService({})
        await service.start()
        
        yield service
        
        await service.stop()


@pytest.fixture
def sample_tag_message():
    """Fixture com mensagem de tag de exemplo"""
    return {
        "tag_name": "CORR01.RPM.PV",
        "value": 1750.5,
        "quality": "GOOD",
        "timestamp": datetime.utcnow(),
        "device_id": "gateway-1"
    }


# ============================================================================
# TESTES COM FIXTURES
# ============================================================================

class TestKafkaProducerWithFixtures:
    """Testes usando fixtures reutilizáveis"""
    
    @pytest.mark.asyncio
    async def test_send_tag_message(self, kafka_producer_service, sample_tag_message):
        """Deve enviar mensagem de tag formatada"""
        await kafka_producer_service.send("raw_tags", sample_tag_message)
        
        # Verificações básicas
        assert kafka_producer_service.is_running is True


# ============================================================================
# INSTRUÇÕES PARA GREEN PHASE
# ============================================================================

"""
PRÓXIMOS PASSOS (GREEN PHASE):

1. Criar app/services/kafka_producer.py com implementação
2. Executar testes: pytest tests/unit/test_kafka_producer.py -v
3. Implementar funcionalidades até testes passarem
4. Commit: test: adiciona testes para KafkaProducerService (RED)
5. Commit: feat: implementa KafkaProducerService (GREEN)
6. Refatorar se necessário
7. Commit: refactor: otimiza KafkaProducerService (REFACTOR)
"""
