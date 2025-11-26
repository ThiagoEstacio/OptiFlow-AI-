# Guia de Resolução de Problemas - Tags do Gateway

Se o dashboard builder ainda está mostrando tags do simulador ao invés das tags do gateway, siga os passos abaixo para garantir que o sistema esteja configurado corretamente.

## Passo 1: Verifique se o Simulador está Desabilitado no Frontend

A modificação que eu fiz em `frontend/src/App.tsx` desabilita o simulador de dados que roda no frontend. Isso previne que dados do simulador sejam enviados para o backend.

**Ação:**
1.  Pare o servidor de desenvolvimento do frontend (se estiver rodando).
2.  Reinicie o servidor de desenvolvimento do frontend.
    ```bash
    npm run dev
    ```
    ou
    ```bash
    yarn dev
    ```
3.  Acesse o dashboard builder e verifique se as tags corretas são exibidas.

## Passo 2: Configure as Tags do Gateway no Banco de Dados

Se o Passo 1 não resolveu o problema, é possível que o banco de dados não tenha as tags do gateway configuradas. O script `configure_gateway_tags.py` foi criado para popular o banco de dados com as tags corretas.

**Ação:**
1.  Certifique-se de que o banco de dados PostgreSQL está rodando.
2.  Execute o script de configuração de tags:
    ```bash
    python3 configure_gateway_tags.py
    ```
3.  O script irá conectar no banco de dados e adicionar as tags do gateway. Verifique o output do script para garantir que não houve erros.

## Passo 3: Reinicie os Serviços do Backend e Gateway

Depois de garantir que as tags do gateway estão no banco de dados, é uma boa prática reiniciar o backend e o gateway para que eles carreguem a nova configuração.

**Ação:**
1.  Reinicie o servidor do backend.
2.  Reinicie o serviço do OPC UA Gateway. Se você estiver usando Docker, o comando é:
    ```bash
    docker compose restart gateway backend
    ```

## Passo 4: Verificação Final

Após completar os passos acima, o sistema deve estar em um estado consistente.

1.  Acesse o dashboard builder no frontend e verifique se as tags do gateway são exibidas.
2.  Se as tags ainda não aparecerem, verifique os logs do backend e do gateway para possíveis erros de conexão com o banco de dados ou com o servidor OPC UA.

Se o problema persistir após seguir este guia, pode haver um problema mais profundo na configuração do backend ou do gateway que precisa ser investigado.
