#!/usr/bin/env python3
"""Ferramenta de trabalho: grava o texto de uma decisão (do SQLite) em arquivo,
com marcadores de página e sem os rodapés de certificação, para leitura."""
import re, sqlite3, sys
db, idd, saida = sys.argv[1:4]
con = sqlite3.connect(db)
with open(saida, "w", encoding="utf-8") as f:
    for pg, imp, peca, t in con.execute("SELECT pagina_pdf, pagina_impressa, peca, texto FROM paginas WHERE id_decisao=? ORDER BY pagina_pdf", (idd,)):
        t = re.sub(r"Documento assinado digitalmente[^\n]*\n[^\n]*\n?", "", t)
        t = re.sub(r"Inteiro Teor do Ac[óo]rd[ãa]o - P[áa]gina \d+ de \d+\s*", "", t)
        t = re.sub(r"Supremo Tribunal Federal\s*", "", t)
        t = re.sub(r"[ \t]+\n", "\n", t)
        t = re.sub(r"(?<![.:;!?\n])\n(?!\n)", " ", t)  # junta linhas quebradas
        t = re.sub(r" {2,}", " ", t)
        f.write(f"\n=== [p.{pg} | impr.{imp or '-'}] ===\n{t.strip()}\n")
