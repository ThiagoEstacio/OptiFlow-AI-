#!/bin/bash
# Setup Ollama with Qwen2.5:7B model for OptiFlow AI
# Optimized for RTX 4060 (8GB VRAM) + 16GB RAM

set -e

echo "============================================"
echo "OptiFlow AI - Ollama Model Setup"
echo "Model: Qwen2.5:7B (Best for your hardware)"
echo "============================================"

# Check if Ollama container is running
if ! docker ps | grep -q optiflow-ollama; then
    echo "Starting Ollama container..."
    docker-compose up -d ollama
    sleep 10
fi

# Check GPU availability
echo ""
echo "Checking GPU availability..."
if docker exec optiflow-ollama nvidia-smi &>/dev/null; then
    echo "✅ GPU detected!"
    docker exec optiflow-ollama nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
else
    echo "⚠️  GPU not detected. Running on CPU (slower)"
    echo "   Make sure nvidia-docker2 is installed"
fi

# Pull the model
echo ""
echo "Downloading Qwen2.5:7B model..."
echo "This may take 10-20 minutes depending on your connection..."
docker exec optiflow-ollama ollama pull qwen2.5:7b

# Verify model is loaded
echo ""
echo "Verifying model installation..."
if docker exec optiflow-ollama ollama list | grep -q "qwen2.5:7b"; then
    echo "✅ Qwen2.5:7B installed successfully!"
else
    echo "❌ Model installation failed"
    exit 1
fi

# Test the model
echo ""
echo "Testing model with a simple prompt..."
RESPONSE=$(docker exec optiflow-ollama ollama run qwen2.5:7b "Say 'OptiFlow AI Ready' in exactly 3 words" 2>/dev/null | head -1)
echo "Model response: $RESPONSE"

# Show model info
echo ""
echo "============================================"
echo "Model Information:"
echo "============================================"
docker exec optiflow-ollama ollama show qwen2.5:7b --modelfile 2>/dev/null | head -20

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "The Qwen2.5:7B model is now ready for use."
echo ""
echo "Key advantages over Llama 3.1:8B:"
echo "  - Better instruction following"
echo "  - Superior reasoning capabilities"
echo "  - Optimized for multilingual (Portuguese/English)"
echo "  - Better at structured outputs (JSON)"
echo ""
echo "To test the AI Assistant:"
echo "  1. Open http://localhost:3000/dashboards/builder"
echo "  2. Click on the AI Assistant button"
echo "  3. Try: 'Crie um gráfico de temperatura'"
echo ""
echo "Memory usage estimate:"
echo "  - Model size: ~4.7GB"
echo "  - RAM usage: ~8-10GB"
echo "  - VRAM usage: ~6GB"
echo ""
