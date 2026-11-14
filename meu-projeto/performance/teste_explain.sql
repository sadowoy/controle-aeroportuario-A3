SET TIMING ON;
SET LINESIZE 200;
SET PAGESIZE 100;

-- Teste 1: FK voo.aeronave_id
EXPLAIN PLAN FOR
SELECT v.voo_id FROM voo v JOIN aeronave a ON v.aeronave_id = a.aeronave_id WHERE v.aeronave_id = 1;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- Teste 2: FK voo.pista_id
EXPLAIN PLAN FOR
SELECT v.voo_id FROM voo v JOIN pista p ON v.pista_id = p.pista_id WHERE v.pista_id = 1;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- Teste 3: FK ordem_manutencao.aeronave_id
EXPLAIN PLAN FOR
SELECT COUNT(*) FROM ordem_manutencao om JOIN aeronave a ON om.aeronave_id = a.aeronave_id WHERE om.aeronave_id = 1;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);