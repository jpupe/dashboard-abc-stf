#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_gerar_banco.py — Gera o output 2 (banco_ABC_STF_mineracao.xlsx) em formato
longo a partir dos JSON de codificação (um por decisão), aplicando as regras
de salto do instrumento e a conferência automática.

Formato: UMA PLANILHA, UMA LINHA POR RESPOSTA (decisão × núcleo × item ×
pergunta). As perguntas e a ordem vêm do catálogo (dicionario_campos.json).

Regras de salto aplicadas pelo script quando a resposta não veio no JSON
(Origem da resposta = "regra de salto"):
  - posição Ausente/Presença documental não judicial → densificação e campos
    condicionados ao critério = Não aplicável (7.4);
  - pergunta de entrada da seção 8 negativa → indicadores e seção 9 = Não
    aplicável (8.1; mesmo padrão do gabarito da ADI 3355);
  - regra de entrada da seção 10 não atendida → campos da seção 10 = Não aplicável;
  - sínteses da seção 12 ausentes → copiadas dos blocos de origem;
  - qualquer outra pergunta aplicável sem resposta → "Campo aplicável ainda
    não preenchido" (pendência de completude, sinalizada na conferência).

Uso: python 04_gerar_banco.py PASTA_JSON decisoes.sqlite dicionario_campos.json SAIDA.xlsx
Gera também relatorio_conferencia.json e banco_longo.csv (para o dashboard e auditoria).
"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from conferencia import MARCADORES, Textos, compatibilidade, valida_dominio  # noqa: E402
from estilo_abc import AMARELO_VALIDACAO, BORDA, FONTE, cab, cor_do_campo  # noqa: E402

PASTA, DB, DIC, SAIDA = (Path(a) for a in sys.argv[1:5])
dic = json.loads(DIC.read_text(encoding="utf-8"))
CAT = dic["catalogo"]
COLS = [c["coluna"] for c in dic["colunas_banco"]]
PQ = {q["id_pergunta"]: q for q in CAT}
textos = Textos(DB)
con = sqlite3.connect(DB)

NA = "Não aplicável"
PENDENTE = "Campo aplicável ainda não preenchido"


def meta(id_dec):
    return dict(con.execute("SELECT campo, valor FROM metadados WHERE id_decisao=?", (id_dec,)).fetchall())


def norm_resp(v):
    """Aceita string ou dict {r,t,a,j,alt,s}. t = [[trecho, pag_pdf], ...]."""
    if v is None:
        return None
    if isinstance(v, (str, int, float)):
        return {"r": str(v)}
    return dict(v)


def salto(pid, resp_nucleo):
    """Retorna (resposta, justificativa) por regra de salto, ou None."""
    for px in ("IN", "FSP", "MA"):
        if not pid.startswith(px + "_"):
            continue
        g = lambda k: (resp_nucleo.get(f"{px}_{k}") or {}).get("r", "")
        pos, ent, aus = g("B_posicao"), g("FS_entrada"), g("AUS_aplicavel")
        if pos in ("Ausente", "Presença documental não judicial") and (
                pid.startswith(f"{px}_C_") or pid in (f"{px}_AT_contribuicao_especifica",)):
            return NA, "Regra 7.4: posição Ausente/Presença documental não judicial exige Não aplicável na densificação."
        if pos in ("Ausente", "Presença documental não judicial") and pid in (f"{px}_AT_explicavel_outra_norma", f"{px}_AT_contrafactual"):
            return "Não aplicável — justificar", "Sem critério demonstrável: princípio não mobilizado judicialmente (7.x.3)."
        if ent == "não" and pid.startswith(f"{px}_FS_") and pid not in (
                f"{px}_FS_entrada", f"{px}_FS_funcao_simbolica", f"{px}_FS_nucleo_segmento", f"{px}_FS_plano"):
            return NA, "Seção 8.1: pergunta de entrada negativa."
        if ent == "não" and pid.startswith(f"{px}_ALT_"):
            return NA, "Pergunta de entrada negativa na seção 8; indicadores de função simbólica não acionados (seção 9 sem efeito)."
        if aus.startswith("não") and pid.startswith(f"{px}_AUS_") and pid != f"{px}_AUS_aplicavel":
            return NA, "Regra de entrada da seção 10 não atendida para este princípio."
    return None


