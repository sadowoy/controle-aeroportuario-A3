# Relatório de Performance — Índices e Planos de Execução (Oracle XE 21c)

## 1. Ambiente e Metodologia
- **SGBD:** Oracle Database 21c Express Edition (`21.3.0.0.0`) — Pluggable Database `XEPDB1`
- **Schema:** `usuario_lab`
- **Ferramentas de Diagnóstico:** `EXPLAIN PLAN FOR`, `DBMS_XPLAN.DISPLAY` e `SET TIMING ON` no SQL*Plus
- **Objetivo:** Eliminar varreduras completas de tabela (`TABLE ACCESS FULL`) em consultas com `JOIN` e filtros sobre chaves estrangeiras frequentemente acessadas.

### Índices Criados (`oracle/04_indices.sql`)
```sql
CREATE INDEX idx_voo_aeronave ON voo(aeronave_id);
CREATE INDEX idx_voo_pista ON voo(pista_id);
CREATE INDEX idx_manutencao_aeronave ON ordem_manutencao(aeronave_id);
```

---

## 2. Resumo Comparativo (Antes vs. Depois)

| Cenário / FK Avaliada | Métrica | Antes dos Índices | Depois dos Índices | Ganho / Impacto |
| :--- | :--- | :--- | :--- | :--- |
| **Teste 1:** `voo.aeronave_id` | **Operação** | `TABLE ACCESS FULL` (`VOO`) | `INDEX RANGE SCAN` (`IDX_VOO_AERONAVE`) + `TABLE ACCESS BY INDEX ROWID BATCHED` | Eliminação de Full Scan |
| | **Predicado** | `filter("V"."AERONAVE_ID"=1)` | `access("V"."AERONAVE_ID"=1)` | Busca direta na árvore B-Tree |
| | **Plan Hash** | `2745278212` | `1894607921` | Plano otimizado |
| | **Custo (Cost)** | `3` | `2` | **-33,3%** |
| | **Tempo (`DISPLAY`)** | `00:00:00.17` | `00:00:00.03` | **-82,4%** |
| **Teste 2:** `voo.pista_id` | **Operação** | `TABLE ACCESS FULL` (`VOO`) | `INDEX RANGE SCAN` (`IDX_VOO_PISTA`) + `TABLE ACCESS BY INDEX ROWID BATCHED` | Eliminação de Full Scan |
| | **Predicado** | `filter("V"."PISTA_ID"=1)` | `access("V"."PISTA_ID"=1)` | Busca direta na árvore B-Tree |
| | **Plan Hash** | `2745278212` | `454668149` | Plano otimizado |
| | **Custo (Cost)** | `3` | `2` | **-33,3%** |
| | **Tempo (`DISPLAY`)** | `00:00:00.03` | `00:00:00.02` | **-33,3%** |
| **Teste 3:** `ordem_manutencao.aeronave_id` | **Operação** | `TABLE ACCESS FULL` (`ORDEM_MANUTENCAO`) | `INDEX RANGE SCAN` (`IDX_MANUTENCAO_AERONAVE`) | *Index-Only Scan* (sem leitura de tabela) |
| | **Predicado** | `filter("OM"."AERONAVE_ID"=1)` | `access("OM"."AERONAVE_ID"=1)` | Busca direta na árvore B-Tree |
| | **Plan Hash** | `2401153907` | `1046830824` | Plano otimizado |
| | **Custo (Cost)** | `3` | `1` | **-66,7%** |
| | **Tempo (`DISPLAY`)** | `00:00:00.03` | `00:00:00.02` | **-33,3%** |

---

## 3. Evidências dos Planos de Execução (`DBMS_XPLAN`)

### Teste 1 — Consulta por Aeronave (`voo.aeronave_id`)
```sql
SELECT v.voo_id FROM voo v JOIN aeronave a ON v.aeronave_id = a.aeronave_id WHERE v.aeronave_id = 1;
```

**Antes:**
```text
Plan hash value: 2745278212
--------------------------------------------------------------------------
| Id  | Operation         | Name | Rows  | Bytes | Cost (%CPU)| Time     |
--------------------------------------------------------------------------
|   0 | SELECT STATEMENT  |      |     1 |    26 |     3   (0)| 00:00:01 |
|*  1 |  TABLE ACCESS FULL| VOO  |     1 |    26 |     3   (0)| 00:00:01 |
--------------------------------------------------------------------------
Predicate Information: 1 - filter("V"."AERONAVE_ID"=1)
```

