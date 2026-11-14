import oracledb

DB_CONFIG = {
    "user": "usuario_lab",
    "password": "senha_lab",
    "dsn": "localhost:1521/XEPDB1",
}


def executar_demonstracao():
    print("Conectando ao Oracle XE 21c (XEPDB1)...")
    try:
        with oracledb.connect(**DB_CONFIG) as conn:
            print(f"Conectado com sucesso! Versao do Oracle: {conn.version}\n")

            with conn.cursor() as cursor:
                # 1. CONSULTA ANALITICA (SELECT + JOIN + GROUP BY + HAVING)
                print("=== 1. Consulta: Modelos com MTOW > 75.000 kg e Voos Agendados ===")
                sql_consulta = """
                    SELECT m.fabricante, m.nome, m.mtow_kg, COUNT(v.voo_id) AS qtd_voos
                    FROM modelo_aeronave m
                    JOIN aeronave a ON m.modelo_id = a.modelo_id
                    LEFT JOIN voo v ON a.aeronave_id = v.aeronave_id AND v.status = 'AGENDADO'
                    GROUP BY m.fabricante, m.nome, m.mtow_kg
                    HAVING m.mtow_kg > 75000
                    ORDER BY m.mtow_kg DESC
                """
                cursor.execute(sql_consulta)
                for fabricante, nome, mtow, qtd in cursor.fetchall():
                    print(f" - {fabricante} {nome} | MTOW: {mtow:,.2f} kg | Voos Agendados: {qtd}")

                # 2. EXECUCAO DA PROCEDURE PL/SQL (registrar_manutencao)
                print("\n=== 2. Executando Procedure: registrar_manutencao(aeronave_id=1, severidade=3) ===")
                cursor.callproc("registrar_manutencao", [1, 3])

                cursor.execute("""
                    SELECT ordem_id, aeronave_id, nivel_severidade, status, TO_CHAR(data_abertura, 'DD/MM/YYYY')
                    FROM ordem_manutencao
                    WHERE aeronave_id = 1
                    ORDER BY ordem_id DESC
                    FETCH FIRST 1 ROW ONLY
                """)
                ordem = cursor.fetchone()
                print(
                    f" Ordem gerada na transacao -> ID: {ordem[0]} | Aeronave: {ordem[1]} | "
                    f"Severidade: {ordem[2]} | Status: {ordem[3]} | Data: {ordem[4]}"
                )
                # Reverte a transacao de demonstracao para manter a massa de dados inicial limpa
                conn.rollback()
                print(" (Rollback aplicado para preservar o estado inicial do banco de testes)")

                # 3. VALIDACAO DA TRIGGER DE MTOW (trg_valida_peso_voo)
                print("\n=== 3. Testando Trigger de MTOW (Tentativa de inserir voo com 999.999 kg) ===")
                try:
                    sql_insert_invalido = """
                        INSERT INTO voo (aeronave_id, pista_id, data_hora_prevista, peso_total_kg, status)
                        VALUES (1, 1, SYSTIMESTAMP, 999999.00, 'AGENDADO')
                    """
                    cursor.execute(sql_insert_invalido)
                    conn.commit()
                except oracledb.DatabaseError as err:
                    (error_obj,) = err.args
                    print(" Bloqueio da Trigger capturado com sucesso!")
                    print(f" Codigo Oracle: ORA-{error_obj.code}")
                    print(f" Mensagem: {error_obj.message.splitlines()[0]}")
                    conn.rollback()

    except oracledb.Error as e:
        print(f"Erro ao conectar ou executar no Oracle: {e}")


if __name__ == "__main__":
    executar_demonstracao()