ORIGEM_S12 = {"S12_resolucao_operativa": "S06_resolucao_operativa"}
for px in ("IN", "FSP", "MA"):
    ORIGEM_S12[f"S12_{px}_concretizacao"] = f"{px}_CN_concretizacao"
    ORIGEM_S12[f"S12_{px}_funcao_simbolica"] = f"{px}_FS_funcao_simbolica"


def resumo_conf(confs):
    """'ok' quando nada a conferir; trechos localizados viram contagem."""
    problemas = [c for c in confs if not (c.startswith("trecho") and c.split(": ", 1)[1].startswith("ok"))]
    n_ok = len(confs) - len(problemas)
    if not problemas:
        return f"ok ({n_ok} trecho(s) localizado(s))" if n_ok else "ok"
    return "; ".join(problemas) + (f" | {n_ok} trecho(s) ok" if n_ok else "")


def linhas_decisao(js):
    idd = js["id_decisao"]
    md = meta(idd)
    dados_d = con.execute("SELECT classe, numero, sufixo FROM decisoes WHERE id_decisao=?", (idd,)).fetchone()
    rotulo = js.get("rotulo") or " ".join(x for x in dados_d if x)
    base = {"ID_decisao": idd, "Decisão": rotulo, "Classe": dados_d[0],
            "Data do julgamento": js.get("data_final") or md.get("data_julgamento", "")}
    out = []

    def emite(q, resp, nivel, nucleo="", titulo="", item="", origem="LLM", extra_alerta=None):
        r = norm_resp(resp) or {}
        trechos = r.get("t") or []
        if trechos and isinstance(trechos[0], str):
            trechos = [trechos]
        pags, impr, confs = [], [], []
        for tr in trechos:
            txt, pg = tr[0], int(tr[1])
            pags.append(str(pg))
            impr.append(textos.impressa(idd, pg) or "—")
            st, _ = textos.localizar(idd, txt, pg)
            confs.append(f"trecho {len(confs)+1}: {st}")
        alerta = valida_dominio(r.get("r", ""), q["categorias"], q["resposta"] == "múltipla")
        if alerta:
            confs.append(alerta)
        if r.get("r") == PENDENTE:
            confs.append("pendência de completude")
        if extra_alerta:
            confs += extra_alerta
        lid = f"{idd}|{nucleo or 'D'}|{item}|{q['id_pergunta']}"
        out.append({**base, "ID_linha": lid, "Nível": nivel, "Núcleo": nucleo, "Título do núcleo": titulo,
                    "Seção": q["secao"], "Grupo da pergunta": q["bloco"], "Princípio": q["principio"],
                    "Item": item, "ID_pergunta": q["id_pergunta"], "Pergunta do questionário": q["descricao"],
                    "Tipo de resposta": q["tipo"] + (f" ({q['resposta']})" if q["resposta"] else ""),
                    "Resposta": r.get("r", ""), "Trecho (evidência literal)": " || ".join(t[0] for t in trechos),
                    "Página PDF": " || ".join(pags), "Página impressa": " || ".join(impr),
                    "Autoria e plano": r.get("a", ""), "Justificativa": r.get("j", ""),
                    "Categoria alternativa e razão": r.get("alt", ""), "Segurança": r.get("s", ""),
                    "Origem da resposta": origem, "Conferência automática": resumo_conf(confs),
                    "_q": q})

    # ---- nível decisão (seções 1–4, 13, 14, 16 e controle documental)
    dec = {k: norm_resp(v) for k, v in js.get("decisao", {}).items()}
    defaults = {"S01_orgao_julgador": md.get("orgao_julgador"), "S01_relator_originario": md.get("relator"),
                "S01_redator_acordao": md.get("redator_acordao"), "S01_datas_julgamento": md.get("data_julgamento"),
                "S01_resultado_proclamado": md.get("resultado_extrato_ata")}
    for q in CAT:
        if q["nivel"] != "decisão" or q["tabela_variavel"]:
            continue
        pid = q["id_pergunta"]
        if pid.startswith("S13_") or pid.startswith("S14_") or pid.startswith("S16_"):
            continue  # emitidos depois do mapa e dos núcleos, na ordem do questionário
        if pid in dec:
            emite(q, dec[pid], "decisão")
        elif defaults.get(pid):
            emite(q, {"r": defaults[pid], "j": "Extraído por regra do PDF (tabela metadados)."}, "decisão", origem="extração automática")
        elif pid.startswith("S04_total"):
            continue
        else:
            emite(q, PENDENTE, "decisão", origem="pendência")
        if pid == "S04_total_elegiveis":
            # mapa (tabela variável) logo após os totais
            for i, ent in enumerate(js.get("mapa", []), start=1):
                for qm in [x for x in CAT if x["tabela_variavel"] == "Núcleo do mapa nº"]:
                    emite(qm, ent.get(qm["id_pergunta"], PENDENTE), "decisão", item=str(i))
    for pid in ("S04_total_nucleos", "S04_total_elegiveis"):
        if pid not in dec:
            pass

    # ---- núcleos
    nucleos = js.get("nucleos", [])
    if not nucleos:
        q = PQ["S05_S12_regra_parada"]
        emite(q, {"r": NA, "j": "Regra de parada: a triagem não identificou núcleo elegível (ver mapa da seção 4)."},
              "núcleo", nucleo="0", origem="regra de parada")
    for nu in nucleos:
        n, tit = str(nu["n"]), nu.get("titulo", "")
        resp = {k: norm_resp(v) for k, v in nu.get("respostas", {}).items()}
        for a, b in ORIGEM_S12.items():
            if a not in resp and b in resp:
                resp[a] = {"r": resp[b]["r"], "j": f"Síntese copiada de {b}."}
        compat = compatibilidade({k: (v or {}).get("r", "") for k, v in resp.items()})
        for q in CAT:
            if q["nivel"] != "núcleo" or q["id_pergunta"] == "S05_S12_regra_parada":
                continue
            pid = q["id_pergunta"]
            if q["tabela_variavel"] == "Categoria nº":
                if pid == "S10_CAT_principio":
                    for i, ent in enumerate(nu.get("categorias", []), start=1):
                        for qc in [x for x in CAT if x["tabela_variavel"] == "Categoria nº"]:
                            emite(qc, ent.get(qc["id_pergunta"], PENDENTE), "núcleo", n, tit, str(i))
                continue
            if q["tabela_variavel"] == "Controle nº":
                if pid == "S15_K_referencia":
                    for i, ent in enumerate(nu.get("controles", []), start=1):
                        for qc in [x for x in CAT if x["tabela_variavel"] == "Controle nº"]:
                            emite(qc, ent.get(qc["id_pergunta"], PENDENTE), "núcleo", n, tit, str(i))
                continue
            if pid == "S15_total_registros":
                emite(q, str(len(nu.get("controles", []))), "núcleo", n, tit, origem="script")
                continue
            origem = "LLM"
            if pid in resp:
                r = resp[pid]
                if (r.get("j") or "").startswith("Síntese copiada"):
                    origem = "script (síntese)"
            else:
                sj = salto(pid, resp)
                if sj:
                    r, origem = {"r": sj[0], "j": sj[1]}, "regra de salto"
                else:
                    r, origem = {"r": PENDENTE}, "pendência"
            emite(q, r, "núcleo", n, tit, origem=origem, extra_alerta=compat.get(pid))

    # ---- seções 13, 14, 16 (nível decisão, depois dos núcleos)
    for q in CAT:
        pid = q["id_pergunta"]
        if q["nivel"] == "decisão" and (pid.startswith("S13_") or pid.startswith("S14_") or pid.startswith("S16_")):
            emite(q, dec.get(pid, PENDENTE), "decisão", origem="LLM" if pid in dec else "pendência")
    return out


