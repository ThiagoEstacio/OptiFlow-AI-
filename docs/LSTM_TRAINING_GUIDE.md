# Guia de Treinamento LSTM - OptiFlow AI

## 📋 Status Atual

✅ **Isolation Forest**: Treinado com sucesso
- Dataset: 1.3M pontos
- F1-Score: 0.0778 (precisa melhoria)
- Arquivo: `/app/models/isolation_forest.joblib`
- Timestamp: 2025-11-11 03:00:47

⏳ **LSTM Autoencoder**: Aguardando treinamento
- Arquitetura: 65,418 parâmetros
- Dataset: 1.3M pontos em sequências de 60
- Tempo estimado: **30-60 minutos no CPU**
- Arquivo esperado: `/app/models/lstm_autoencoder.h5`

---

## 🚀 Como Executar o Treinamento LSTM

### Opção 1: Executar e Acompanhar em Tempo Real

```bash
cd /home/thiestacio/OptiFlow-AI-

# Executar treinamento (vai ocupar o terminal)
docker compose exec backend python scripts/train_anomaly_models.py
```

**Vantagens**: Você vê o progresso em tempo real (epochs, loss)  
**Desvantagens**: Terminal fica bloqueado por 30-60 minutos

---

### Opção 2: Executar em Background e Monitorar

```bash
cd /home/thiestacio/OptiFlow-AI-

# Iniciar treinamento em background
docker compose exec backend bash -c "python scripts/train_anomaly_models.py > /tmp/training_lstm.log 2>&1 &"

# Monitorar progresso
docker compose exec backend tail -f /tmp/training_lstm.log

# Ou verificar de tempos em tempos
docker compose exec backend tail -100 /tmp/training_lstm.log
```

**Vantagens**: Terminal livre para outros comandos  
**Desvantagens**: Precisa checar log manualmente

---

### Opção 3: Usar Script de Monitoramento Automático

```bash
cd /home/thiestacio/OptiFlow-AI-

# Em um terminal, iniciar treinamento
docker compose exec backend python scripts/train_anomaly_models.py &

# Em outro terminal, monitorar automaticamente
./scripts/wait_for_lstm.sh
```

Este script:
- ✅ Verifica a cada 2 minutos se LSTM completou
- ✅ Notifica quando terminar
- ✅ Mostra métricas finais automaticamente

---

## 📊 Verificar Status Rapidamente

```bash
# Verificar status atual dos modelos
./scripts/check_ml_status.sh
```

Mostra:
- ✅ Quais modelos estão treinados
- ⏳ Quais estão em progresso
- 📊 Métricas disponíveis
- 🔄 Se processo está rodando

---

## 🎯 O Que Esperar

### Durante o Treinamento

Você verá output como:

```
============================================================
🧠 TRAINING LSTM AUTOENCODER
============================================================
⏳ Creating sequences (length=60)...
📊 Training sequences shape: (1034628, 60, 10)

🏗️  Model Architecture:
Model: "sequential"
...
Total params: 65418 (255.54 KB)

⏳ Training LSTM Autoencoder...
Epoch 1/50
32333/32333 [==============================] - 45s 1ms/step - loss: 0.0234
Epoch 2/50
32333/32333 [==============================] - 44s 1ms/step - loss: 0.0156
...
```

### Progresso Esperado

- **Epoch 1-10**: ~7-10 minutos (loss vai de ~0.02 para ~0.01)
- **Epoch 11-30**: ~20-30 minutos (loss estabiliza em ~0.005-0.008)
- **Epoch 31-50**: ~20-30 minutos (fine-tuning, loss < 0.005)

**Tempo total**: 30-60 minutos dependendo do CPU

---

## ✅ Quando Completar

### Arquivos Gerados

```bash
/app/models/
├── isolation_forest.joblib     # ✅ Já existe
├── scaler.joblib                # ✅ Já existe
├── lstm_autoencoder.h5          # ⏳ Será criado
└── metrics.json                 # ⏳ Será criado
```

### Verificar Métricas

```bash
# Ver métricas comparativas
docker compose exec backend cat /app/models/metrics.json | jq

# Deve mostrar algo como:
{
  "isolation_forest": {
    "precision": 0.0457,
    "recall": 0.2620,
    "f1_score": 0.0778
  },
  "lstm_autoencoder": {
    "precision": 0.65,     # Esperado > 0.6
    "recall": 0.70,        # Esperado > 0.6
    "f1_score": 0.67       # Esperado > 0.6
  }
}
```

### Testar API com LSTM

```bash
# Endpoint deve funcionar automaticamente
curl "http://localhost:8000/api/v1/analytics/anomalies?model_type=lstm&limit=100" | jq
```

---

## 🐛 Troubleshooting

### Processo Não Inicia

```bash
# Verificar se backend está rodando
docker compose ps backend

# Se não estiver, iniciar
docker compose up -d backend
```

### Processo Trava ou Para

```bash
# Verificar logs do container
docker compose logs backend --tail 100

# Verificar recursos
docker stats optiflow-backend
```

### Memória Insuficiente

Se o treinamento falhar por falta de memória:

```bash
# Editar docker-compose.yml e aumentar limite de memória do backend
# Ou executar com dataset menor (editar SAMPLE_MAX no script)
```

---

## 🎯 Próximos Passos Após LSTM Completar

1. **Comparar Performance**
   ```bash
   # F1-Score esperado: LSTM (0.65-0.75) vs Isolation Forest (0.0778)
   ```

2. **Testar API com Ambos Modelos**
   ```bash
   # Isolation Forest
   curl "http://localhost:8000/api/v1/analytics/anomalies?model_type=isolation_forest"
   
   # LSTM (quando estiver pronto)
   curl "http://localhost:8000/api/v1/analytics/anomalies?model_type=lstm"
   ```

3. **Criar Frontend de Visualização**
   - Página `/analytics/anomalies`
   - Gráficos de scatter plot
   - Comparação entre modelos
   - Filtros interativos

4. **Atualizar Agent para Usar LSTM**
   - Se LSTM tiver performance melhor, configurar como modelo padrão
   - Agent vai automaticamente usar nas próximas consultas

---

## 📝 Notas Importantes

⚠️ **Reiniciar Backend**: Se reiniciar o backend durante treinamento, o processo será interrompido e precisa recomeçar

⚠️ **Tempo de CPU**: 30-60 minutos é normal sem GPU. Com GPU seria ~5-10 minutos

✅ **Modelos Salvos**: Uma vez treinados, os modelos são persistentes (salvos em volume Docker)

✅ **API Funcionando**: Isolation Forest já está funcionando e pode ser usado enquanto LSTM treina

---

## 🔗 Referências

- Script de treinamento: `scripts/train_anomaly_models.py`
- Script de monitoramento: `scripts/wait_for_lstm.sh`
- Script de status: `scripts/check_ml_status.sh`
- API endpoints: `backend/app/api/v1/endpoints/analytics.py`
- Documentação ML: `docs/ML_API_GUIDE.md`

---

**Data**: 2025-11-11  
**Status**: Aguardando execução de treinamento LSTM  
**Próxima Task**: Frontend de visualização de anomalias
