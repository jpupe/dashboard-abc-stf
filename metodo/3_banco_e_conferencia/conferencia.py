# -*- coding: utf-8 -*-
"""
conferencia.py — Conferência automática da codificação (Passo 4).

Verificações, sem alterar nenhuma resposta:
  1. TRECHOS: cada trecho citado existe no texto da página indicada do banco
     SQLite (tolerância para hifenização, quebras de linha, aspas e espaços;
     se não estiver na página indicada, procura nas páginas vizinhas e avisa).
  2. DOMÍNIO: toda categoria usada está entre as permitidas para a pergunta
     (ou é um marcador de dados do instrumento).
  3. COMPLETUDE: toda pergunta aplicável tem resposta ou marcador.
  4. COMPATIBILIDADE: regras da seção 7.4 (posição × densificação ×
     atribuição × concretização), regras 8.1 da função simbólica e coerência
     das sínteses da seção 12 com os blocos de origem.
Os alertas vão para a coluna "Conferência automática" e para o relatório
de conferência da decisão; a decisão sobre cada alerta é da pesquisadora.
"""
import re
import sqlite3
import unicodedata

MARCADORES = {"Não aplicável", "Informação não disponível ou não localizada",
              "Inconclusivo — evidência examinada insuficiente",
              "Campo aplicável ainda não preenchido",
              "Registro provisório pendente de conferência"}


def normaliza(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "")
    t = re.sub(r"-\s*\n\s*", "", t)            # hifenização no fim da linha
    t = re.sub(r"(?<=\w)-\s+(?=\w)", "", t)      # idem, quando a quebra virou espaço
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"\s+", " ", t).lower()
    return re.sub(r"[^\w\s§º°ª%/.,;:()\"'-]", "", t).strip()


class Textos:
    def __init__(self, db):
        self.con = sqlite3.connect(db)
        self._cache = {}

    def pagina(self, id_decisao, pag):
        k = (id_decisao, pag)
        if k not in self._cache:
            r = self.con.execute("SELECT texto, pagina_impressa, origem_texto FROM paginas "
                                 "WHERE id_decisao=? AND pagina_pdf=?", (id_decisao, pag)).fetchone()
            self._cache[k] = (normaliza(r[0]), r[1], r[2]) if r else None
        return self._cache[k]

    def impressa(self, id_decisao, pag):
        p = self.pagina(id_decisao, pag)
        return p[1] if p else None

    def localizar(self, id_decisao, trecho, pag):
        """Retorna (status, página onde achou)."""
        alvo = normaliza(trecho).strip(" .,;:\"'…")
        alvo = re.sub(r"\s*(\.\.\.|…)\s*", "\x00", alvo)  # reticências = elipse no trecho
        partes = [x.strip() for x in alvo.split("\x00") if len(x.strip()) >= 8]
        if not partes:
            return "trecho curto demais", None
        def acha(p):
            pg = self.pagina(id_decisao, p)
            return pg and all(x in pg[0] for x in partes)
        if acha(pag):
            return "ok", pag
        # trecho que atravessa a quebra de página
        for p in (pag, pag - 1):
            a, b = self.pagina(id_decisao, p), self.pagina(id_decisao, p + 1)
            if a and b and all(x in a[0] + " " + b[0] for x in partes):
                return "ok (atravessa páginas)", p
        for d in (1, -1, 2, -2, 3, -3):
            if acha(pag + d):
                return f"página divergente (achado na p. {pag + d})", pag + d
        pg = self.pagina(id_decisao, pag)
        if pg and pg[2] == "ocr":
            return "não localizado (página de OCR: conferir na imagem)", None
        return "NÃO LOCALIZADO", None


def valida_dominio(resposta, categorias, multipla):
    if not categorias or resposta in (None, ""):
        return None
    if resposta in MARCADORES:
        return None
    perm = [c.strip() for c in categorias.split("|")]
    abertas = [c[:-3].strip() for c in perm if c.endswith("…")]  # "outro: …"
    itens = [x.strip() for x in resposta.split(" ; ")] if multipla else [resposta.strip()]
    ruins = [x for x in itens if x not in perm and not any(x.startswith(a) for a in abertas)
             and x not in MARCADORES]
    if len(itens) > 1 and not multipla:
        return "resposta múltipla em pergunta de resposta única"
    return f"categoria fora do domínio: {ruins}" if ruins else None


