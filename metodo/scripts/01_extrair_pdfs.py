#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_extrair_pdfs.py — Extração do texto das decisões do STF para banco SQLite
==========================================================================

Projeto: Banco A/B/C das decisões do STF em direito minerário
         (tese de doutorado de Suzy Sousa, UFPA)

O QUE ESTE SCRIPT FAZ
---------------------
1. Seleciona, na pasta indicada, os PDFs cujo nome começa com ADI, ACO, ADPF
   ou RE (as decisões a codificar) e avisa se não encontrar exatamente 27.
2. Extrai o texto de cada PDF PÁGINA POR PÁGINA, guardando o número da página
   do PDF e, quando localizável, a paginação impressa no documento.
3. Aplica OCR (Tesseract, idioma português) às páginas sem camada de texto
   ou com texto insuficiente, e marca quais páginas vieram de OCR.
4. Grava tudo em um banco SQLite com as tabelas:
     decisoes  — uma linha por decisão (arquivo, classe, número, sufixo,
                 páginas, OCR, hash do arquivo, data da extração, origem);
     paginas   — uma linha por página (texto, página do PDF, página
                 impressa, peça, origem do texto: nativo, OCR ou texto do
                 projeto);
     metadados — campos que são só dado, extraídos por regra (classe,
                 número, UF, relator, redator, data de julgamento, órgão
                 julgador, meio de julgamento, resultado do extrato de ata),
                 com o registro de divergências entre acórdão e ata
                 (quando divergem, prevalece a ata);
     execucoes — registro de cada execução do script.
5. Pode ser executado de novo sem duplicar registros: cada decisão é
   identificada por um id estável (ex.: "ADI_7273_MC-Ref") e seus registros
   são substituídos a cada execução.

PÁGINAS DUPLICADAS NA CAMADA DE TEXTO
-------------------------------------
Nos PDFs de inteiro teor do STF, a camada de texto de muitas páginas contém
a mesma página duas vezes (uma por camada de assinatura digital). O script
detecta quando uma cópia está contida na outra e guarda só a mais completa,
marcando a página com duplicacao_removida = 1. Nenhum texto distinto é
descartado: se as duas cópias diferirem, ambas são mantidas.

FONTE PROVISÓRIA EM TEXTO (--textos)
------------------------------------
No projeto da pesquisadora, nove decisões longas ficaram disponíveis apenas
como texto já convertido (sem o PDF original). Com a opção --textos, o script
lê esses arquivos .txt, separa as páginas pelo rodapé "Inteiro Teor do
Acórdão - Página N de M" (que o STF imprime em todas as páginas) e remove a
duplicação parcial de conteúdo gerada pela conversão. Essas páginas recebem
origem "texto_projeto". Se o PDF da mesma decisão existir na pasta, o PDF
sempre prevalece e o texto é ignorado.

USO
---
    pip install -r requirements.txt     # e o Tesseract com o pacote "por"
    python 01_extrair_pdfs.py PASTA_DOS_PDFS [--textos PASTA_TXT]
                              [--db decisoes.sqlite] [--dpi 300]

Ao final, o script imprime um resumo (decisões, páginas, páginas com OCR).

