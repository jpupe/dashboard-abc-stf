#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_dicionario_xlsx.py — Gera o output 3 (dicionario_dados_banco_ABC.xlsx)
a partir de dicionario_campos.json (gerado por 02_dicionario.py).

Abas: Leia-me | Dicionário | Regras 7.4 | Marcadores
Uso:  python 03_dicionario_xlsx.py [dicionario_campos.json] [saida.xlsx]
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

sys.path.insert(0, str(Path(__file__).parent))
from estilo_abc import AMARELO_VALIDACAO, FONTE, cab, cor_do_campo, corpo  # noqa: E402

ENTRADA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dicionario_campos.json")
SAIDA = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dicionario_dados_banco_ABC.xlsx")

d = json.loads(ENTRADA.read_text(encoding="utf-8"))
campos, marcadores, colunas_banco = d["catalogo"], d["marcadores"], d["colunas_banco"]

wb = Workbook()

# ------------------------------------------------------------------ Leia-me
ws = wb.active
ws.title = "Leia-me"
linhas = [
    ("Banco A/B/C das decisões do STF em direito minerário — Dicionário de dados", "titulo"),
    ("Pré-preenchimento assistido por IA. TODAS AS CLASSIFICAÇÕES SÃO PROVISÓRIAS até a validação da pesquisadora (Suzy Sousa, UFPA).", "alerta"),
    ("", ""),
    ("O que é este arquivo", "sub"),
    ("Descreve o banco (banco_ABC_STF_mineracao.xlsx), que tem uma planilha única em formato longo: cada linha é UMA RESPOSTA a uma pergunta do 'Instrumento de análise dos núcleos decisórios e de classificação pelo índice A/B/C', versão 5.0. A aba 'Colunas do banco' descreve as colunas, na mesma ordem do banco. A aba 'Catálogo de perguntas' lista todas as perguntas do questionário, com código (ID_pergunta), grupo, categorias permitidas e regra de entrada.", ""),
    ("Unidade da linha do banco", "sub"),
    ("Uma linha por decisão × núcleo × pergunta. As perguntas das seções 1–4, 13, 14 e 16 e o controle documental aparecem uma vez por decisão (Nível = decisão). As das seções 5–12 e 15 aparecem uma vez por núcleo elegível (Nível = núcleo). Decisões sem núcleo elegível (regra de parada) têm as linhas da decisão e uma única linha 'Análise substantiva (seções 5 a 12) = Não aplicável'. Para filtrar: use as colunas Decisão, Núcleo, Grupo da pergunta, Princípio, Pergunta do questionário e Resposta.", ""),
    ("Campos que acompanham cada classificação", "sub"),
    ("Evidência textual, localização e autoria, justificativa, categoria alternativa e segurança não viram linhas próprias: ficam nas colunas Trecho, Página PDF, Página impressa, Autoria e plano, Justificativa, Categoria alternativa e razão e Segurança da linha da classificação. A coluna 'Campos absorvidos' do catálogo indica, para cada pergunta, quais campos do questionário estão nessas colunas. Assim nenhum campo do instrumento se perde.", ""),
    ("Como ler os códigos das perguntas (ID_pergunta)", "sub"),
    ("S01_…S16_ = seção do questionário. IN_ = Interesse nacional (art. 176, § 1º); FSP_ = Função social da propriedade (art. 170, III); MA_ = Meio ambiente ecologicamente equilibrado (art. 225). Dentro de cada princípio: _B_ = Dimensão B (posição na fundamentação, 7.x.1); _C_ = Dimensão C (densificação, 7.x.2); _AT_ = atribuição normativa e contrafactual (7.x.3); _CN_ = concretização normativa (7.x.4); _FS_ = indicadores de função simbólica (seção 8); _ALT_H01…H10_ = explicações alternativas (seção 9, uma hipótese por número, na ordem do instrumento); _AUS_ = ausências e não mobilização (seção 10).", ""),
    ("Tabelas de tamanho variável", "sub"),
    ("Mapa de núcleos (S04_N_…), categorias jurídicas prevalentes (S10_CAT_…) e registros de controle da seção 15 (S15_K_…) têm uma linha por entrada existente; a coluna Item indica o número da entrada. Não há limite de entradas.", ""),
    ("Evidências", "sub"),
    ("O trecho literal fica na coluna 'Trecho (evidência literal)' e a página na coluna 'Página PDF' (página do arquivo da decisão). Vários trechos na mesma célula são separados por ' || ', com as páginas na mesma ordem. A página impressa é lida automaticamente do banco decisoes.sqlite. Todo trecho é conferido por script contra o texto extraído; o resultado fica na coluna 'Conferência automática' (células alaranjadas indicam algo a conferir).", ""),
    ("Origem da resposta", "sub"),
    ("'LLM' = leitura interpretativa; 'extração automática' = metadado lido por regra do PDF; 'regra de salto' = 'Não aplicável' aplicado pelo script por regra expressa do instrumento (ex.: densificação quando o princípio está ausente, seção 9 quando a entrada da seção 8 é negativa); 'script (síntese)' = síntese da seção 12 copiada do bloco de origem; 'pendência' = campo aplicável ainda não preenchido.", ""),
    ("Respostas múltiplas", "sub"),
    ("Categorias separadas por ' ; '. Quando a categoria é 'outro: …' ou 'outra: …', a descrição vem depois dos dois-pontos.", ""),
    ("Cores dos cabeçalhos (as mesmas do piloto)", "sub"),
    ("A célula da coluna Seção é colorida pelo grupo da pergunta. Azul-escuro: identificação da decisão (seções 1–4). Azul: núcleo e Dimensão A (seções 5–6). Dourado: Interesse nacional. Marrom: Função social da propriedade. Verde: Meio ambiente. Cinza: categorias prevalentes, implementação e sínteses (10.1–14). Roxo: controle e auditoria (15–16). Cinza médio: controle documental. Amarelo: validação da pesquisadora.", ""),
    ("Colunas de validação (amarelas, no fim de cada linha)", "sub"),
    ("'Concorda?' (sim / não / parcialmente), 'Correções' (novo valor proposto) e 'Comentário', em cada linha, ou seja, em cada resposta. Ficam vazias até a revisão da pesquisadora. O banco é regerado por script depois das correções.", ""),
    ("Marcadores de dados", "sub"),
    ("Ver aba Marcadores. Campo aplicável nunca fica vazio para representar falta de informação ou pendência.", ""),
    ("Origem dos campos", "sub"),
    ("'extração automática' = lido por regra do PDF pelo script 01_extrair_pdfs.py; 'LLM' = preenchido na leitura interpretativa (Claude Opus 5.5) segundo o capítulo de regras e o questionário; 'validação da pesquisadora' = preenchido por ela.", ""),
]
ws.column_dimensions["A"].width = 130
for i, (txt, tipo) in enumerate(linhas, start=1):
    c = ws.cell(row=i, column=1, value=txt)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    if tipo == "titulo":
        c.font = Font(name=FONTE, bold=True, size=14, color="1F3864")
    elif tipo == "alerta":
        c.font = Font(name=FONTE, bold=True, size=10, color="9C0006")
        c.fill = PatternFill("solid", fgColor="FFC7CE")
    elif tipo == "sub":
        c.font = Font(name=FONTE, bold=True, size=10, color="1F3864")
    else:
        c.font = Font(name=FONTE, size=10)

