# GPU Acceleration Setup Guide

## 🚀 Sua GPU

**NVIDIA GeForce RTX 4060 Laptop**
- VRAM: 8 GB
- CUDA Cores: ~3072
- Compute Capability: 8.9
- Driver: 570.195.03

## 📊 Performance Esperado

| Modo | Partículas | FPS | Uso |
|------|-----------|-----|-----|
| CPU (NumPy) | 500-1000 | 60 | ⚠️ Alta CPU |
| GPU (CuPy) | 5000-8000 | 60 | ✅ GPU ~30% |

**Ganho esperado: 10-50x mais rápido**

## 🛠️ Instalação

### Opção 1: Instalação Local (Recomendado para desenvolvimento)

```bash
# 1. Ativar ambiente Python
cd backend
source venv/bin/activate  # ou conda activate seu_env

# 2. Instalar CuPy para CUDA 12.x
pip install cupy-cuda12x==12.3.0

# 3. Verificar instalação
python -c "import cupy as cp; print(f'CuPy OK: {cp.cuda.Device().name}')"

# 4. Reiniciar backend
uvicorn app.main:app --reload
```

### Opção 2: Docker com GPU (Para produção)

1. **Instalar NVIDIA Container Toolkit:**
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. **Atualizar docker-compose.yml:**
```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

3. **Rebuild container:**
```bash
# Adicionar cupy ao Dockerfile
RUN pip install cupy-cuda12x==12.3.0

# Rebuild
sudo docker compose build backend
sudo docker compose up -d backend
```

## ✅ Verificação

```bash
# Ver logs do backend
sudo docker compose logs backend | grep "GPU"

# Deve mostrar:
# 🚀 GPU ACCELERATION ENABLED - CuPy detected
# GPU: NVIDIA GeForce RTX 4060 Laptop GPU
# VRAM: 8188 MB
```

## 📈 Monitoramento

```bash
# Terminal 1: Monitor GPU
watch -n 0.5 nvidia-smi

# Terminal 2: Backend logs
sudo docker compose logs -f backend

# Terminal 3: Simulador
curl -X POST http://localhost:8000/api/v1/simulator/start
```

## 🎯 Benefícios Implementados

1. **Fallback Automático**: Se GPU não disponível, usa CPU sem erros
2. **Zero Code Changes**: DEM funciona igual, apenas mais rápido
3. **Memory Efficient**: Transfere apenas dados necessários
4. **Monitoring**: Logs mostram uso de GPU/CPU

## 🔧 Troubleshooting

### GPU não detectada
```bash
# Verificar driver NVIDIA
nvidia-smi

# Verificar CUDA
nvcc --version

# Reinstalar driver se necessário
sudo apt install nvidia-driver-570
```

### CuPy import error
```bash
# Verificar versão CUDA
python -c "import cupy; cupy.show_config()"

# Reinstalar versão correta
pip uninstall cupy-cuda12x
pip install cupy-cuda12x==12.3.0
```

### Docker não vê GPU
```bash
# Testar acesso GPU no Docker
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Se falhar, reinstalar nvidia-container-toolkit
```

## 🚦 Status Atual

- ✅ Código GPU-ready implementado
- ✅ Fallback automático funcionando  
- ⏳ CuPy não instalado (opcional)
- ⏳ Docker GPU não configurado (opcional)

**Sistema funciona AGORA mesmo sem GPU instalada!**

Para ativar GPU: Siga "Instalação" acima.

