# -*- coding: utf-8 -*-
"""Cores e estilos comuns ao banco (output 2) e ao dicionário (output 3).
Paleta herdada do piloto aprovado pela pesquisadora."""
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

FONTE = "Arial"
COR_GRUPO = {
    "ID": "1F3864", "Controle": "595959",
    "1": "1F3864", "2": "1F3864", "3": "1F3864", "4": "1F3864",
    "5": "2E5597", "6": "2E5597",
    "Interesse nacional": "7F6000",
    "Função social da propriedade": "833C0B",
    "Meio ambiente ecologicamente equilibrado": "385723",
    "10.1": "404040", "11": "404040", "12": "404040", "13": "404040", "14": "404040",
    "15": "7030A0", "16": "7030A0",
    "Validação": "BF8F00",
}
AMARELO_VALIDACAO = "FFF2CC"


def cor_do_campo(c):
    """Cor do cabeçalho: blocos por princípio usam a cor do princípio."""
    if c.get("principio") and c["secao"] not in ("12", "13", "14"):
        return COR_GRUPO[c["principio"]]
    return COR_GRUPO.get(c["secao"], "404040")


def rotulo_grupo(c):
    if c["secao"] in ("ID", "Controle", "Validação"):
        return c["bloco"]
    return c["bloco"]


BORDA = Border(*(Side(style="thin", color="BFBFBF"),) * 4)


def cab(cell, cor, tamanho=9):
    cell.font = Font(name=FONTE, bold=True, color="FFFFFF", size=tamanho)
    cell.fill = PatternFill("solid", fgColor=cor)
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    cell.border = BORDA


def corpo(cell, wrap=True, tamanho=9):
    cell.font = Font(name=FONTE, size=tamanho)
    cell.alignment = Alignment(wrap_text=wrap, vertical="top")
    cell.border = BORDA
