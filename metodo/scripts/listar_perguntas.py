#!/usr/bin/env python3
"""Ferramenta de trabalho: lista o catálogo de perguntas (ID | nível | tipo | categorias | regra | campos absorvidos)."""
import json, sys
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "dicionario_campos.json", encoding="utf-8"))
for q in d["catalogo"]:
    linha = f"{q['id_pergunta']} | {q['nivel']} | {q['tipo']}{' ('+q['resposta']+')' if q['resposta'] else ''} | {q['descricao']}"
    if q["categorias"]: linha += f" | CAT: {q['categorias']}"
    if q["regra_entrada"]: linha += f" | REGRA: {q['regra_entrada']}"
    if q.get("absorve"): linha += f" | ABSORVE: {q['absorve']}"
    if q.get("tabela_variavel"): linha += f" | TABELA VARIÁVEL: {q['tabela_variavel']}"
    print(linha)