Dependências: PyMuPDF (leitura do PDF e renderização para OCR), pytesseract
+ Tesseract OCR 5 com dados de idioma "por", Pillow. Python 3.10+.
"""

import argparse
import datetime as dt
import hashlib
import io
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import pymupdf  # PyMuPDF

try:
    import pytesseract
    from PIL import Image
    OCR_DISPONIVEL = True
except ImportError:  # o script ainda funciona para PDFs com camada de texto
    OCR_DISPONIVEL = False

VERSAO_SCRIPT = "1.0 (20/11/2026)"
N_ESPERADO = 27

# Nome de arquivo de decisão: começa com a classe processual.
RE_ARQUIVO = re.compile(r"^(ADI|ACO|ADPF|RE)\s+([\d.]+)\s*(.*)$", re.IGNORECASE)

# Página com menos palavras que isto (na camada de texto) vai para OCR.
MIN_PALAVRAS_TEXTO = 20

# Rodapé que o STF imprime em todas as páginas do inteiro teor.
RE_RODAPE_PAGINA = re.compile(
    r"Inteiro Teor do Ac[óo]rd[ãa]o\s*-\s*P[áa]gina\s+(\d+)\s+de\s+(\d+)[^\n]*\n?")

# Linha de certificação digital (duas linhas) que fecha a área de texto.
RE_CERTIFICACAO = re.compile(
    r"Documento assinado digitalmente[^\n]*\n[^\n]*(?:\n|$)")


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
ESQUEMA = """
CREATE TABLE IF NOT EXISTS decisoes (
    id_decisao      TEXT PRIMARY KEY,   -- ex.: ADI_7273_MC-Ref
    arquivo         TEXT NOT NULL,      -- nome do arquivo de origem
    classe          TEXT NOT NULL,      -- ADI, ACO, ADPF, RE
    numero          TEXT NOT NULL,      -- número sem pontos
    sufixo          TEXT,               -- MC, AgR, RG, MC-Ref (ou vazio)
    total_paginas   INTEGER NOT NULL,
    paginas_ocr     INTEGER NOT NULL,   -- quantas páginas vieram de OCR
    houve_ocr       INTEGER NOT NULL,   -- 0/1
    origem          TEXT NOT NULL,      -- pdf | texto_projeto
    hash_sha256     TEXT NOT NULL,      -- hash do arquivo de origem
    total_palavras  INTEGER NOT NULL,
    data_extracao   TEXT NOT NULL,
    versao_script   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paginas (
    id_decisao      TEXT NOT NULL REFERENCES decisoes(id_decisao),
    pagina_pdf      INTEGER NOT NULL,   -- 1..N, ordem física no PDF
    pagina_impressa TEXT,               -- numeração impressa na peça, se houver
    peca            TEXT,               -- cabeçalho da peça (Ementa e Acórdão, Relatório, Voto...)
    texto           TEXT NOT NULL,
    origem_texto    TEXT NOT NULL,      -- nativo | ocr | texto_projeto
    n_palavras      INTEGER NOT NULL,
    duplicacao_removida INTEGER NOT NULL, -- 1 = cópia repetida da página descartada
    PRIMARY KEY (id_decisao, pagina_pdf)
);
CREATE TABLE IF NOT EXISTS metadados (
    id_decisao      TEXT NOT NULL REFERENCES decisoes(id_decisao),
    campo           TEXT NOT NULL,
    valor           TEXT,
    pagina_pdf      INTEGER,            -- onde o valor foi encontrado
    regra           TEXT,               -- regra de extração usada
    PRIMARY KEY (id_decisao, campo)
);
CREATE TABLE IF NOT EXISTS execucoes (
    data            TEXT,
    versao_script   TEXT,
    pasta_pdfs      TEXT,
    pasta_textos    TEXT,
    n_decisoes      INTEGER,
    n_paginas       INTEGER,
    n_paginas_ocr   INTEGER,
    avisos          TEXT
);
"""


def conectar(caminho_db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(caminho_db)
    con.executescript(ESQUEMA)
    return con


def apagar_decisao(con, id_decisao):
    """Remove registros anteriores da decisão (torna o script reexecutável)."""
    for tabela in ("paginas", "metadados", "decisoes"):
        con.execute(f"DELETE FROM {tabela} WHERE id_decisao = ?", (id_decisao,))


# ---------------------------------------------------------------------------
# Identificação da decisão a partir do nome do arquivo
# ---------------------------------------------------------------------------
def identificar(nome_arquivo: str):
    """'ADI 7.273 MC-Ref.pdf' -> ('ADI', '7273', 'MC-Ref', 'ADI_7273_MC-Ref')"""
    base = Path(nome_arquivo).stem.strip()
    m = RE_ARQUIVO.match(base)
    if not m:
        return None
    classe = m.group(1).upper()
    numero = m.group(2).replace(".", "")
    sufixo = m.group(3).strip()
    id_decisao = "_".join(x for x in (classe, numero, sufixo) if x)
    return classe, numero, sufixo, id_decisao


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Paginação impressa e peça
# ---------------------------------------------------------------------------
PECAS = ("Ementa e Acórdão", "Relatório", "Voto", "Antecipação ao Voto",
         "Aditamento ao Voto", "Esclarecimento", "Confirmação de Voto",
         "Debate", "Extrato de Ata", "Decisão de Julgamento", "Observação",
         "Explicação", "Vista", "Voto Vogal", "Voto-Vista", "Manifestação")


def detectar_peca(texto: str):
    """O STF imprime no topo de cada página o nome da peça (ex.: 'Voto - MIN. X')."""
    for linha in texto.strip().splitlines()[:3]:
        linha = linha.strip()
        for p in PECAS:
            if linha.lower().startswith(p.lower()):
                return linha[:120]
    return None


def detectar_pagina_impressa(texto: str):
    """
    A numeração impressa aparece como uma linha só com número, logo antes da
    certificação digital no pé da página. Procura nas últimas linhas úteis.
    """
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    corte = len(linhas)
    for i, l in enumerate(linhas):
        if l.startswith("Documento assinado digitalmente") or l == "Supremo Tribunal Federal":
            corte = i
            break
    for l in reversed(linhas[max(0, corte - 3):corte]):
        if re.fullmatch(r"\d{1,4}", l):
            return l
    return None


# ---------------------------------------------------------------------------
# Extração de PDF (texto nativo + OCR)
# ---------------------------------------------------------------------------
def palavras_reais(texto: str) -> int:
    """
    Conta palavras com 3 ou mais letras. Algumas capas escaneadas têm uma
    camada de texto residual com uma letra por linha (ex.: carimbos), que não
    deve ser confundida com texto legível.
    """
    return sum(1 for w in texto.split() if len(re.sub(r"[^A-Za-zÀ-ÿ]", "", w)) >= 3)


def ocr_pagina(pagina, dpi: int) -> str:
    pix = pagina.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img, lang="por")


def extrair_pdf(caminho: Path, dpi: int, avisos: list):
    doc = pymupdf.open(caminho)
    paginas = []
    for i, pg in enumerate(doc, start=1):
        texto = pg.get_text("text")
        origem = "nativo"
        if palavras_reais(texto) < MIN_PALAVRAS_TEXTO:
            if OCR_DISPONIVEL:
                texto_ocr = ocr_pagina(pg, dpi)
                if palavras_reais(texto_ocr) > palavras_reais(texto):
                    texto, origem = texto_ocr, "ocr"
            else:
                avisos.append(f"{caminho.name} p.{i}: sem texto e OCR indisponível")
        removeu = False
        if origem == "nativo":
            texto, removeu = deduplicar_pagina(texto)
        paginas.append({"pagina_pdf": i, "texto": texto, "origem_texto": origem,
                        "dedup": removeu})
    return paginas


# ---------------------------------------------------------------------------
# Extração de texto do projeto (fonte provisória)
# ---------------------------------------------------------------------------
def _norm(s: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", s))


def _sem_cabecalho(txt: str):
    """Separa as linhas de cabeçalho ('Supremo Tribunal Federal', nome da peça)."""
    linhas = txt.strip("\n").split("\n")
    cab = []
    while linhas and (linhas[0].strip() in ("", "Supremo Tribunal Federal")
                      or any(linhas[0].strip().lower().startswith(p.lower()) for p in PECAS)):
        cab.append(linhas.pop(0))
    return cab, "\n".join(linhas)


def deduplicar_pagina(seg: str):
    """
    A conversão do projeto às vezes grava a mesma página duas vezes dentro do
    mesmo segmento (cada cópia fechada pela certificação digital), com
    cabeçalhos diferentes ('Ementa e Acórdão' / 'Supremo Tribunal Federal').
    Se uma cópia, sem cabeçalho, estiver contida na outra, fica só a mais
    completa, com o cabeçalho da peça preservado. Retorna (texto, removeu).
    """
    certs = list(RE_CERTIFICACAO.finditer(seg))
    if len(certs) < 2:
        return seg, False
    a = seg[:certs[0].end()]
    b = seg[certs[0].end():]
    cab_a, corpo_a = _sem_cabecalho(a)
    cab_b, corpo_b = _sem_cabecalho(b)
    na, nb = _norm(corpo_a), _norm(corpo_b)
    if not na or not nb:
        return seg, False
    cab = [l for l in cab_a + cab_b if l.strip() and l.strip() != "Supremo Tribunal Federal"][:1]
    if na in nb:
        return "\n".join(cab + [corpo_b]), True
    if nb in na:
        return "\n".join(cab + [corpo_a]), True
    return seg, False


def extrair_texto_projeto(caminho: Path, avisos: list):
    bruto = caminho.read_text(encoding="utf-8").replace("\r\n", "\n")
    partes = RE_RODAPE_PAGINA.split(bruto)
    # partes = [txt_p1, n1, total, txt_p2, n2, total, ..., resto_final]
    paginas, dedup = [], 0
    for k in range(0, len(partes) - 1, 3):
        seg, n, total = partes[k], int(partes[k + 1]), int(partes[k + 2])
        seg, removeu = deduplicar_pagina(seg)
        dedup += removeu
        paginas.append({"pagina_pdf": n, "texto": seg.strip("\n") +
                        f"\nInteiro Teor do Acórdão - Página {n} de {total}\n",
                        "origem_texto": "texto_projeto", "total_declarado": total,
                        "dedup": removeu})
    sobra = partes[-1].strip()
    if sobra:
        avisos.append(f"{caminho.name}: {len(sobra.split())} palavras após o último rodapé (ignoradas)")
    numeros = [p["pagina_pdf"] for p in paginas]
    total = paginas[0]["total_declarado"] if paginas else 0
    if numeros != list(range(1, total + 1)):
        avisos.append(f"{caminho.name}: sequência de páginas incompleta ou fora de ordem")
    if dedup:
        avisos.append(f"{caminho.name}: duplicação de conversão removida em {dedup} páginas")
    return paginas


# ---------------------------------------------------------------------------
# Metadados por regra (campos que são só dado)
# ---------------------------------------------------------------------------
MESES = {m: i for i, m in enumerate(
    ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
     "agosto", "setembro", "outubro", "novembro", "dezembro"], start=1)}


def _limpa(s):
    return re.sub(r"\s+", " ", s or "").strip(" :")


def extrair_metadados(paginas):
    meta = {}

    def put(campo, valor, pag, regra):
        if valor and campo not in meta:
            meta[campo] = (_limpa(valor), pag, regra)

    p1 = paginas[0]["texto"] if paginas else ""
    p1u = re.sub(r"\s+", " ", p1)

    m = re.search(r"(\d{2}/\d{2}/\d{4})", p1u)
    put("data_julgamento", m and m.group(1), 1, "primeira data dd/mm/aaaa da página 1")
    m = re.search(r"(PLEN[ÁA]RIO|PRIMEIRA TURMA|SEGUNDA TURMA)", p1u)
    put("orgao_julgador", m and m.group(1), 1, "cabeçalho da página 1")
    m = re.search(r"RELATORA?\s*:\s*(MIN\.?\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ .]+?)(?=\s+(?:REDATOR|RECTE|REQTE|AGTE|AUTOR|RECDO|ADV|INTDO|REQDO|AGDO|EMENTA|REQUERENTE|RECORRENTE|AGRAVANTE|\())", p1u)
    put("relator", m and m.group(1), 1, "campo RELATOR(A) do cabeçalho")
    m = re.search(r"REDATORA?\s+DO\s+AC[ÓO]RD[ÃA]O\s*:\s*(MIN\.?\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ .]+?)(?=\s+(?:RECTE|REQTE|AGTE|AUTOR|RECDO|ADV|INTDO|REQDO|AGDO|EMENTA|REQUERENTE|RECORRENTE|AGRAVANTE|\())", p1u)
    put("redator_acordao", m and m.group(1), 1, "campo REDATOR DO ACÓRDÃO do cabeçalho")
    m = re.search(r"(A[ÇC][ÃA]O DIRETA DE INCONSTITUCIONALIDADE|A[ÇC][ÃA]O C[ÍI]VEL ORIGIN[ÁA]RIA|ARGUI[ÇC][ÃA]O DE DESCUMPRIMENTO DE PRECEITO FUNDAMENTAL|RECURSO EXTRAORDIN[ÁA]RIO)[^0-9]*([\d.]+)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ ]+?)(?=\s+(?:RELATOR|REGISTRADO))", p1u)
    if m:
        put("classe_extenso", m.group(1), 1, "título da página 1")
        put("numero_cabecalho", m.group(2).replace(".", ""), 1, "título da página 1")
        put("uf_origem", m.group(3), 1, "título da página 1")

    # Extrato de ata: última página que contém "EXTRATO DE ATA"
    pag_ata = None
    for p in reversed(paginas):
        if re.search(r"EXTRATO\s+DE\s+ATA", p["texto"], re.IGNORECASE):
            pag_ata = p
            break
    if pag_ata:
        put("pagina_extrato_ata", str(pag_ata["pagina_pdf"]), pag_ata["pagina_pdf"], "última página com 'EXTRATO DE ATA'")
        # texto da ata pode continuar na página seguinte
        idx = paginas.index(pag_ata)
        ata = " ".join(p["texto"] for p in paginas[idx: idx + 2])
        ata = re.sub(r"\s+", " ", ata)
        # A ata pode ter várias entradas "Decisão:" (sessões suspensas, pedidos
        # de vista). O resultado final é a ÚLTIMA; as anteriores ficam no histórico.
        entradas = re.findall(r"Decis[ãa]o\s*:\s*(.+?)(?=Decis[ãa]o\s*:|Presid[êe]ncia d|Presidiu o julgamento|Composi[çc][ãa]o\s*:|$)", ata)
        if entradas:
            put("resultado_extrato_ata", entradas[-1][:2000], pag_ata["pagina_pdf"], "última entrada 'Decisão:' do extrato de ata")
            if len(entradas) > 1:
                put("historico_extrato_ata", " || ".join(e[:600] for e in entradas[:-1]),
                    pag_ata["pagina_pdf"], "entradas 'Decisão:' anteriores à final")
        final = entradas[-1] if entradas else ata
        if re.search(r"[Ss]ess[ãa]o [Vv]irtual", final):
            put("meio_julgamento", "Sessão virtual", pag_ata["pagina_pdf"], "menção a 'Sessão Virtual' no extrato de ata")
        elif re.search(r"[Pp]len[áa]rio,|[Ss]ess[ãa]o (?:Ordin[áa]ria|Extraordin[áa]ria)|[Tt]urma,", final):
            put("meio_julgamento", "Sessão presencial", pag_ata["pagina_pdf"], "extrato de ata sem menção a sessão virtual")
        # Unanimidade x maioria: ata x acórdão (página 1-3)
        ata_res = (meta.get("resultado_extrato_ata") or ("",))[0].lower()
        acordao = " ".join(p["texto"] for p in paginas[:3]).lower()
        m_ac = re.search(r"acordam[^.]{0,400}?(por unanimidade|por maioria|unanimemente)", re.sub(r"\s+", " ", acordao))
        vot_ata = "unanimidade" if ("unanimidade" in ata_res or "unanime" in ata_res or "unânime" in ata_res) else ("maioria" if "maioria" in ata_res else None)
        vot_ac = None
        if m_ac:
            vot_ac = "maioria" if "maioria" in m_ac.group(1) else "unanimidade"
        put("votacao_extrato_ata", vot_ata, pag_ata["pagina_pdf"], "'unanimidade'/'maioria' no extrato de ata")
        put("votacao_acordao", vot_ac, 1, "'por unanimidade'/'por maioria' no texto do acórdão")
        if vot_ata and vot_ac and vot_ata != vot_ac:
            put("divergencia_acordao_ata",
                f"Acórdão registra '{vot_ac}', extrato de ata registra '{vot_ata}'. Prevalece a ata.",
                pag_ata["pagina_pdf"], "comparação acórdão x ata")
    return meta


# ---------------------------------------------------------------------------
# Gravação
# ---------------------------------------------------------------------------
def gravar(con, ident, arquivo, origem, hash_, paginas, agora):
    classe, numero, sufixo, id_decisao = ident
    apagar_decisao(con, id_decisao)
    n_ocr = sum(p["origem_texto"] == "ocr" for p in paginas)
    total_palavras = 0
    for p in paginas:
        n_pal = len(p["texto"].split())
        total_palavras += n_pal
        con.execute(
            "INSERT INTO paginas VALUES (?,?,?,?,?,?,?,?)",
            (id_decisao, p["pagina_pdf"], detectar_pagina_impressa(p["texto"]),
             detectar_peca(p["texto"]), p["texto"], p["origem_texto"], n_pal,
             int(p.get("dedup", False))))
    con.execute(
        "INSERT INTO decisoes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (id_decisao, arquivo, classe, numero, sufixo, len(paginas), n_ocr,
         int(n_ocr > 0), origem, hash_, total_palavras, agora, VERSAO_SCRIPT))
    meta = extrair_metadados(paginas)
    meta.setdefault("classe", (classe, None, "nome do arquivo"))
    meta.setdefault("numero", (numero, None, "nome do arquivo"))
    if sufixo:
        meta.setdefault("sufixo", (sufixo, None, "nome do arquivo"))
    for campo, (valor, pag, regra) in meta.items():
        con.execute("INSERT INTO metadados VALUES (?,?,?,?,?)",
                    (id_decisao, campo, valor, pag, regra))
    return len(paginas), n_ocr


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("pasta", type=Path, help="pasta com os PDFs das decisões")
    ap.add_argument("--textos", type=Path, default=None,
                    help="pasta com textos .txt do projeto (fonte provisória)")
    ap.add_argument("--db", type=Path, default=Path("decisoes.sqlite"))
    ap.add_argument("--dpi", type=int, default=300, help="resolução do OCR")
    args = ap.parse_args()

    avisos = []
    agora = dt.datetime.now().isoformat(timespec="seconds")

    # 1) Seleção dos arquivos de decisão
    fontes = {}  # id_decisao -> (ident, caminho, origem)
    for c in sorted(args.pasta.glob("*.pdf")):
        ident = identificar(c.name)
        if ident:
            fontes[ident[3]] = (ident, c, "pdf")
    if args.textos:
        for c in sorted(args.textos.glob("*.txt")):
            ident = identificar(c.name)
            if ident and ident[3] not in fontes:  # PDF sempre prevalece
                fontes[ident[3]] = (ident, c, "texto_projeto")

    if len(fontes) != N_ESPERADO:
        msg = f"ATENÇÃO: encontradas {len(fontes)} decisões; esperadas {N_ESPERADO}."
        print(msg, file=sys.stderr)
        avisos.append(msg)

    con = conectar(args.db)
    tot_pag = tot_ocr = 0
    for id_decisao, (ident, caminho, origem) in sorted(fontes.items()):
        if origem == "pdf":
            paginas = extrair_pdf(caminho, args.dpi, avisos)
        else:
            paginas = extrair_texto_projeto(caminho, avisos)
        n, n_ocr = gravar(con, ident, caminho.name, origem, sha256(caminho), paginas, agora)
        con.commit()
        tot_pag += n
        tot_ocr += n_ocr
        print(f"  {id_decisao:22s} {origem:14s} {n:4d} páginas  ({n_ocr} OCR)")

    # Remove do banco decisões cujo arquivo não está mais na pasta
    ids_banco = {r[0] for r in con.execute("SELECT id_decisao FROM decisoes")}
    for orfao in ids_banco - set(fontes):
        apagar_decisao(con, orfao)
        avisos.append(f"{orfao}: removida do banco (arquivo ausente)")

    con.execute("INSERT INTO execucoes VALUES (?,?,?,?,?,?,?,?)",
                (agora, VERSAO_SCRIPT, str(args.pasta), str(args.textos),
                 len(fontes), tot_pag, tot_ocr, "\n".join(avisos)))
    con.commit()
    con.close()

    print("\nRESUMO")
    print(f"  decisões:          {len(fontes)}")
    print(f"  páginas:           {tot_pag}")
    print(f"  páginas com OCR:   {tot_ocr}")
    print(f"  banco:             {args.db}")
    if avisos:
        print("\nAVISOS")
        for a in avisos:
            print("  -", a)


if __name__ == "__main__":
    main()
