# ✅ Sistema de Backup Automatizado - IMPLEMENTADO

## Status: CONCLUÍDO

Data: $(date +%Y-%m-%d)

---

## 🎯 Objetivo

Implementar sistema robusto de backup automatizado para todos os dados críticos do OptiFlow AI, com criptografia, retenção configurável e verificação de integridade.

---

## ✅ Componentes Implementados

### 1. Script de Backup Principal
**Arquivo**: `scripts/backup-production.sh`

**Funcionalidades**:
- ✅ **PostgreSQL**: pg_dumpall completo + compressão gzip
- ✅ **InfluxDB**: Backup de time series com influx backup
- ✅ **Redis**: SAVE + cópia do dump.rdb
- ✅ **Application Data**: Backup de volumes (logs, ML models, configs)
- ✅ **Criptografia**: GPG AES256 para todos os backups
- ✅ **Upload Cloud**: Suporte para AWS S3 (opcional)
- ✅ **Retenção**: Limpeza automática de backups antigos
- ✅ **Logging**: Log detalhado de todas operações
- ✅ **Notificações**: Webhook para notificar conclusão

**Variáveis de Ambiente**:
```bash
BACKUP_KEEP_DAYS=7              # Retenção (default: 7 dias)
BACKUP_ENABLED=true             # Enable/disable backups
GPG_PASSPHRASE=secure_phrase    # Senha para criptografia
AWS_ACCESS_KEY_ID=...           # AWS credentials (opcional)
AWS_SECRET_ACCESS_KEY=...
S3_BACKUP_BUCKET=...
BACKUP_NOTIFICATION_WEBHOOK=... # Slack/Discord webhook
```

### 2. Script de Restore
**Arquivo**: `scripts/restore-from-backup.sh`

**Funcionalidades**:
- ✅ **Seleção Interativa**: Lista backups disponíveis
- ✅ **Confirmação**: Requer confirmação antes de restore
- ✅ **Descriptografia**: Automática com GPG
- ✅ **Restore Completo**: PostgreSQL, InfluxDB, Redis, App Data
- ✅ **Service Management**: Para/inicia serviços automaticamente
- ✅ **Verificação**: Checklist pós-restore
- ✅ **Cleanup**: Remove arquivos temporários

### 3. Verificação de Saúde
**Arquivo**: `scripts/check-backup-health.sh`

**Verificações**:
- ✅ **Timestamp**: Alerta se último backup > 26h
- ✅ **Tamanho**: Alerta se backup < 10MB (suspeito)
- ✅ **Conteúdo**: Verifica presença de arquivos críticos
- ✅ **Logs**: Detecta erros em logs recentes
- ✅ **Disk Space**: Alerta se > 80% usado
- ✅ **Retenção**: Verifica quantidade de backups
- ✅ **Alertas**: Email e webhook para falhas

### 4. Automação com Cron
**Arquivo**: `scripts/backup-cron`

**Schedule**:
```cron
# Backup diário às 2:00 AM
0 2 * * * root /path/to/backup-production.sh

# Health check às 5:00 AM
0 5 * * * root /path/to/check-backup-health.sh

# Limpeza de logs às 4:00 AM
0 4 * * * root find /backups -name "*.log" -mtime +30 -delete
```

---

## 📋 Estrutura de Backups

```
/backups/
├── 20240115_020000/           # Backup completo
│   ├── postgresql_20240115_020000.sql.gz.gpg
│   ├── influxdb_20240115_020000.tar.gz.gpg
│   ├── redis_20240115_020000.rdb.gz.gpg
│   └── app_data_20240115_020000.tar.gz.gpg
├── 20240116_020000/
│   └── ...
├── backup.log                 # Log de operações
└── cron.log                   # Log do cron

S3 (opcional):
s3://optiflow-backups/optiflow/
└── 20240115_020000/
    └── [encrypted backups]
```

---

## 🚀 Como Usar

### Setup Inicial

1. **Configurar Variáveis de Ambiente**

Adicione ao `.env.production`:
```bash
# Backup Configuration
BACKUP_KEEP_DAYS=7
BACKUP_ENABLED=true
GPG_PASSPHRASE=your-secure-passphrase-here

# S3 (opcional)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BACKUP_BUCKET=optiflow-backups

# Alertas
BACKUP_NOTIFICATION_WEBHOOK=https://hooks.slack.com/...
ALERT_EMAIL=ops@optiflow.com
```

2. **Criar Diretório de Backups**

```bash
sudo mkdir -p /backups
sudo chown -R $(whoami):$(whoami) /backups
```

3. **Instalar Dependências**

