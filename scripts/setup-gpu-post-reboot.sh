#!/bin/bash
# Post-reboot GPU verification and setup script

echo "========================================="
echo "GPU ACCELERATION - POST-REBOOT SETUP"
echo "========================================="
echo ""

# Step 1: Verify new driver
echo "📋 Step 1: Verificando driver NVIDIA 580..."
nvidia-smi | head -3
if [ $? -eq 0 ]; then
    echo "✅ Driver 580 ativo!"
else
    echo "❌ Erro ao acessar GPU"
    exit 1
fi
echo ""

# Step 2: Add CUDA to PATH
echo "📋 Step 2: Configurando CUDA PATH..."
if ! grep -q "cuda-12.2/bin" ~/.bashrc; then
    echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
    echo "✅ Variáveis adicionadas ao ~/.bashrc"
else
    echo "✅ Variáveis já configuradas"
fi
export PATH=/usr/local/cuda-12.2/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH
echo ""

# Step 3: Verify CUDA
echo "📋 Step 3: Verificando CUDA..."
nvcc --version | grep "release"
if [ $? -eq 0 ]; then
    echo "✅ CUDA Toolkit detectado!"
else
    echo "⚠️ nvcc não encontrado (normal se não instalou toolkit completo)"
fi
echo ""

# Step 4: Install CuPy in host Python
echo "📋 Step 4: Instalando CuPy no Python do host..."
pip3 install cupy-cuda12x==12.3.0 --user
echo ""

# Step 5: Test CuPy
echo "📋 Step 5: Testando CuPy..."
python3 -c "import cupy as cp; device = cp.cuda.Device(); print(f'✅ GPU: {device.name}'); print(f'Compute: {device.compute_capability}'); mem = cp.cuda.runtime.memGetInfo(); print(f'VRAM: {mem[1]/(1024**2):.0f} MB')"
if [ $? -eq 0 ]; then
    echo "✅ CuPy funcionando no host!"
else
    echo "❌ Erro ao testar CuPy"
    exit 1
fi
echo ""

# Step 6: Build GPU-enabled Docker image
echo "📋 Step 6: Building Docker image com suporte GPU..."
cd /home/thiestacio/OptiFlow-AI-
sudo docker compose build backend --no-cache
if [ $? -eq 0 ]; then
    echo "✅ Imagem backend com GPU construída!"
else
    echo "❌ Erro ao buildar imagem"
    exit 1
fi
echo ""

# Step 7: Restart backend container
echo "📋 Step 7: Reiniciando backend com GPU..."
sudo docker compose up -d --force-recreate backend
sleep 5
echo ""

# Step 8: Verify GPU in container
echo "📋 Step 8: Verificando GPU no container..."
sudo docker exec optiflow-backend nvidia-smi | head -3
sudo docker exec optiflow-backend python -c "import cupy as cp; print('✅ Container GPU:', cp.cuda.Device().name)"
if [ $? -eq 0 ]; then
    echo "✅ GPU acessível do container!"
else
    echo "❌ GPU não acessível do container"
    exit 1
fi
echo ""

# Step 9: Check backend logs
echo "📋 Step 9: Verificando logs do backend..."
sudo docker compose logs backend | grep -E "GPU|🚀" | tail -5
echo ""

echo "========================================="
echo "✅ SETUP COMPLETO!"
echo "========================================="
echo ""
echo "GPU está pronta para acelerar a simulação DEM!"
echo ""
echo "Próximos passos:"
echo "1. Acesse http://localhost:3000/simulator"
echo "2. Inicie simulação: POST /api/v1/simulator/start"
echo "3. Monitor GPU: watch -n 0.5 nvidia-smi"
echo "4. Aumente partículas para testar aceleração"
echo ""
