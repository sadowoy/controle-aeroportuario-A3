CREATE INDEX idx_voo_aeronave ON voo(aeronave_id);
CREATE INDEX idx_voo_pista ON voo(pista_id);
CREATE INDEX idx_manutencao_aeronave ON ordem_manutencao(aeronave_id);