def escreve_xlsx(linhas):
    wb = Workbook()
    ws = wb.active
    ws.title = "Banco"
    larg = {"ID_linha": 10, "ID_decisao": 14, "Decisão": 15, "Classe": 7, "Data do julgamento": 11, "Nível": 8,
            "Núcleo": 7, "Título do núcleo": 24, "Seção": 7, "Grupo da pergunta": 28, "Princípio": 16, "Item": 6,
            "ID_pergunta": 22, "Pergunta do questionário": 42, "Tipo de resposta": 13, "Resposta": 40,
            "Trecho (evidência literal)": 50, "Página PDF": 8, "Página impressa": 8, "Autoria e plano": 26,
            "Justificativa": 50, "Categoria alternativa e razão": 34, "Segurança": 10, "Origem da resposta": 12,
            "Conferência automática": 24, "Concorda?": 11, "Correções": 30, "Comentário": 30}
    for j, c in enumerate(COLS, start=1):
        cell = ws.cell(row=1, column=j, value=c)
        cab(cell, "BF8F00" if c in ("Concorda?", "Correções", "Comentário") else "1F3864", 10)
        ws.column_dimensions[get_column_letter(j)].width = larg.get(c, 14)
    amarelo = PatternFill("solid", fgColor=AMARELO_VALIDACAO)
    alerta_fill = PatternFill("solid", fgColor="FCE4D6")
    fonte, wrap = Font(name=FONTE, size=9), Alignment(wrap_text=True, vertical="top")
    cache_fill = {}
    for i, l in enumerate(linhas, start=2):
        q = l["_q"]
        cor = cor_do_campo({"secao": q["secao"].split(".")[0] if q["secao"].startswith(("7", "8", "9")) else q["secao"],
                            "principio": q["principio"]})
        for j, c in enumerate(COLS, start=1):
            cell = ws.cell(row=i, column=j, value=l.get(c, ""))
            cell.font, cell.alignment, cell.border = fonte, wrap, BORDA
            if c in ("Concorda?", "Correções", "Comentário"):
                cell.fill = amarelo
        sc = ws.cell(row=i, column=COLS.index("Seção") + 1)
        sc.fill = cache_fill.setdefault(cor, PatternFill("solid", fgColor=cor))
        sc.font = Font(name=FONTE, size=9, bold=True, color="FFFFFF")
        cf = ws.cell(row=i, column=COLS.index("Conferência automática") + 1)
        if not str(cf.value).startswith("ok"):
            cf.fill = alerta_fill
    ws.freeze_panes = ws.cell(row=2, column=COLS.index("Pergunta do questionário") + 2)
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{len(linhas) + 1}"
    for c in ("ID_linha", "ID_decisao", "Classe"):
        ws.column_dimensions[get_column_letter(COLS.index(c) + 1)].hidden = False
    wb.save(SAIDA)