```bash
# GPG para criptografia
sudo apt-get install gnupg

# AWS CLI (se usar S3)
sudo apt-get install awscli
aws configure
```

4. **Configurar Cron**

```bash
# Adicionar ao crontab do sistema
sudo cp scripts/backup-cron /etc/cron.d/optiflow-backup
sudo chmod 644 /etc/cron.d/optiflow-backup

# Ou adicionar manualmente
sudo crontab -e
# Cole o conteúdo de backup-cron
```

### Backup Manual

```bash
cd /home/thiestacio/OptiFlow-AI-
./scripts/backup-production.sh
```

**Saída esperada**:
```
============================================
Starting OptiFlow AI Production Backup
============================================
Created backup directory: /backups/20240115_143022
✅ PostgreSQL backup completed: 45M
✅ InfluxDB backup completed: 120M
✅ Redis backup completed: 8M
✅ Application data backup completed: 15M
✅ Encrypted: postgresql_20240115_143022.sql.gz.gpg
✅ Encrypted: influxdb_20240115_143022.tar.gz.gpg
✅ Encrypted: redis_20240115_143022.rdb.gz.gpg
✅ Encrypted: app_data_20240115_143022.tar.gz.gpg
✅ Backups uploaded to S3: optiflow-backups
✅ Cleanup completed. Current backups: 7
============================================
Backup Summary
Total Size: 188M
Status: ✅ COMPLETED
============================================
```

### Restore de Backup

```bash
cd /home/thiestacio/OptiFlow-AI-
./scripts/restore-from-backup.sh
```

**Interação**:
```
Available backups:
  [0] 20240115_020000 (188M)
  [1] 20240114_020000 (185M)
  [2] 20240113_020000 (182M)

Select backup to restore [0-2]: 0

⚠️  WARNING: This will REPLACE current data with backup from 20240115_020000
Are you sure? Type 'YES' to confirm: YES

[Processo de restore...]

✅ RESTORE COMPLETED
```

### Verificar Saúde dos Backups

```bash
./scripts/check-backup-health.sh
```

**Saída (sucesso)**:
```
Checking last backup time...
✅ Last backup: 20240115_020000 (4h ago)
Checking backup size...
✅ Backup size: 188MB
Checking backup contents...
✅ Found: postgresql_*.sql.gz.gpg
✅ Found: influxdb_*.tar.gz.gpg
✅ No errors in recent logs
✅ Disk usage: 45%
✅ Backup count: 7

✅ BACKUP HEALTH: OK
```

**Saída (falha)**:
```
❌ BACKUP HEALTH: ISSUES DETECTED

  ❌ Last backup is 30h old (expected <26h)
  ⚠️  Disk usage at 85% (warning)

Please investigate backup system immediately!
[Alert sent to Slack and email]
```

---

## 🔐 Segurança

### Criptografia
- **Algoritmo**: GPG com AES256
- **Backups**: Todos criptografados antes de armazenamento
- **Senha**: Armazenada em .env.production (chmod 600)
- **Descriptografia**: Apenas durante restore

### Permissões
```bash
# Diretório de backups
chmod 700 /backups

# Scripts
chmod 700 scripts/backup-production.sh
chmod 700 scripts/restore-from-backup.sh
chmod 700 scripts/check-backup-health.sh

# Arquivo de ambiente
chmod 600 .env.production
```

### Armazenamento Cloud (S3)
- **Encryption**: Server-side encryption (SSE)
- **Storage Class**: STANDARD_IA (lower cost for infrequent access)
- **Versioning**: Recomendado habilitar no bucket S3
- **Lifecycle**: Configurar para mover para Glacier após 30 dias

---

## 🧪 Testes

### Teste de Backup

```bash
# 1. Executar backup
./scripts/backup-production.sh

# 2. Verificar arquivos criados
ls -lh /backups/$(date +%Y%m%d_*)

# 3. Testar descriptografia
cd /backups/$(date +%Y%m%d_*)
gpg --decrypt postgresql_*.sql.gz.gpg > /tmp/test.sql.gz
gunzip /tmp/test.sql.gz
head -50 /tmp/test.sql  # Deve mostrar SQL válido
rm /tmp/test.sql
```

### Teste de Restore (Ambiente de Teste!)

⚠️ **NUNCA execute em produção sem backup prévio!**

```bash
# 1. Criar ambiente de teste
docker-compose -f docker-compose.test.yml up -d

# 2. Executar restore
./scripts/restore-from-backup.sh

# 3. Verificar dados
docker-compose -f docker-compose.test.yml exec backend \
  python -c "from app.db.session import SessionLocal; print(SessionLocal().execute('SELECT COUNT(*) FROM users').scalar())"

# 4. Limpar ambiente de teste
docker-compose -f docker-compose.test.yml down -v
```

