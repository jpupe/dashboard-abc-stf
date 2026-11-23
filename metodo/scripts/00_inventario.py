#!/usr/bin/env python3
"""
00_inventario.py — Inventário e controle documental (Passo 0).

Lê decisoes.sqlite (gerado por 01_extrair_pdfs.py) e grava:
  - tabela `inventario` no próprio banco;
  - inventario.csv (para consulta e para o apêndice).

Para cada decisão: páginas, origem, OCR, palavras, faixa de tamanho e
presença das peças (ementa, acórdão, relatório, voto, extrato de ata).
Uso: python 00_inventario.py decisoes.sqlite
"""
import csv
import re
import sqlite3
import sys

PECAS = {
    "ementa": r"\bEMENTA\b",
    "acordao": r"\bAC[ÓO]RD[ÃA]O\b|\bACORDAM\b",
    "relatorio": r"\bRELAT[ÓO]RIO\b",
    "voto": r"\bVOTO\b",
    "extrato_ata": r"EXTRATO\s+DE\s+ATA",
}

# Observações de controle já conhecidas (registradas, não alteram o escopo).
OBS = {
    "ADPF_935_MC-Ref": "Decisão sobre cavidades naturais subterrâneas. Excluída na "
                       "triagem automática da planilha de seleção ('sem nexo com atividade "
                       "minerária'); incluída por decisão da pesquisadora na revisão.",
    "ACO_399_AgR": "Marcada como 'decisão não selecionada' (agravo interno) na planilha de "
                   "seleção, mas está na pasta do projeto; incluída no escopo por estar entre "
                   "os 27 PDFs. Confirmar com a pesquisadora.",
    "ADI_6233": "Dependência: aplica integralmente a ADI 4606.",
    "ADI_7273_MC-Ref": "Dependência: cautelar da ADI 7273 (mérito também no conjunto).",
    "ADI_7273": "Dependência: mérito da ADI 7273 MC-Ref (cautelar também no conjunto).",
}


def faixa(p):
    return "curta (≤30 p.)" if p <= 30 else "média (31–70 p.)" if p <= 70 else "longa (>70 p.)"


def main(db):
    con = sqlite3.connect(db)
    con.execute("DROP TABLE IF EXISTS inventario")
    con.execute("""CREATE TABLE inventario (id_decisao TEXT PRIMARY KEY, arquivo TEXT,
        origem TEXT, total_paginas INT, paginas_ocr INT, total_palavras INT, faixa TEXT,
        processar_em_partes INT, tem_ementa INT, tem_acordao INT, tem_relatorio INT,
        tem_voto INT, tem_extrato_ata INT, completo INT, observacao TEXT)""")
    linhas = []
    for (id_, arq, orig, pags, ocr, pal) in con.execute(
            "SELECT id_decisao, arquivo, origem, total_paginas, paginas_ocr, total_palavras FROM decisoes ORDER BY id_decisao").fetchall():
        texto = " ".join(t for (t,) in con.execute("SELECT texto FROM paginas WHERE id_decisao=?", (id_,)))
        pres = {k: int(bool(re.search(rx, texto, re.I))) for k, rx in PECAS.items()}
        completo = int(all(pres.values()))
        obs = OBS.get(id_, "")
        if orig == "texto_projeto":
            obs = ("Fonte provisória: texto convertido do projeto (PDF original não disponível). " + obs).strip()
        reg = [id_, arq, orig, pags, ocr, pal, faixa(pags), int(pags > 70), *pres.values(), completo, obs]
        con.execute("INSERT INTO inventario VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reg)
        linhas.append(reg)
    con.commit()
    cab = ["id_decisao", "arquivo", "origem", "total_paginas", "paginas_ocr", "total_palavras",
           "faixa", "processar_em_partes", "tem_ementa", "tem_acordao", "tem_relatorio",
           "tem_voto", "tem_extrato_ata", "completo", "observacao"]
    with open("inventario.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cab)
        w.writerows(linhas)
    for l in linhas:
        print(f"{l[0]:18s} {l[3]:4d}p {l[5]:6d}pal  {l[6]:17s} completo={l[13]}  {l[14][:60]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "decisoes.sqlite")
