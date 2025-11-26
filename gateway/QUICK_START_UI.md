# Gateway UI - Início Rápido

## Acesso Rápido

1. **Abra o navegador** e acesse:
   ```
   http://localhost:8080/
   ```

2. **Você verá**:
   - Dashboard com estatísticas dos adaptadores
   - Cards com cada adaptador configurado
   - Botões para gerenciar adaptadores

---

## Adicionar Seu Primeiro Dispositivo (3 minutos)

### Exemplo: Adicionar PLC OPC UA

1. Clique em **"+ Adicionar Adaptador"**

2. Preencha:
   ```
   Nome: Meu PLC Teste
   Protocolo: OPC UA
   Host: 192.168.1.10  (IP do seu PLC)
   Porta: 4840
   Taxa de Scan: 1000ms
   ✓ Habilitado
   ```

3. Clique **"Criar Adaptador"**

4. No card criado, clique **"Testar"** para verificar conexão

5. Se conectou com sucesso, clique **"Descobrir Tags"**

6. Veja a lista de tags encontrados

7. Pronto! O adaptador já está coletando e enviando dados para o Kafka

---

## Ações Rápidas

### Ver Status de Todos Adaptadores
- Basta abrir `http://localhost:8080/`
- Dashboard mostra: Total, Conectados, Rodando, Tags

### Parar Coleta Temporariamente
- Clique **"Parar"** no card do adaptador
- Dados param de ser coletados
- Configuração permanece salva

### Reiniciar Coleta
- Clique **"Iniciar"** no card do adaptador
- Coleta recomeça imediatamente

### Remover Dispositivo
- Clique **"Excluir"** no card
- Confirme a exclusão
- Adaptador é removido

---

## Protocolos Disponíveis

Ao adicionar adaptador, escolha:

| Protocolo | Porta Padrão | Uso Típico |
|-----------|--------------|------------|
| **OPC UA** | 4840 | PLCs modernos (Siemens, Beckhoff) |
| **Modbus TCP** | 502 | PLCs antigos, instrumentação |
| **MQTT** | 1883 | Sensores IoT, wireless |
| **EtherNet/IP** | 44818 | Allen Bradley, Rockwell |
| **Siemens S7** | 102 | PLCs Siemens S7 |

---

## Documentação Completa

- **Guia de Uso Detalhado**: [UI_USAGE_GUIDE.md](UI_USAGE_GUIDE.md)
- **API REST**: [GATEWAY_API_DOCUMENTATION.md](GATEWAY_API_DOCUMENTATION.md)
- **Swagger UI**: http://localhost:8080/docs

---

## Troubleshooting Rápido

**Interface não abre?**
```bash
docker ps | grep gateway  # Verificar se está rodando
docker compose restart gateway  # Reiniciar
```

**Adaptador não conecta?**
1. Verificar IP e porta corretos
2. Testar ping: `ping 192.168.1.10`
3. Clicar "Testar" para diagnóstico
4. Verificar firewall do PLC

**Descoberta não encontra tags?**
1. Verificar adaptador está "Conectado"
2. Para OPC UA: verificar namespace
3. Checar permissões no dispositivo

---

## Próximos Passos

Após configurar adaptadores:

1. ✅ Verificar dados chegando no Kafka
2. ✅ Acessar dashboard principal: `http://localhost:3000`
3. ✅ Configurar alertas e limites
4. ✅ Criar visualizações personalizadas

---

**Dica**: A interface atualiza automaticamente a cada 10 segundos. Deixe aberta para monitoramento em tempo real!