### Teste de Health Check

```bash
# Deve passar
./scripts/check-backup-health.sh
echo $?  # 0 = success

# Simular falha (apagar último backup)
mv /backups/$(ls /backups | grep 20 | tail -1) /tmp/
./scripts/check-backup-health.sh
echo $?  # 1 = failure

# Restaurar backup
mv /tmp/20* /backups/
```

---

## 📊 Monitoramento

### Métricas de Backup

Adicionar ao Prometheus:

```yaml
# monitoring/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'backup-health'
    static_configs:
      - targets: ['localhost:9999']
    metrics_path: '/metrics'
```

Criar exporter (opcional):
```bash
# scripts/backup-metrics-exporter.sh
# Expõe métricas em formato Prometheus
```

### Alertas no Grafana

```yaml
# monitoring/grafana/dashboards/backup-dashboard.json
{
  "alert": {
    "name": "Backup Failed",
    "conditions": [
      {
        "query": "backup_last_success_timestamp < now() - 26h",
        "severity": "critical"
      }
    ]
  }
}
```

---

## 🔧 Troubleshooting

### Backup Falha com "Permission Denied"

```bash
# Verificar permissões
ls -l /backups
sudo chown -R $(whoami):$(whoami) /backups
sudo chmod 700 /backups
```

### Backup Muito Lento

```bash
# Verificar IO do disco
iostat -x 1

# Otimizar PostgreSQL backup
# Usar pg_dump paralelo em vez de pg_dumpall
pg_dump -j 4 -Fd -f /backups/pgdump_$(date +%Y%m%d)

# Otimizar compressão
# Usar pigz (parallel gzip) em vez de gzip
```

### Descriptografia Falha

```bash
# Verificar passphrase
echo $GPG_PASSPHRASE

# Tentar descriptografia manual
gpg --decrypt backup.sql.gz.gpg

# Re-criptografar com nova senha
gpg --decrypt backup.sql.gz.gpg | gpg --symmetric --cipher-algo AES256 -o backup_new.gpg
```

### S3 Upload Falha

```bash
# Verificar credenciais AWS
aws s3 ls s3://optiflow-backups/

# Verificar permissões IAM
# Necessário: s3:PutObject, s3:ListBucket

# Testar upload manual
aws s3 cp /backups/latest/ s3://optiflow-backups/test/ --recursive
```

---

## 📈 Performance

### Tempo de Execução (Estimado)

| Componente       | Tamanho | Tempo   |
|------------------|---------|---------|
| PostgreSQL       | 50MB    | 30s     |
| InfluxDB         | 150MB   | 2min    |
| Redis            | 10MB    | 10s     |
| App Data         | 20MB    | 20s     |
| Compressão       | -       | 1min    |
| Criptografia     | -       | 30s     |
| Upload S3        | 230MB   | 3min    |
| **TOTAL**        | **230MB** | **~8min** |

### Otimizações Futuras

1. **Backup Incremental**: Reduzir tempo e espaço
2. **Compressão Paralela**: pigz em vez de gzip
3. **Deduplica**: restic ou borg backup
4. **Snapshot**: Usar LVM snapshots para consistência
5. **Streaming**: Upload durante backup (não esperar finalizar)

---

## ✅ Checklist de Validação

- [x] Script de backup criado e testado
- [x] Script de restore criado e testado
- [x] Health check implementado
- [x] Cron job configurado
- [x] Criptografia GPG funcionando
- [x] Upload S3 opcional configurado
- [x] Retenção de backups funcionando
- [x] Logs detalhados implementados
- [x] Alertas de falha configurados
- [x] Documentação completa
- [x] Permissões seguras definidas
- [x] Testes de backup executados
- [x] Testes de restore executados

---

## 🚀 Próximos Passos

✅ **CONCLUÍDO**: Sistema de Backup Automatizado

🔄 **EM ANDAMENTO**:
- Item 3: Configurar alertas críticos no Alertmanager

📋 **MELHORIAS FUTURAS**:
- Implementar backup incremental
- Configurar backup offsite (segundo datacenter)
- Adicionar testes de restore automáticos (semanal)
- Integrar com sistema de monitoring (métricas Prometheus)
- Implementar backup validation (checksum verification)

---

**Status Final**: ✅ **PRODUÇÃO-READY**

Sistema completo de backup automatizado implementado com criptografia, retenção configurável, health checks e suporte para cloud storage. Pronto para operação em ambiente de produção.
