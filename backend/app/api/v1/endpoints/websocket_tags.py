"""
WebSocket endpoint for real-time tag streaming via Kafka

This endpoint creates a WebSocket connection that streams tag updates
from Kafka to connected frontend clients in real-time.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
import asyncio

try:
    from aiokafka import AIOKafkaConsumer
    from aiokafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/tags")
async def websocket_tags_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming tag updates from Kafka

    Usage from frontend:
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/tags');
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('Tag update:', message.data);
        };

    Message format:
        {
            "type": "tag_update",
            "data": {
                "tag_id": "TAG001",
                "name": "Temperature_1",
                "value": 25.5,
                "quality": "good",
                "timestamp": "2025-11-05T15:30:00Z",
                "source": "simulator"
            }
        }
    """
    await websocket.accept()
    client_id = f"{websocket.client.host}:{websocket.client.port}"

    if not KAFKA_AVAILABLE:
        await websocket.send_json({
            "type": "error",
            "message": "Kafka streaming not available - aiokafka not installed"
        })
        await websocket.close()
        return

    logger.info(f"✅ WebSocket client connected: {client_id}")

    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "message": "Connected to Kafka tag stream",
        "client_id": client_id
    })

    consumer = None

    try:
        # Kafka broker address
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')

        # Create Kafka consumer for this WebSocket connection
        consumer = AIOKafkaConsumer(
            'raw_tags',
            'simulator_state',  # Also subscribe to full simulator state
            bootstrap_servers=bootstrap_servers,
            group_id=f'frontend_{client_id}',
            auto_offset_reset='latest',  # Only read new messages
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        await consumer.start()
        logger.info(f"Kafka consumer started for client {client_id}")

        # Stream messages from Kafka to WebSocket
        async for message in consumer:
            try:
                # Determine message type based on topic
                if message.topic == 'raw_tags':
                    msg_type = 'tag_update'
                elif message.topic == 'simulator_state':
                    msg_type = 'simulator_state'
                else:
                    msg_type = 'unknown'

                # Send to frontend via WebSocket
                await websocket.send_json({
                    "type": msg_type,
                    "data": message.value,
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset
                })

            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")

    except KafkaError as e:
        logger.error(f"Kafka error for client {client_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Kafka connection error: {str(e)}"
            })
        except:
            pass

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Internal error: {str(e)}"
            })
        except:
            pass

    finally:
        # Cleanup
        if consumer:
            try:
                await consumer.stop()
                logger.info(f"Kafka consumer stopped for client {client_id}")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")

        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/simulator")
async def websocket_simulator_stream(websocket: WebSocket):
    """
    WebSocket endpoint specifically for simulator state updates

    This is optimized for the simulator page, providing full state updates
    """
    await websocket.accept()
    client_id = f"{websocket.client.host}:{websocket.client.port}"

    if not KAFKA_AVAILABLE:
        await websocket.send_json({
            "type": "error",
            "message": "Kafka streaming not available"
        })
        await websocket.close()
        return

    logger.info(f"✅ Simulator WebSocket connected: {client_id}")

    consumer = None

    try:
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')

        consumer = AIOKafkaConsumer(
            'simulator_state',
            bootstrap_servers=bootstrap_servers,
            group_id=f'simulator_frontend_{client_id}',
            auto_offset_reset='latest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        await consumer.start()

        # Stream simulator state updates
        async for message in consumer:
            try:
                await websocket.send_json({
                    "type": "state_update",
                    "data": message.value
                })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in simulator stream: {e}")
                continue

    except WebSocketDisconnect:
        logger.info(f"Simulator WebSocket disconnected: {client_id}")

    finally:
        if consumer:
            await consumer.stop()
        try:
            await websocket.close()
        except:
            pass