def compatibilidade(r):
    """r: dict ID_pergunta -> resposta (texto) de UM núcleo. Retorna {ID: [alertas]}."""
    al = {}

    def add(pid, msg):
        al.setdefault(pid, []).append(msg)

    for px in ("IN", "FSP", "MA"):
        pos, den = r.get(f"{px}_B_posicao", ""), r.get(f"{px}_C_densificacao", "")
        atr, con = r.get(f"{px}_AT_atribuicao", ""), r.get(f"{px}_CN_concretizacao", "")
        mob = r.get(f"{px}_B_forma_mobilizacao", "")
        ent, fs = r.get(f"{px}_FS_entrada", ""), r.get(f"{px}_FS_funcao_simbolica", "")
        cn = f"{px}_CN_concretizacao"
        if pos in ("Ausente", "Presença documental não judicial"):
            if den and den != "Não aplicável":
                add(f"{px}_C_densificacao", "7.4: posição Ausente/Presença documental não judicial exige densificação 'Não aplicável'")
            if atr and atr != "Atribuição de critério não demonstrada":
                add(f"{px}_AT_atribuicao", "7.4: esperado 'Atribuição de critério não demonstrada'")
            if con and con != "Não mobilizado":
                add(cn, "7.4: esperado 'Não mobilizado'")
        if den in ("Densificação no caso/corrente", "Densificação institucional com critério potencialmente replicável") \
                and atr not in ("Contribuição própria ao critério", "Contribuição compartilhada"):
            add(f"{px}_C_densificacao", "7.4: densificação exige Contribuição própria ou compartilhada")
        if pos == "Voto não prevalecente":
            if den == "Densificação institucional com critério potencialmente replicável":
                add(f"{px}_C_densificacao", "7.4: voto não prevalecente não admite densificação institucional")
            if con and con != "Presença contextual/discursiva":
                add(cn, "7.4: voto não prevalecente → Presença contextual/discursiva no plano institucional")
        if pos in ("Genérica/ornamental", "Relevante sem participação determinante"):
            if mob.strip() == "não mobilizado":
                add(f"{px}_B_forma_mobilizacao", "7.4: 'não mobilizado' inadmissível com presença judicial")
            if con and con != "Presença contextual/discursiva":
                add(cn, "7.4: esperado 'Presença contextual/discursiva'")
        if con == "Concretização no caso" and not (pos == "Fundamento determinante" and den == "Densificação no caso/corrente"
                                                   and atr in ("Contribuição própria ao critério", "Contribuição compartilhada")):
            add(cn, "7.4: Concretização no caso exige FD + Densificação no caso/corrente + contribuição própria/compartilhada")
        if con.startswith("Concretização institucional") and not (
                pos == "Fundamento determinante" and den.startswith("Densificação institucional")
                and atr in ("Contribuição própria ao critério", "Contribuição compartilhada")):
            add(cn, "7.4: Concretização institucional exige FD + Densificação institucional + contribuição própria/compartilhada")
        if pos == "Fundamento determinante" and den == "Conteúdo não densificado" and con and con != "Fundamento determinante sem densificação":
            add(cn, "7.4: FD + Conteúdo não densificado → esperado 'Fundamento determinante sem densificação'")
        if con == "Fundamento determinante sem densificação" and atr == "Presença contextual":
            add(f"{px}_AT_atribuicao", "7.4: Presença contextual não admitida na combinação FD sem densificação")
        # 8.1 função simbólica
        if ent == "não" and fs and fs != "Não aplicável":
            add(f"{px}_FS_funcao_simbolica", "8.1: entrada negativa → 'Não aplicável'")
        if fs == "Função simbólica demonstrada":
            req = {f"{px}_FS_entrada": ("sim",), f"{px}_FS_proeminencia": ("média", "alta"),
                   f"{px}_FS_baixa_contribuicao": ("demonstrada",), f"{px}_FS_discrepancia": ("presente",),
                   f"{px}_FS_politico_ideologica": ("demonstrada no plano discursivo",)}
            for k, ok in req.items():
                if r.get(k) not in ok:
                    add(f"{px}_FS_funcao_simbolica", f"8.1: requisito não atendido em {k}")
            if not r.get(f"{px}_FS_funcao_identificavel") or r.get(f"{px}_FS_funcao_identificavel") in MARCADORES:
                add(f"{px}_FS_funcao_simbolica", "8.1: falta Função identificável")
            if pos in ("Ausente", "Presença documental não judicial"):
                add(f"{px}_FS_funcao_simbolica", "8: Ausente/Presença documental não sustentam FS demonstrada")
        # síntese 12
        for a, b in ((f"S12_{px}_concretizacao", cn), (f"S12_{px}_funcao_simbolica", f"{px}_FS_funcao_simbolica")):
            if r.get(a) and r.get(b) and r[a] != r[b]:
                add(a, f"síntese diverge de {b}")
    if r.get("S12_resolucao_operativa") and r.get("S06_resolucao_operativa") and r["S12_resolucao_operativa"] != r["S06_resolucao_operativa"]:
        add("S12_resolucao_operativa", "síntese diverge de S06_resolucao_operativa")
    return al