**Depois:**
```text
Plan hash value: 1894607921
--------------------------------------------------------------------------------------------------------
| Id  | Operation                           | Name             | Rows  | Bytes | Cost (%CPU)| Time     |
--------------------------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT                    |                  |     1 |    26 |     2   (0)| 00:00:01 |
|   1 |  TABLE ACCESS BY INDEX ROWID BATCHED| VOO              |     1 |    26 |     2   (0)| 00:00:01 |
|*  2 |   INDEX RANGE SCAN                  | IDX_VOO_AERONAVE |     1 |       |     1   (0)| 00:00:01 |
--------------------------------------------------------------------------------------------------------
Predicate Information: 2 - access("V"."AERONAVE_ID"=1)
```

---

### Teste 2 — Consulta por Pista (`voo.pista_id`)
```sql
SELECT v.voo_id FROM voo v JOIN pista p ON v.pista_id = p.pista_id WHERE v.pista_id = 1;
```

**Antes:**
```text
Plan hash value: 2745278212
--------------------------------------------------------------------------
| Id  | Operation         | Name | Rows  | Bytes | Cost (%CPU)| Time     |
--------------------------------------------------------------------------
|   0 | SELECT STATEMENT  |      |     1 |    26 |     3   (0)| 00:00:01 |
|*  1 |  TABLE ACCESS FULL| VOO  |     1 |    26 |     3   (0)| 00:00:01 |
--------------------------------------------------------------------------
Predicate Information: 1 - filter("V"."PISTA_ID"=1)
```

**Depois:**
```text
Plan hash value: 454668149
-----------------------------------------------------------------------------------------------------
| Id  | Operation                           | Name          | Rows  | Bytes | Cost (%CPU)| Time     |
-----------------------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT                    |               |     1 |    26 |     2   (0)| 00:00:01 |
|   1 |  TABLE ACCESS BY INDEX ROWID BATCHED| VOO           |     1 |    26 |     2   (0)| 00:00:01 |
|*  2 |   INDEX RANGE SCAN                  | IDX_VOO_PISTA |     1 |       |     1   (0)| 00:00:01 |
-----------------------------------------------------------------------------------------------------
Predicate Information: 2 - access("V"."PISTA_ID"=1)
```

---

### Teste 3 — Contagem de Ordens de Manutenção (`ordem_manutencao.aeronave_id`)
```sql
SELECT COUNT(*) FROM ordem_manutencao om JOIN aeronave a ON om.aeronave_id = a.aeronave_id WHERE om.aeronave_id = 1;
```

**Antes:**
```text
Plan hash value: 2401153907
---------------------------------------------------------------------------------------
| Id  | Operation          | Name             | Rows  | Bytes | Cost (%CPU)| Time     |
---------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT   |                  |     1 |    13 |     3   (0)| 00:00:01 |
|   1 |  SORT AGGREGATE    |                  |     1 |    13 |            |          |
|*  2 |   TABLE ACCESS FULL| ORDEM_MANUTENCAO |     1 |    13 |     3   (0)| 00:00:01 |
---------------------------------------------------------------------------------------
Predicate Information: 2 - filter("OM"."AERONAVE_ID"=1)
```

**Depois:**
```text
Plan hash value: 1046830824
---------------------------------------------------------------------------------------------
| Id  | Operation         | Name                    | Rows  | Bytes | Cost (%CPU)| Time     |
---------------------------------------------------------------------------------------------
|   0 | SELECT STATEMENT  |                         |     1 |    13 |     1   (0)| 00:00:01 |
|   1 |  SORT AGGREGATE   |                         |     1 |    13 |            |          |
|*  2 |   INDEX RANGE SCAN| IDX_MANUTENCAO_AERONAVE |     1 |    13 |     1   (0)| 00:00:01 |
---------------------------------------------------------------------------------------------
Predicate Information: 2 - access("OM"."AERONAVE_ID"=1)
```

---

## 4. Análise Técnica dos Resultados
1. **Transição de `filter` para `access`:** Antes da indexação, o otimizador do Oracle precisava ler todos os blocos das tabelas `VOO` e `ORDEM_MANUTENCAO` na memória e descartar linhas via `filter()`. Após a criação dos índices B-Tree, a condição passou a ser resolvida diretamente via `access()` na estrutura ordenada do índice (`INDEX RANGE SCAN`).

2. **Eliminação de Junção (*Join Elimination*):** Como as restrições de chave estrangeira (`FOREIGN KEY`) garantem integridade referencial com as tabelas pai (`AERONAVE` e `PISTA`) e nenhuma coluna das tabelas pai foi projetada no `SELECT`, o otimizador baseado em custo (CBO) do Oracle descartou a leitura redundante das tabelas pai nos planos de execução.

3. **Leitura Exclusiva pelo Índice (*Index-Only Scan*) no Teste 3:** Na consulta de agregação (`COUNT(*)`), o índice `IDX_MANUTENCAO_AERONAVE` contém todas as informações necessárias para contabilizar os registros da aeronave. O Oracle eliminou completamente o acesso aos blocos de dados da tabela `ORDEM_MANUTENCAO`, derrubando o custo total da operação de `3` para `1` (-66,7%).