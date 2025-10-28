# SmartPort Backend Tests

Suite de testes críticos para o backend SmartPort.

## Estrutura

```
tests/
├── conftest.py              # Fixtures e configuração global
├── test_auth.py             # Testes de autenticação
├── test_sites.py            # Testes CRUD de Sites
├── test_devices.py          # Testes CRUD de Devices
├── test_tags.py             # Testes CRUD de Tags
├── test_alarms.py           # Testes de Alarmes
└── test_rate_limiting.py    # Testes de Rate Limiting
```

## Cobertura dos Testes

### 1. Autenticação (test_auth.py)
- ✅ Login com credenciais corretas
- ✅ Login com senha incorreta
- ✅ Login com usuário inexistente
- ✅ Validação de campos obrigatórios
- ✅ Acesso a endpoints protegidos sem token
- ✅ Acesso a endpoints protegidos com token válido
- ✅ Acesso a endpoints protegidos com token inválido
- ✅ Rate limiting no login (5/minuto)

### 2. Sites (test_sites.py)
- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Validação de site_type (smartport, smartmine, smartsteel)
- ✅ Validação de coordenadas (latitude, longitude)
- ✅ Filtro por organization_id
- ✅ Tratamento de erros 404

### 3. Devices (test_devices.py)
- ✅ CRUD completo
- ✅ Validação de protocolo (modbus_tcp, s7, ethernetip, etc)
- ✅ Validação de porta (1-65535)
- ✅ Configurações específicas por protocolo (S7, Ethernet/IP)
- ✅ Filtro por site_id
- ✅ Tratamento de erros 404

### 4. Tags (test_tags.py)
- ✅ CRUD completo
- ✅ Validação de data_type (BOOL, INT, FLOAT, etc)
- ✅ Suporte a diferentes tipos de dados
- ✅ Obter último valor da tag
- ✅ Filtro por device_id
- ✅ Categorização de tags
- ✅ Configuração de escala e limites

### 5. Alarms (test_alarms.py)
- ✅ CRUD de definições de alarme
- ✅ Validação de severity (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Reconhecimento de alarmes ativos
- ✅ Validação de status (não pode reconhecer alarme não-ativo)
- ✅ Obter eventos de alarme
- ✅ Filtro por severity

### 6. Rate Limiting (test_rate_limiting.py)
- ✅ Auth: 5 requisições/minuto
- ✅ Users: 10 requisições/minuto
- ✅ Organizations: 20 requisições/minuto
- ✅ Sites: 30 requisições/minuto
- ✅ Devices: 30 requisições/minuto
- ✅ Tags: 50 requisições/minuto
- ✅ Verificar independência entre endpoints
- ✅ Headers de rate limit nos responses

## Executar Testes

### Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

### Executar Todos os Testes

```bash
pytest
```

### Executar com Verbosidade

```bash
pytest -v
```

### Executar Arquivo Específico

```bash
pytest tests/test_auth.py
```

### Executar Teste Específico

```bash
pytest tests/test_auth.py::test_login_success
```

### Executar com Coverage

```bash
pytest --cov=app --cov-report=html
```

O relatório HTML será gerado em `htmlcov/index.html`.

### Executar Testes Paralelos (mais rápido)

```bash
pip install pytest-xdist
pytest -n auto
```

## Fixtures Disponíveis

Definidos em `conftest.py`:

- `test_engine`: Engine SQLite em memória
- `test_db`: Sessão de banco de dados para testes
- `client`: Cliente HTTP AsyncClient
- `test_organization`: Organização de teste
- `test_user`: Usuário de teste
- `test_token`: Token JWT de teste
- `auth_headers`: Headers de autenticação prontos
- `test_site`: Site de teste
- `test_device`: Device de teste
- `test_tag`: Tag de teste

## Estratégia de Testes

### Banco de Dados
- SQLite em memória (`:memory:`) para testes rápidos
- Tabelas criadas/destruídas automaticamente
- Isolamento total entre testes

### Rate Limiting
- Testes verificam que os limites estão sendo aplicados
- Importante: Limites são POR MINUTO, testes podem demorar

### Autenticação
- Todos os testes usam fixtures com autenticação
- Testes de auth verificam comportamento sem token

## Comandos Úteis

```bash
# Listar todos os testes
pytest --collect-only

# Executar apenas testes marcados
pytest -m asyncio

# Parar no primeiro erro
pytest -x

# Ver output completo (print statements)
pytest -s

# Atualizar snapshots (se usando)
pytest --snapshot-update
```

## Notas Importantes

1. **Rate Limiting**: Testes de rate limiting podem demorar ~1 minuto cada
2. **Ordem**: Testes são independentes e podem rodar em qualquer ordem
3. **Limpeza**: Banco é limpo automaticamente entre testes
4. **Async**: Todos os testes usam `@pytest.mark.asyncio`

## Próximos Passos

Para aumentar a cobertura:

1. Testes de integração com InfluxDB
2. Testes de integração com Redis
3. Testes de WebSocket (tempo real)
4. Testes de Dashboard endpoints
5. Testes de Analytics/ML endpoints
6. Testes de performance com locust
7. Testes E2E com Playwright

## Troubleshooting

### Erro: "Event loop is closed"
```bash
pip install --upgrade pytest-asyncio
```

### Erro: "No module named aiosqlite"
```bash
pip install aiosqlite
```

### Testes lentos
Use pytest-xdist para paralelização:
```bash
pip install pytest-xdist
pytest -n auto
```