def main():
    todas, relat = [], {}
    for f in sorted(PASTA.glob("*.json")):
        js = json.loads(f.read_text(encoding="utf-8"))
        ls = linhas_decisao(js)
        todas += ls
        rel = {"linhas": len(ls),
               "nucleos": len(js.get("nucleos", [])),
               "trechos": sum(l["Página PDF"].count("||") + 1 for l in ls if l["Página PDF"]),
               "trechos_nao_localizados": [(l["ID_pergunta"], l["Núcleo"], l["Conferência automática"]) for l in ls
                                           if "NÃO LOCALIZADO" in l["Conferência automática"] or "divergente" in l["Conferência automática"]
                                           or "OCR" in l["Conferência automática"]],
               "fora_do_dominio": [(l["ID_pergunta"], l["Núcleo"], l["Resposta"]) for l in ls if "domínio" in l["Conferência automática"] or "múltipla em" in l["Conferência automática"]],
               "alertas_compatibilidade": [(l["ID_pergunta"], l["Núcleo"], l["Conferência automática"]) for l in ls
                                           if any(k in l["Conferência automática"] for k in ("7.4", "8.1", "8:", "síntese diverge"))],
               "pendencias_completude": [(l["ID_pergunta"], l["Núcleo"], l["Item"]) for l in ls if l["Resposta"] == PENDENTE],
               "por_origem": {}}
        for l in ls:
            rel["por_origem"][l["Origem da resposta"]] = rel["por_origem"].get(l["Origem da resposta"], 0) + 1
        relat[js["id_decisao"]] = rel
    escreve_xlsx(todas)
    with open(SAIDA.with_name("banco_longo.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore", delimiter=";")
        w.writeheader()
        w.writerows(todas)
    SAIDA.with_name("relatorio_conferencia.json").write_text(json.dumps(relat, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, r in relat.items():
        print(f"{k}: {r['linhas']} linhas, {r['nucleos']} núcleo(s), {r['trechos']} trechos, "
              f"{len(r['trechos_nao_localizados'])} trechos a conferir, {len(r['fora_do_dominio'])} fora do domínio, "
              f"{len(r['alertas_compatibilidade'])} alertas 7.4/8.1, {len(r['pendencias_completude'])} pendências")
    print(f"TOTAL: {len(todas)} linhas → {SAIDA}")


if __name__ == "__main__":
    main()