# ---------------------------------------------------------- Colunas do banco
ws = wb.create_sheet("Colunas do banco")
for j, (t, larg) in enumerate([("Ordem", 7), ("Coluna do banco", 30), ("Descrição", 90), ("Origem", 26)], start=1):
    cab(ws.cell(row=1, column=j, value=t), "1F3864")
    ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = larg
for i, c in enumerate(colunas_banco, start=2):
    for j, v in enumerate([i - 1, c["coluna"], c["descricao"], c["origem"]], start=1):
        corpo(ws.cell(row=i, column=j, value=v), tamanho=10)
    if c["coluna"] in ("Concorda?", "Correções", "Comentário"):
        ws.cell(row=i, column=2).fill = PatternFill("solid", fgColor=AMARELO_VALIDACAO)
ws.freeze_panes = "A2"

# ------------------------------------------------------ Catálogo de perguntas
ws = wb.create_sheet("Catálogo de perguntas")
cols = [("ordem", "Ordem", 7), ("id_pergunta", "ID_pergunta", 30), ("secao", "Seção", 8),
        ("bloco", "Grupo da pergunta", 30), ("descricao", "Pergunta do questionário", 55),
        ("nivel", "Nível", 9), ("principio", "Princípio", 18), ("tabela_variavel", "Tabela variável", 14),
        ("tipo", "Tipo", 12), ("resposta", "Resposta", 9), ("categorias", "Categorias permitidas", 48),
        ("regra_entrada", "Regra de entrada / aplicabilidade", 48), ("absorve", "Campos absorvidos nas colunas da linha", 48),
        ("origem", "Origem", 18), ("exemplo", "Exemplo", 28)]
for j, (_, titulo, larg) in enumerate(cols, start=1):
    cab(ws.cell(row=1, column=j, value=titulo), "1F3864")
    ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = larg
for i, c in enumerate(campos, start=2):
    for j, (k, _, _) in enumerate(cols, start=1):
        corpo(ws.cell(row=i, column=j, value=c.get(k) or None))
    nm = ws.cell(row=i, column=2)
    nm.font = Font(name=FONTE, size=9, bold=True, color="FFFFFF")
    nm.fill = PatternFill("solid", fgColor=cor_do_campo(c))
