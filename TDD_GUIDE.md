# Test-Driven Development (TDD) Guide - OptiFlow AI

## 📋 Índice
1. [Visão Geral do TDD](#visão-geral-do-tdd)
2. [Estrutura de Testes](#estrutura-de-testes)
3. [Processo TDD](#processo-tdd)
4. [Convenções de Commit](#convenções-de-commit)
5. [Ferramentas e Configuração](#ferramentas-e-configuração)
6. [Exemplos Práticos](#exemplos-práticos)

---

## Visão Geral do TDD

### Ciclo Red-Green-Refactor

```
🔴 RED    → Escrever teste que falha
🟢 GREEN  → Implementar código mínimo para passar
🔵 REFACTOR → Melhorar código mantendo testes passando
```

### Benefícios no OptiFlow AI

- ✅ Confiabilidade em sistemas críticos (SCADA/industrial)
- ✅ Documentação viva através de testes
- ✅ Refatoração segura
- ✅ Detecção precoce de bugs
- ✅ Design melhor e modular

---

## Estrutura de Testes

### Backend (Python/FastAPI)

```
backend/
├── tests/
│   ├── unit/              # Testes unitários (funções isoladas)
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── integration/       # Testes de integração (componentes juntos)
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   └── test_kafka_influxdb.py
│   ├── e2e/              # End-to-end (sistema completo)
│   │   ├── test_data_pipeline.py
│   │   └── test_user_workflows.py
│   ├── performance/       # Testes de carga/stress
│   │   ├── test_load.py
│   │   └── test_stress.py
│   └── fixtures/          # Dados de teste reutilizáveis
│       ├── __init__.py
│       └── sample_data.py
```

### Frontend (React/TypeScript)

```
frontend/
├── src/
│   ├── __tests__/
│   │   ├── unit/         # Componentes isolados
│   │   ├── integration/  # Fluxos de componentes
│   │   └── e2e/          # Testes Cypress/Playwright
│   └── components/
│       └── Button/
│           ├── Button.tsx
│           ├── Button.test.tsx
│           └── Button.stories.tsx
```

### Gateway (Python)

```
gateway/
├── tests/
│   ├── unit/
│   │   ├── test_opcua_browser.py
│   │   ├── test_device_manager.py
│   │   └── test_buffer.py
│   ├── integration/
│   │   ├── test_opcua_connection.py
│   │   └── test_backend_sync.py
│   └── fixtures/
│       └── mock_opcua_server.py
```

---

## Processo TDD

### 1. Criar Issue/Task

```bash
# Exemplo: Nova feature de descoberta automática de tags
Feature: Auto-discovery de tags OPC-UA

User Story:
Como operador do sistema
Quero que o gateway descubra tags automaticamente
Para não precisar configurar manualmente cada tag

Acceptance Criteria:
- [ ] Gateway conecta ao servidor OPC-UA
- [ ] Descobre todos os namespaces disponíveis
- [ ] Lista todos os tags em cada namespace
- [ ] Filtra tags por padrão (opcional)
- [ ] Salva configuração no banco de dados
```

### 2. Escrever Testes (RED 🔴)

```python
# tests/unit/test_opcua_browser.py

import pytest
from gateway.services.opcua_browser import OPCUABrowser

class TestOPCUABrowser:
    """Testes para o browser OPC-UA"""
    
    @pytest.mark.asyncio
    async def test_connect_to_server_success(self):
        """Deve conectar ao servidor OPC-UA com sucesso"""
        browser = OPCUABrowser("opc.tcp://localhost:4840")
        
        connected = await browser.connect()
        
        assert connected is True
        assert browser.is_connected is True
    
    @pytest.mark.asyncio
    async def test_discover_namespaces(self):
        """Deve listar todos os namespaces disponíveis"""
        browser = OPCUABrowser("opc.tcp://localhost:4840")
        await browser.connect()
        
        namespaces = await browser.get_namespaces()
        
        assert len(namespaces) > 0
        assert any(ns['uri'] == 'http://optiflow.com/terminal' for ns in namespaces)
    
    @pytest.mark.asyncio
    async def test_discover_tags_in_namespace(self):
        """Deve descobrir tags em namespace específico"""
        browser = OPCUABrowser("opc.tcp://localhost:4840")
        await browser.connect()
        
        tags = await browser.discover_tags(namespace_index=2)
        
        assert len(tags) > 0
        assert all('tag_name' in tag for tag in tags)
        assert all('node_id' in tag for tag in tags)
```

### 3. Executar Testes (devem FALHAR)

```bash
# Backend
cd backend
pytest tests/unit/test_opcua_browser.py -v

# Resultado esperado: FAILED ❌
```

### 4. Implementar Código Mínimo (GREEN 🟢)

```python
# gateway/services/opcua_browser.py

from asyncua import Client
from typing import List, Dict, Optional

class OPCUABrowser:
    """Browser para descoberta de tags OPC-UA"""
    
    def __init__(self, endpoint: str, timeout: int = 10):
        self.endpoint = endpoint
        self.timeout = timeout
        self.client = Client(url=endpoint, timeout=timeout)
        self.is_connected = False
    
    async def connect(self) -> bool:
        """Conecta ao servidor OPC-UA"""
        try:
            await self.client.connect()
            self.is_connected = True
            return True
        except Exception as e:
            self.is_connected = False
            return False
    
    async def get_namespaces(self) -> List[Dict[str, any]]:
        """Retorna lista de namespaces"""
        if not self.is_connected:
            raise RuntimeError("Not connected")
        
        namespaces = await self.client.get_namespace_array()
        return [
            {"index": idx, "uri": ns}
            for idx, ns in enumerate(namespaces)
        ]
    
    async def discover_tags(self, namespace_index: int) -> List[Dict[str, str]]:
        """Descobre tags em namespace específico"""
        # Implementação básica para passar teste
        tags = []
        # ... código de descoberta ...
        return tags
```

### 5. Executar Testes Novamente

```bash
pytest tests/unit/test_opcua_browser.py -v

# Resultado esperado: PASSED ✅
```

### 6. Refatorar (REFACTOR 🔵)

```python
# Melhorar código mantendo testes passando
# - Extrair métodos complexos
# - Adicionar type hints completos
# - Melhorar tratamento de erros
# - Adicionar logging
# - Otimizar performance
```

### 7. Commit com Convenção

```bash
git add tests/unit/test_opcua_browser.py
git add gateway/services/opcua_browser.py
git commit -m "test: adiciona testes para OPCUABrowser

- Testa conexão ao servidor OPC-UA
- Testa descoberta de namespaces
- Testa descoberta de tags

Refs: #123"

# Em seguida, após implementação passar:
git commit -m "feat: implementa auto-discovery de tags OPC-UA

- Adiciona OPCUABrowser service
- Descobre namespaces automaticamente
- Lista todos os tags por namespace
- Suporta filtragem opcional

Tests: ✅ 3/3 passed
Closes: #123"
```

---

## Convenções de Commit

### Formato Padrão (Conventional Commits)

```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos de Commit

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `feat` | Nova funcionalidade | `feat: adiciona endpoint de descoberta OPC-UA` |
| `fix` | Correção de bug | `fix: corrige await em propriedade is_connected` |
| `test` | Adiciona/modifica testes | `test: adiciona testes unitários para gateway` |
| `refactor` | Refatoração sem mudar comportamento | `refactor: extrai lógica de descoberta para método` |
| `docs` | Documentação | `docs: atualiza README com guia TDD` |
| `style` | Formatação, linting | `style: formata código com black` |
| `perf` | Melhoria de performance | `perf: otimiza query de tags no PostgreSQL` |
| `chore` | Tarefas de manutenção | `chore: atualiza dependências` |
| `ci` | CI/CD | `ci: adiciona GitHub Actions para testes` |

### Exemplos de Commits TDD

```bash
# 1. RED: Escrever teste que falha
git commit -m "test: adiciona teste para filtragem de tags por equipamento

Teste falha conforme esperado (TDD Red phase)

Refs: #456"

# 2. GREEN: Implementar funcionalidade
git commit -m "feat: implementa filtragem de tags por equipamento

- Adiciona parâmetro equipment_filter
- Filtra tags por prefixo
- Retorna apenas tags correspondentes

Tests: ✅ 5/5 passed (TDD Green phase)
Refs: #456"

# 3. REFACTOR: Melhorar código
git commit -m "refactor: otimiza filtragem de tags usando regex

- Substitui loops por list comprehension
- Adiciona cache para padrões compilados
- Performance: 3x mais rápido

Tests: ✅ 5/5 passed (mantidos)
Refs: #456"
```

---

## Ferramentas e Configuração

### Backend (Python)

#### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --asyncio-mode=auto
markers =
    unit: Testes unitários
    integration: Testes de integração
    e2e: Testes end-to-end
    slow: Testes lentos
```

#### Instalação

```bash
cd backend
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

#### Executar Testes

```bash
# Todos os testes
pytest

# Apenas unitários
pytest -m unit

# Com cobertura
pytest --cov=app --cov-report=html

# Específico
pytest tests/unit/test_opcua_browser.py -v

# Watch mode (com pytest-watch)
ptw
```

### Frontend (TypeScript/React)

#### jest.config.js

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.test.ts?(x)'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
```

#### Instalação

```bash
cd frontend
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
npm install --save-dev @testing-library/user-event vitest
```

#### Executar Testes

```bash
# Todos os testes
npm test

# Watch mode
npm test -- --watch

# Cobertura
npm test -- --coverage
```

### CI/CD com GitHub Actions

#### .github/workflows/tests.yml

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
```

---

## Exemplos Práticos

### Exemplo 1: Nova Feature - Alarme de Temperatura

#### 1. Escrever Teste (RED 🔴)

```python
# tests/unit/test_alarm_manager.py

import pytest
from app.services.alarm_manager import AlarmManager
from app.models.alarm import AlarmSeverity

class TestAlarmManager:
    def test_create_temperature_alarm_when_threshold_exceeded(self):
        """Deve criar alarme quando temperatura exceder limite"""
        manager = AlarmManager()
        
        # Simular leitura de temperatura alta
        alarm = manager.check_temperature(
            equipment_id="CORR01",
            temperature=85.0,
            threshold=80.0
        )
        
        assert alarm is not None
        assert alarm.severity == AlarmSeverity.HIGH
        assert "temperatura" in alarm.message.lower()
        assert alarm.equipment_id == "CORR01"
```

#### 2. Executar (deve FALHAR)

```bash
pytest tests/unit/test_alarm_manager.py::TestAlarmManager::test_create_temperature_alarm_when_threshold_exceeded
# FAILED ❌
```

#### 3. Implementar (GREEN 🟢)

```python
# app/services/alarm_manager.py

from typing import Optional
from app.models.alarm import Alarm, AlarmSeverity
from datetime import datetime

class AlarmManager:
    def check_temperature(
        self,
        equipment_id: str,
        temperature: float,
        threshold: float
    ) -> Optional[Alarm]:
        """Verifica temperatura e cria alarme se necessário"""
        
        if temperature <= threshold:
            return None
        
        return Alarm(
            id=self._generate_id(),
            equipment_id=equipment_id,
            severity=AlarmSeverity.HIGH,
            message=f"Temperatura alta: {temperature}°C (limite: {threshold}°C)",
            timestamp=datetime.utcnow(),
            acknowledged=False
        )
```

#### 4. Commit

```bash
git add tests/unit/test_alarm_manager.py
git commit -m "test: adiciona teste para alarme de temperatura

TDD Red phase: teste falha conforme esperado"

git add app/services/alarm_manager.py
git commit -m "feat: implementa verificação de alarme de temperatura

- Cria alarme quando temperatura excede threshold
- Severity HIGH para temperaturas críticas
- Mensagem descritiva com valores

Tests: ✅ 1/1 passed
TDD Green phase"
```

### Exemplo 2: Bug Fix - Conexão WebSocket

#### 1. Escrever Teste de Regressão (RED 🔴)

```python
# tests/integration/test_websocket.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestWebSocketConnection:
    def test_websocket_accepts_valid_connection(self):
        """Deve aceitar conexão WebSocket válida"""
        client = TestClient(app)
        
        with client.websocket_connect("/api/v1/ws/tags") as websocket:
            # Deve conectar sem erro 1006
            websocket.send_json({"action": "subscribe", "tags": ["TAG01"]})
            data = websocket.receive_json()
            
            assert data["status"] == "subscribed"
```

#### 2. Confirmar Falha

```bash
pytest tests/integration/test_websocket.py
# FAILED: Connection closed with code 1006 ❌
```

#### 3. Corrigir Bug (GREEN 🟢)

```python
# app/api/v1/endpoints/websocket.py

@router.websocket("/ws/tags")
async def websocket_tags_endpoint(
    websocket: WebSocket,
    token: str = Query(...)  # FIX: Adicionar autenticação
):
    try:
        # Validar token antes de aceitar conexão
        user = await get_current_user_ws(token)
        
        await websocket.accept()
        # ... resto do código ...
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)  # FIX: Código correto
```

#### 4. Commit

```bash
git commit -m "fix: corrige erro 1006 em conexão WebSocket

- Adiciona autenticação antes de aceitar conexão
- Usa código de fechamento correto (1000)
- Adiciona logging de erros

Fixes: #789
Tests: ✅ 1/1 passed"
```

---

## Checklist TDD para Pull Requests

```markdown
## Checklist TDD

- [ ] Testes escritos ANTES da implementação (Red phase)
- [ ] Todos os testes passam (Green phase)
- [ ] Código refatorado mantendo testes passando (Refactor phase)
- [ ] Cobertura de testes ≥ 80%
- [ ] Testes unitários para lógica de negócio
- [ ] Testes de integração para APIs/Database
- [ ] Testes E2E para fluxos críticos
- [ ] Commits seguem Conventional Commits
- [ ] CI/CD passou sem erros
- [ ] Documentação atualizada
```

---

## Métricas de Qualidade

### Cobertura de Código

```bash
# Backend
pytest --cov=app --cov-report=term-missing
# Target: ≥ 80%

# Frontend
npm test -- --coverage
# Target: ≥ 80%
```

### Qualidade de Testes

- **Assertividade**: Cada teste deve ter ≥ 1 assertion clara
- **Isolamento**: Testes não devem depender uns dos outros
- **Rapidez**: Testes unitários < 100ms cada
- **Clareza**: Nome do teste descreve exatamente o comportamento

### Exemplo de Bom Teste

```python
def test_gateway_reconnects_after_network_failure_with_exponential_backoff(self):
    """
    DADO um gateway conectado ao backend
    QUANDO a conexão de rede falha
    ENTÃO o gateway deve:
      - Detectar a falha
      - Tentar reconectar com backoff exponencial
      - Restaurar operação normal após reconexão
    """
    # Arrange
    gateway = Gateway()
    gateway.connect()
    
    # Act
    simulate_network_failure()
    time.sleep(5)  # Aguardar tentativas de reconexão
    
    # Assert
    assert gateway.is_connected is True
    assert gateway.retry_count > 0
    assert gateway.backoff_seconds == 8  # 2^3
```

---

## Recursos Adicionais

### Links Úteis

- [pytest documentation](https://docs.pytest.org/)
- [Testing Library](https://testing-library.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [TDD by Example (Kent Beck)](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)

### Comandos Rápidos

```bash
# Executar testes modificados
pytest --lf

# Executar testes falhos
pytest --failed-first

# Modo verboso com output
pytest -vv -s

# Parar no primeiro erro
pytest -x

# Executar em paralelo
pytest -n auto
```

---

**Mantido por**: Equipe OptiFlow AI  
**Última atualização**: 10 de novembro de 2025  
**Versão**: 1.0.0
