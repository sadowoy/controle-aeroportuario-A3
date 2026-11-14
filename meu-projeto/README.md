# Sistema de Controle de Pátio e Decolagem Aeroportuário (SCPDA)

Projeto prático de Banco de Dados Relacional implementado em **Oracle Database 21c Express Edition (XE)** via Docker, com automação de inicialização, regras de negócio em PL/SQL, otimização por índices e aplicação cliente em Python.

---

## Estrutura do Repositório

```text
meu-projeto/
├── app/
│   ├── main.py                  # Aplicação cliente Python (SELECT, Procedure e Trigger)
│   └── requirements.txt         # Dependências Python (driver oracledb)
├── DER/
│   └── controle-patio.puml      # Diagrama Entidade-Relacionamento (PlantUML)
├── docker/
│   └── oracle-init.sh           # Script de inicialização automática do schema
├── oracle/
│   ├── 01_ddl.sql               # Criação das 7 tabelas, PKs, FKs e CHECKs
│   ├── 02_inserts.sql           # Carga de dados iniciais para testes
│   ├── 03_consultas.sql         # 10 consultas analíticas (JOIN, GROUP BY, HAVING, Subqueries)
│   └── 04_indices.sql           # Índices B-Tree em chaves estrangeiras
├── performance/
│   └── analise_indices.md       # Relatório comparativo EXPLAIN PLAN (Antes vs. Depois)
├── procedures/
│   └── oracle_procedures.sql    # Procedures e Trigger de validação de MTOW
├── docker-compose.yml           # Orquestração do container Oracle XE 21c
└── README.md
```

---

## Modelo de Dados e Regras de Negócio

O esquema relacional é composto por 7 entidades principais:
- **`MODELO_AERONAVE`** e **`AERONAVE`**: Cadastro de modelos, prefixos únicos e Peso Máximo de Decolagem (`mtow_kg`).
- **`PISTA`** e **`VOO`**: Alocação de pistas, horários previstos, peso total da operação e status do voo.
- **`TRIPULANTE`** e **`ESCALA_VOO`**: Controle associativo (`N:N`) de tripulação escalada e horas computadas por voo.
- **`ORDEM_MANUTENCAO`**: Registro de ocorrências técnicas por nível de severidade (`1` a `5`).

### Rotinas PL/SQL (`procedures/oracle_procedures.sql`)
1. **`registrar_manutencao(p_aeronave, p_severidade)`**: Abre uma ordem de manutenção e, caso a severidade seja crítica (`1`), cancela automaticamente os voos agendados da aeronave.
2. **`cancelar_voo(p_voo_id)`**: Valida a existência e o status do voo (bloqueando cancelamento de voos já concluídos), altera o status para `CANCELADO` e remove as escalas vinculadas.
3. **`trg_valida_peso_voo` (Trigger `BEFORE INSERT OR UPDATE`)**: Impede o agendamento ou alteração de voos cujo `peso_total_kg` ultrapasse o `mtow_kg` do modelo da aeronave (`ORA-20002 / AER-002`).

---

## Como Executar o Projeto

### 1. Subir o Banco de Dados Oracle (Docker)
Na pasta raiz do projeto (`meu-projeto/`), inicie o container. O script `docker/oracle-init.sh` criará automaticamente as tabelas, dados iniciais, consultas, procedures, trigger e índices no Pluggable Database `XEPDB1`:

```bash
docker compose up -d --wait
```

**Credenciais do Ambiente:**
- **Host / Porta:** `localhost:1521`
- **Service Name:** `XEPDB1`
- **Usuário / Senha:** `usuario_lab` / `senha_lab`

*(Opcional) Para acessar o terminal SQL*Plus diretamente no container:*
```bash
docker exec -it bd_oracle sqlplus "usuario_lab/senha_lab@XEPDB1"
```

---

### 2. Executar a Aplicação Cliente (Python)
Ainda na pasta raiz (`meu-projeto/`), instale o driver oficial `oracledb` (modo *Thin*, sem necessidade de Oracle Instant Client) e execute a demonstração:

```bash
pip install -r app/requirements.txt
python app/main.py
```

A aplicação executa três validações em sequência:
1. Consulta analítica de modelos com MTOW superior a 75.000 kg e contagem de voos agendados.
2. Chamada da procedure `registrar_manutencao` seguida de `rollback` para preservar o estado base.
3. Tentativa controlada de inserção de voo com excesso de peso, capturando o bloqueio `ORA-20002` da trigger `trg_valida_peso_voo`.

---

## Análise de Performance
Os planos de execução (`DBMS_XPLAN.DISPLAY`) antes e depois da criação dos índices `idx_voo_aeronave`, `idx_voo_pista` e `idx_manutencao_aeronave` estão documentados em [`performance/analise_indices.md`](performance/analise_indices.md), demonstrando a substituição de `TABLE ACCESS FULL` por `INDEX RANGE SCAN` e redução de custo de até **66,7%**.