ws.freeze_panes = "C2"
ws.auto_filter.ref = ws.dimensions

# ---------------------------------------------------------------- Regras 7.4
ws = wb.create_sheet("Regras 7.4")
regras = [
    ("Princípio ausente ou presente somente em peça não judicial", "Ausente ou Presença documental não judicial; Não aplicável para densificação; Atribuição de critério não demonstrada. Registrar a ausência de mobilização judicial.", "Não mobilizado"),
    ("Princípio presente apenas em voto não prevalecente", "Voto não prevalecente; Conteúdo não densificado ou Densificação no caso/corrente no voto/corrente (esta exige Contribuição própria ou compartilhada). Densificação institucional não é admissível.", "Presença contextual/discursiva no plano institucional; preservar densificação e atribuição do voto"),
    ("Presença judicial genérica ou ornamental", "Genérica/ornamental; 'Não mobilizado' não é admissível nesse plano. Se houver densificação demonstrada, reexaminar a posição.", "Presença contextual/discursiva"),
    ("Presença judicial relevante sem participação determinante", "Relevante sem participação determinante; 'Não mobilizado' não é admissível. Registrar densificação e atribuição conforme a evidência.", "Presença contextual/discursiva"),
    ("Obstáculo que impediu a mobilização judicial", "Obstáculo processual/institucional; documentar obstáculo e ausência de mobilização; Não aplicável para densificação quando estruturalmente inaplicável; Atribuição de critério não demonstrada.", "Não mobilizado"),
    ("Mobilização judicial com exame substantivo obstado", "Obstáculo processual/institucional; demonstrar presença judicial e limitação; distinguir Não aplicável de Conteúdo não densificado.", "Presença contextual/discursiva"),
    ("Fundamento determinante sem densificação", "Fundamento determinante + Conteúdo não densificado + Atribuição de critério não demonstrada. Não admitir Presença contextual nessa combinação no mesmo segmento.", "Fundamento determinante sem densificação"),
    ("Concretização no caso", "Fundamento determinante + Densificação no caso/corrente + Contribuição própria ou compartilhada, com plano e evidências.", "Concretização no caso"),
    ("Concretização institucional", "Fundamento determinante + Densificação institucional com critério potencialmente replicável + Contribuição própria ou compartilhada; exigir incorporação institucional e potencial de orientação.", "Concretização institucional com critério potencialmente replicável"),
    ("Evidência analiticamente insuficiente", "Após exame, a documentação não permite decidir. Identificar insuficiência e alternativas.", "Inconclusivo"),
    ("Combinação incompatível ou não prevista", "Registrar alerta e revisão dirigida (seção 15). Preservar categoria provisória e marcar 'Registro provisório pendente de conferência'. Lacuna da tabela não equivale a insuficiência documental.", "Não atribuir Inconclusivo automaticamente"),
]
for j, (t, larg) in enumerate([("Situação documentada", 40), ("Combinação e condição", 80), ("Concretização normativa", 40)], start=1):
    cab(ws.cell(row=1, column=j, value=t), "404040")
    ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = larg
for i, r in enumerate(regras, start=2):
    for j, v in enumerate(r, start=1):
        corpo(ws.cell(row=i, column=j, value=v), tamanho=10)
ws.freeze_panes = "A2"

# ---------------------------------------------------------------- Marcadores
ws = wb.create_sheet("Marcadores")
regra_m = [
    "Não aplicável em razão da estrutura do instrumento ou de regra de salto. Exige justificativa quando a inaplicabilidade não for evidente.",
    "Informação não disponível ou não localizada no material examinado. Registrar a fonte ou o limite documental.",
    "Evidência examinada, mas insuficiente para decidir entre categorias. Não equivale a campo não preenchido.",
    "Campo aplicável ainda não preenchido. Representa pendência de completude.",
    "Categoria ou registro provisório pendente de conferência.",
]
for j, (t, larg) in enumerate([("Marcador", 45), ("Regra de uso", 100)], start=1):
    cab(ws.cell(row=1, column=j, value=t), "404040")
    ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = larg
for i, (m, r) in enumerate(zip(marcadores + ["Célula vazia"], regra_m + ["Admitida somente em linha não utilizada, campo livre opcional ou campo estruturalmente desativado. Não representa resposta analítica."]), start=2):
    corpo(ws.cell(row=i, column=1, value=m), tamanho=10)
    corpo(ws.cell(row=i, column=2, value=r), tamanho=10)

wb.save(SAIDA)
print(f"{SAIDA}: {len(colunas_banco)} colunas do banco, {len(campos)} perguntas no catálogo")
