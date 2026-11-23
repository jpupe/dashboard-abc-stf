#!/usr/bin/env python3
"""
06_verificar_outputs.py — Verifica a coerência entre o banco (output 2) e o
dicionário (output 3):
  1. as colunas do banco são exatamente as da aba 'Colunas do banco', na mesma ordem;
  2. todo ID_pergunta do banco existe no 'Catálogo de perguntas';
  3. toda linha tem ID_linha único;
  4. resumo de alertas da conferência automática.
Uso: python 06_verificar_outputs.py banco.xlsx dicionario.xlsx
"""
import sys
from collections import Counter

from openpyxl import load_workbook

banco, dic = sys.argv[1:3]
wb, wd = load_workbook(banco, read_only=True), load_workbook(dic, read_only=True)
linhas = list(wb["Banco"].iter_rows(values_only=True))
cab, dados = list(linhas[0]), linhas[1:]
col_dic = [r[1] for r in list(wd["Colunas do banco"].iter_rows(values_only=True))[1:]]
cat = {r[1] for r in list(wd["Catálogo de perguntas"].iter_rows(values_only=True))[1:]}
ok = True
if cab != col_dic:
    ok = False
    print("ERRO: colunas do banco ≠ dicionário", set(cab) ^ set(col_dic))
else:
    print(f"ok: {len(cab)} colunas do banco = {len(col_dic)} linhas da aba 'Colunas do banco', mesma ordem")
ip = cab.index("ID_pergunta")
fora = {r[ip] for r in dados} - cat
if fora:
    ok = False
    print("ERRO: perguntas fora do catálogo:", fora)
else:
    print(f"ok: {len({r[ip] for r in dados})} perguntas usadas, todas no catálogo ({len(cat)})")
ids = Counter(r[cab.index("ID_linha")] for r in dados)
dup = [k for k, v in ids.items() if v > 1]
print("ok: ID_linha único" if not dup else f"ERRO: ID_linha duplicado {dup[:5]}")
ok &= not dup
conf = Counter("ok" if str(r[cab.index("Conferência automática")]).startswith("ok") else "a conferir" for r in dados)
orig = Counter(r[cab.index("Origem da resposta")] for r in dados)
dec = Counter(r[cab.index("Decisão")] for r in dados)
print(f"linhas: {len(dados)} | por decisão: {dict(dec)}")
print(f"conferência: {dict(conf)} | origem: {dict(orig)}")
sys.exit(0 if ok else 1)
