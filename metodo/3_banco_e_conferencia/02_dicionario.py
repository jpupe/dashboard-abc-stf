#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_dicionario.py — Dicionário de campos do banco A/B/C (Passo 2 / output 3)

Transcreve o "Instrumento de análise dos núcleos decisórios e de classificação
pelo índice A/B/C" (versão 5.0) em uma lista ordenada de colunas. Cada coluna
do Excel final (output 2) corresponde a exatamente uma linha deste dicionário.

Convenções:
  - Prefixos por seção: ID_, CTRL_ (controle), S01_..S06_, IN_/FSP_/MA_ (blocos
    por princípio: 7.x, 8, 9 e 10), S11_, S12_, S13_, S14_, S15_K{n}_, S16_, VAL_.
  - Campos da decisão (seções 1–4, 13, 14 e 16) se repetem em todas as linhas
    de núcleo da mesma decisão (nível = "decisão").
  - Tabelas de tamanho variável viram colunas numeradas: mapa de núcleos
    (S04_N{k}_), categorias jurídicas prevalentes (S10_CAT{k}_) e registros de
    controle da seção 15 (S15_K{k}_). O máximo vigente fica em MAXIMOS e é
    registrado no dicionário; se algum caso passar dele, aumenta-se o máximo.
  - A seção 9 (explicações alternativas) tem lista fechada de 10 hipóteses no
    instrumento; por isso vira colunas fixas por princípio e hipótese
    (IN_ALT_H01_...), e não colunas numeradas genéricas.
  - Evidências: o trecho literal vem entre « » seguido da localização,
    ex.: «texto do acórdão» (p. PDF 12; p. impr. 9; Voto – Min. Fachin).
    Vários trechos na mesma célula são separados por " || ".
  - Resposta múltipla: categorias separadas por " ; ".

Uso:  python 02_dicionario.py  -> gera dicionario_campos.json
"""
import json
from pathlib import Path

MAXIMOS = {"mapa_nucleos": 5, "categorias_prevalentes": 5, "controles_s15": 6}

# ---------------------------------------------------------------- categorias
MARCADORES = ["Não aplicável", "Informação não disponível ou não localizada",
              "Inconclusivo — evidência examinada insuficiente",
              "Campo aplicável ainda não preenchido",
              "Registro provisório pendente de conferência"]
SIM_NAO = ["sim", "não"]
SEG = ["alta", "média", "baixa", "inconclusiva"]
POSICAO = ["Ausente", "Presença documental não judicial", "Voto não prevalecente",
           "Genérica/ornamental", "Relevante sem participação determinante",
           "Obstáculo processual/institucional", "Fundamento determinante", "Inconclusivo"]
MOBIL = ["literal", "conteúdo equivalente demonstrado", "não mobilizado"]
DENS = ["Não aplicável", "Conteúdo não densificado", "Densificação no caso/corrente",
        "Densificação institucional com critério potencialmente replicável", "Inconclusivo"]
ALCANCE = ["apenas o caso", "casos semelhantes", "cumprimento/controle", "indeterminado"]
SIT_CRIT = ["critério identificado", "critério não demonstrado após exame suficiente",
            "insuficiência documental"]
ATRIB = ["Contribuição própria ao critério", "Contribuição compartilhada", "Presença contextual",
         "Atribuição de critério não demonstrada", "Inconclusivo"]
NAO_SIM_INC_NA = ["não", "sim", "inconclusivo", "Não aplicável — justificar"]
SIM_NAO_INC_NA = ["sim", "não", "inconclusivo", "Não aplicável — justificar"]
CONCR = ["Não mobilizado", "Presença contextual/discursiva",
         "Fundamento determinante sem densificação", "Concretização no caso",
         "Concretização institucional com critério potencialmente replicável", "Inconclusivo"]
FS = ["Não aplicável", "Sem indicador suficiente", "Indícios",
      "Função simbólica demonstrada", "Inconclusivo"]
RESOL = ["Sem resolução operativa", "Com resolução operativa", "Não classificável"]
HIPOTESES = ["Princípio irrelevante à questão", "Regra mais específica aplicável",
             "Obstáculo processual/institucional", "Ausência de maioria ou quórum",
             "Decisão provisória/cautelar", "Dependência de prova indisponível",
             "Contribuição compartilhada com outra norma", "Linguagem de voto individual/vencido",
             "Limitação do recorte documental", "Estilo retórico sem função demonstrável"]
DEC_HIP = ["aceita", "aceita parcialmente", "rejeitada",
           "Inconclusivo — evidência examinada insuficiente"]
PRINCIPIOS = [("IN", "Interesse nacional", "art. 176, § 1º", "7.1"),
              ("FSP", "Função social da propriedade", "art. 170, III", "7.2"),
              ("MA", "Meio ambiente ecologicamente equilibrado", "art. 225", "7.3")]

CAMPOS = []


def add(nome, secao, bloco, descricao, nivel, tipo, categorias=None, resposta="",
        regra="", origem="LLM", principio="", exemplo="", plano=""):
    CAMPOS.append(dict(
        coluna=nome, ordem=len(CAMPOS) + 1, secao=secao, bloco=bloco, descricao=descricao,
        nivel=nivel, principio=principio, plano=plano, tipo=tipo,
        resposta=resposta or ("única" if tipo == "categoria" else ""),
        categorias=" | ".join(categorias) if categorias else "",
        regra_entrada=regra, origem=origem, exemplo=exemplo))


D, N = "decisão", "núcleo"
TXT, CAT, EVID, ID, MARC = "texto livre", "categoria", "evidência", "identificador", "marcador"

# ------------------------------------------------------------ identificação
add("ID_decisao", "ID", "Identificação da linha", "Identificador estável da decisão (classe_número_sufixo), igual ao do banco SQLite.", D, ID, origem="extração automática", exemplo="ADI_7273_MC-Ref")
add("ID_nucleo", "ID", "Identificação da linha", "Identificador do núcleo (ID_decisao + _N + número). Em decisão sem núcleo elegível: ID_decisao + _N0.", N, ID, origem="LLM", exemplo="ADI_3355_N1")
add("ID_decisao_rotulo", "ID", "Identificação da linha", "Nome da decisão por extenso abreviado.", D, ID, origem="extração automática", exemplo="ADI 7273 MC-Ref")
add("ID_nucleo_n", "ID", "Identificação da linha", "Número do núcleo elegível no mapa da seção 4 (0 = decisão sem núcleo elegível).", N, ID, origem="LLM", exemplo="1")
add("ID_tipo_linha", "ID", "Identificação da linha", "Tipo de linha.", N, CAT, ["núcleo elegível", "decisão sem núcleo elegível (regra de parada)"], origem="LLM")

# ---------------------------------------------------------------- controle
add("CTRL_fonte_texto", "Controle", "Controle documental", "Origem do texto usado na codificação (tabela decisoes do SQLite).", D, CAT, ["pdf", "texto_projeto"], origem="extração automática", exemplo="pdf")
add("CTRL_paginas_total", "Controle", "Controle documental", "Total de páginas da decisão no banco.", D, "dado", origem="extração automática")
add("CTRL_paginas_ocr", "Controle", "Controle documental", "Páginas cujo texto veio de OCR.", D, "dado", origem="extração automática")
add("CTRL_inconsistencias", "Controle", "Controle documental", "Inconsistências materiais do acórdão (erro de lei, parágrafos trocados, acórdão × ata). Registradas sem corrigir o texto.", D, TXT, origem="LLM + extração automática", exemplo="Acórdão diz 'por maioria'; ata registra unanimidade (p. 28). Prevalece a ata.")
add("CTRL_dependencias", "Controle", "Controle documental", "Dependências com outras decisões do conjunto (aplicação integral de precedente, cautelar × mérito).", D, TXT, origem="LLM", exemplo="Aplica integralmente a ADI 4606.")
add("CTRL_inclusao", "Controle", "Controle documental", "Registro sobre a inclusão da decisão no conjunto (ex.: incluída pela pesquisadora na revisão).", D, TXT, origem="LLM")
add("CTRL_pendencias_metodologicas", "Controle", "Controle documental", "Tensões ou lacunas entre capítulo de regras e questionário que afetam esta decisão, registradas para a pesquisadora (não resolvidas por regra nova).", D, TXT, origem="LLM")
add("CTRL_partes_processadas", "Controle", "Controle documental", "Para decisões longas: partes (blocos de páginas/votos) em que a leitura foi feita.", D, TXT, origem="LLM", exemplo="Parte 1: pp. 1–60 (ementa, relatório, voto do relator)...")
add("CTRL_conferencia_automatica", "Controle", "Controle documental", "Resultado da conferência automática (trechos, compatibilidade, completude, domínio).", N, TXT, origem="script de conferência", exemplo="trechos 42/42 ok; 0 alertas de compatibilidade")
add("CTRL_versao_codificacao", "Controle", "Controle documental", "Versão e data do pré-preenchimento (modelo e rodada).", D, TXT, origem="LLM", exemplo="v1 — Claude Opus 5.5 — 21/11/2026")

# ---------------------------------------------------------------- seção 1
s = "1 Identificação da decisão"
add("S01_classe_numero", "1", s, "Classe e número", D, "dado", origem="extração automática + LLM")
add("S01_orgao_julgador", "1", s, "Órgão julgador", D, "dado", origem="extração automática + LLM")
add("S01_relator_originario", "1", s, "Relator(a) originário(a)", D, "dado", origem="extração automática + LLM")
add("S01_redator_acordao", "1", s, "Redator(a) do acórdão", D, "dado", origem="extração automática + LLM", regra="Não aplicável se não houver redator designado.")
add("S01_datas_julgamento", "1", s, "Data(s) do julgamento e data final", D, "dado", origem="extração automática + LLM")
add("S01_tipo_decisao", "1", s, "Tipo de decisão", D, CAT, ["acórdão", "cautelar", "mérito", "monocrática", "outra: …"], "múltipla", regra="Resposta múltipla quando coexistirem qualificações distintas.")
add("S01_objeto", "1", s, "Objeto", D, TXT)
add("S01_resultado_proclamado", "1", s, "Resultado proclamado", D, TXT, origem="extração automática (ata) + LLM", regra="Se acórdão e ata divergirem, prevalece a ata; registrar em CTRL_inconsistencias.")
add("S01_meio_julgamento", "1", s, "Meio de julgamento", D, CAT, ["presencial", "virtual", "outra: …"], origem="extração automática + LLM")
add("S01_pecas_examinadas", "1", s, "Peças examinadas", D, TXT)
add("S01_acesso_inteiro_teor", "1", s, "Acesso ao inteiro teor", D, TXT)
add("S01_acompanhamento_processual", "1", s, "Acompanhamento processual", D, TXT, regra="Fonte é o PDF; sem consulta externa (marcador 'Informação não disponível ou não localizada' quando não constar).")
add("S01_formacao_maioria_resultado", "1", s, "Formação da maioria quanto ao resultado", D, TXT)
add("S01_quorum", "1", s, "Quórum constitucional pertinente e atendimento", D, TXT)
add("S01_fundamentacao", "1", s, "Fundamentação", D, CAT, ["não fragmentada", "parcialmente fragmentada", "substancialmente fragmentada", "não verificável"])
add("S01_suficiencia_documental", "1", s, "Suficiência documental para reconstruir a decisão institucional", D, CAT, ["sim", "parcial", "não"])

# ---------------------------------------------------------------- seção 2
s = "2 Triagem, elegibilidade e delimitação minerária"
add("S02_conexao_substantiva", "2", s, "Conexão substantiva com o direito minerário (nexo entre objeto minerário e controvérsia).", D, TXT)
add("S02_objeto_minerario", "2", s, "Objeto minerário identificado", D, CAT, ["extração", "recurso/substância mineral", "cadeia produtiva", "impacto direto", "tributação/compensação", "servidão/propriedade", "licenciamento", "garimpo", "outro: …"], "múltipla")
add("S02_centralidade", "2", s, "Centralidade da mineração", D, CAT, ["central", "secundária", "contextual"])
add("S02_conteudo_decisao", "2", s, "Conteúdo da decisão", D, CAT, ["substantivo", "processual com consequência relevante", "exclusivamente processual"])
add("S02_caso_limitrofe", "2", s, "Caso limítrofe?", D, CAT, SIM_NAO)
add("S02_caso_limitrofe_justificativa", "2", s, "Caso limítrofe — justificar", D, TXT, regra="Não aplicável se S02_caso_limitrofe = não.")
add("S02_justificativa_inclusao", "2", s, "Justificativa de inclusão/exclusão", D, TXT)
add("S02_limites_material", "2", s, "Limites do material disponível", D, TXT)

# ---------------------------------------------------------------- seção 3
s = "3 Reconstrução da decisão institucional"
add("S03_resultado_proclamado", "3", s, "Resultado proclamado (reconstrução)", D, TXT)
add("S03_fundamentos_relator", "3", s, "Fundamentos do(a) relator(a)", D, EVID)
add("S03_correntes", "3", s, "Correntes identificadas e respectivos fundamentos", D, EVID)
add("S03_adesoes_ressalvas", "3", s, "Adesões, ressalvas e divergências", D, EVID)
add("S03_razoes_convergentes", "3", s, "Razões convergentes suficientes", D, TXT)
add("S03_maioria_fundamento", "3", s, "Maioria quanto ao fundamento", D, CAT, ["identificável", "parcial", "não identificável"], regra="Razões adicionais de um voto rejeitadas por outro ministro tornam a maioria 'parcial' (calibração ADI 3355).")
add("S03_maioria_res_dif_fund", "3", s, "Maioria quanto ao resultado ≠ maioria quanto ao fundamento?", D, CAT, SIM_NAO)
add("S03_maioria_res_dif_fund_explicar", "3", s, "Maioria resultado ≠ fundamento — explicar", D, TXT, regra="Não aplicável se a resposta for não.")
add("S03_efeito_quorum", "3", s, "Efeito do quórum sobre o mérito e a eficácia", D, TXT)
add("S03_separar_nucleos", "3", s, "Necessidade de separar núcleo substantivo e núcleo processual", D, CAT, SIM_NAO)
add("S03_separar_nucleos_explicar", "3", s, "Separar núcleos — explicar", D, TXT, regra="Não aplicável se a resposta for não.")
add("S03_repercussao_fragmentacao", "3", s, "Repercussão da fragmentação na codificação", D, TXT)

# ---------------------------------------------------------------- seção 4
s = "4 Mapa dos núcleos decisórios"
add("S04_total_nucleos", "4", s, "Total de núcleos identificados no mapa", D, "dado")
add("S04_total_elegiveis", "4", s, "Total de núcleos elegíveis", D, "dado")
for k in range(1, MAXIMOS["mapa_nucleos"] + 1):
    r = "Célula vazia se a decisão tiver menos núcleos que este número (linha não utilizada)."
    add(f"S04_N{k}_questao", "4", s, f"Núcleo {k} — questão jurídica", D, TXT, regra=r)
    add(f"S04_N{k}_regra_comando", "4", s, f"Núcleo {k} — regra/comando", D, TXT, regra=r)
    add(f"S04_N{k}_consequencia", "4", s, f"Núcleo {k} — consequência", D, TXT, regra=r)
    add(f"S04_N{k}_elegivel", "4", s, f"Núcleo {k} — elegível?", D, CAT, SIM_NAO, regra=r + " Exige os quatro requisitos cumulativos (problema, fundamentação, resposta e consequência próprios) e conexão substantiva com o direito minerário.")
    add(f"S04_N{k}_justificativa", "4", s, f"Núcleo {k} — justificativa da separação/elegibilidade; se não elegível, requisito não demonstrado", D, TXT, regra=r)
    add(f"S04_N{k}_evidencia", "4", s, f"Núcleo {k} — evidência e localização", D, EVID, regra=r)

# ---------------------------------------------------------------- seção 5
s = "5 Identificação do núcleo"
add("S05_numero_titulo", "5", s, "Número e título", N, TXT)
add("S05_questao_juridica", "5", s, "Questão jurídica", N, TXT)
add("S05_pretensao", "5", s, "Pretensão ou controvérsia", N, TXT)
add("S05_posicao_institucional", "5", s, "Posição institucional identificável", N, TXT)
add("S05_regra_central", "5", s, "Regra ou comando central", N, TXT)
add("S05_consequencia", "5", s, "Consequência jurídica própria", N, TXT)
add("S05_autonomia_problema", "5", s, "Autonomia — problema próprio", N, TXT)
add("S05_autonomia_fundamentacao", "5", s, "Autonomia — fundamentação própria", N, TXT)
add("S05_autonomia_resposta", "5", s, "Autonomia — resposta própria", N, TXT)
add("S05_autonomia_consequencia", "5", s, "Autonomia — consequência própria", N, TXT)
add("S05_nao_fundir", "5", s, "Por que não deve ser fundido ou fragmentado?", N, TXT)
add("S05_macrocampos", "5", s, "Macrocampos", N, CAT, ["controle ambiental/proteção territorial", "riscos ambientais/sanitários/ocupacionais", "organização federativa/controle institucional", "regulação econômico-fiscal", "ilicitude/responsabilização/reparação", "outro: …"], "múltipla")
add("S05_marcadores_auxiliares", "5", s, "Marcadores auxiliares", N, CAT, ["base técnico-probatória", "infraestrutura/logística", "direitos indígenas/comunidades", "consulta/participação", "vulnerabilidade", "outro: …"], "múltipla")
add("S05_fundamentacao_nucleo", "5", s, "Fundamentação no núcleo", N, CAT, ["não fragmentada", "parcial", "substancial", "não verificável"])

# ---------------------------------------------------------------- seção 6
s = "6 Dimensão A — Resolução operativa"
add("S06_resolucao_operativa", "6", s, "Resolução operativa", N, CAT, RESOL)
add("S06_posicao_juridica", "6", s, "Posição jurídica criada, mantida, restringida ou extinta", N, TXT)
add("S06_comando", "6", s, "Comando/consequência", N, TXT)
add("S06_destinatario", "6", s, "Destinatário", N, TXT)
add("S06_prazo_modulacao", "6", s, "Prazo, condição ou modulação", N, TXT)
add("S06_mecanismo", "6", s, "Mecanismo de cumprimento ou controle", N, TXT)
add("S06_evidencia", "6", s, "Evidência textual", N, EVID)
add("S06_localizacao_autoria", "6", s, "Localização, autoria e posição institucional", N, TXT)
add("S06_justificativa", "6", s, "Justificativa da classificação", N, TXT)
add("S06_alternativa", "6", s, "Categoria alternativa considerada e razão da rejeição", N, TXT, regra="Obrigatória em caso limítrofe, segurança baixa/inconclusiva ou impacto possível na síntese.")
add("S06_implementacao_documentada", "6", s, "Implementação documentada no acórdão?", N, CAT, ["sim", "não", "inconclusivo"])
add("S06_info_adicional", "6", s, "Informação adicional necessária", N, TXT)
add("S06_seguranca", "6", s, "Segurança", N, CAT, SEG)


# ------------------------------------------------- blocos por princípio
def bloco_principio(px, nome, art, sec, parte):
    p = nome
    if parte != "7":
        return _bloco_8_9_10(px, nome, sec, parte)
    s1 = f"{sec}.1 {nome} — Dimensão B (posição na fundamentação)"
    add(f"{px}_B_posicao", f"{sec}.1", s1, "Posição do princípio na fundamentação", N, CAT, POSICAO, principio=p)
    add(f"{px}_B_plano_voto", f"{sec}.1", s1, "Plano de referência e voto/corrente examinado", N, TXT, principio=p, plano="voto | corrente | núcleo | decisão")
    add(f"{px}_B_forma_mobilizacao", f"{sec}.1", s1, "Forma de mobilização", N, CAT, MOBIL, "múltipla", principio=p, regra="Genérica/ornamental e Relevante sem participação determinante não autorizam 'não mobilizado' quando houver mobilização judicial no plano.")
    add(f"{px}_B_evidencia", f"{sec}.1", s1, "Evidência da posição do princípio na fundamentação", N, EVID, principio=p)
    add(f"{px}_B_localizacao_autoria", f"{sec}.1", s1, "Localização e autoria", N, TXT, principio=p)
    add(f"{px}_B_posicao_voto_decisao", f"{sec}.1", s1, "Posição do voto/fundamento na decisão", N, TXT, principio=p)
    add(f"{px}_B_conexao", f"{sec}.1", s1, "Conexão com fatos, normas e conclusão", N, TXT, principio=p)
    add(f"{px}_B_mobilizacao_obstaculo", f"{sec}.1", s1, "Mobilização judicial e eventual obstáculo processual/institucional (distinguir mobilização pelo julgador de reprodução de alegação)", N, TXT, principio=p)
    add(f"{px}_B_justificativa", f"{sec}.1", s1, "Justificativa da classificação", N, TXT, principio=p)
    add(f"{px}_B_alternativa", f"{sec}.1", s1, "Categoria alternativa considerada e razão da rejeição", N, TXT, principio=p)

    s2 = f"{sec}.2 {nome} — Dimensão C (densificação normativa)"
    na = "Não aplicável quando a posição for Ausente ou Presença documental não judicial (7.4)."
    add(f"{px}_C_densificacao", f"{sec}.2", s2, "Densificação normativa", N, CAT, DENS, principio=p, regra="Ausente ou Presença documental não judicial exigem 'Não aplicável'. Voto não prevalecente nunca admite Densificação institucional. Densificações exigem Contribuição própria ou compartilhada.")
    add(f"{px}_C_plano_segmento", f"{sec}.2", s2, "Plano da densificação e segmento examinado", N, TXT, principio=p, regra=na)
    add(f"{px}_C_conteudo_extraido", f"{sec}.2", s2, f"Conteúdo normativo extraído: 'Do princípio {nome}, [voto/corrente/decisão] extraiu o critério segundo o qual: …'", N, TXT, principio=p, regra=na)
    add(f"{px}_C_criterio", f"{sec}.2", s2, "Critério, dever, limite ou parâmetro", N, TXT, principio=p, regra=na)
    add(f"{px}_C_alcance", f"{sec}.2", s2, "Alcance", N, CAT, ALCANCE, "múltipla", principio=p, regra=na)
    add(f"{px}_C_incorporacao", f"{sec}.2", s2, "Grau de incorporação institucional (adesão ao critério; potencial futuro não comprova incorporação)", N, TXT, principio=p, regra=na)
    add(f"{px}_C_evidencia", f"{sec}.2", s2, "Evidência da densificação normativa", N, EVID, principio=p, regra=na)
    add(f"{px}_C_localizacao_autoria", f"{sec}.2", s2, "Localização e autoria", N, TXT, principio=p, regra=na)
    add(f"{px}_C_justificativa", f"{sec}.2", s2, "Justificativa da classificação", N, TXT, principio=p)
    add(f"{px}_C_alternativa", f"{sec}.2", s2, "Categoria alternativa considerada e razão da rejeição", N, TXT, principio=p)

    s3 = f"{sec}.3 {nome} — Teste de atribuição normativa e contrafactual"
    nc = "Não aplicável, com justificativa, quando não houver critério demonstrável após exame suficiente."
    add(f"{px}_AT_criterio_plano", f"{sec}.3", s3, "Princípio, critério examinado e plano (critério/dever/limite/parâmetro; voto/corrente/núcleo/decisão e segmento)", N, TXT, principio=p)
    add(f"{px}_AT_situacao_criterio", f"{sec}.3", s3, "Situação do critério após exame", N, CAT, SIT_CRIT, principio=p)
    add(f"{px}_AT_atribuicao", f"{sec}.3", s3, "Atribuição normativa", N, CAT, ATRIB, principio=p, regra="Ausente/Presença documental não judicial → Atribuição de critério não demonstrada (7.4). Contribuição própria não equivale a Fundamento determinante.")
    add(f"{px}_AT_outras_fontes", f"{sec}.3", s3, "Outras fontes normativas concorrentes", N, TXT, principio=p)
    add(f"{px}_AT_contribuicao_especifica", f"{sec}.3", s3, "Contribuição específica do princípio para o critério", N, TXT, principio=p, regra=nc)
    add(f"{px}_AT_explicavel_outra_norma", f"{sec}.3", s3, "O critério é inteiramente explicável por outra norma?", N, CAT, NAO_SIM_INC_NA, principio=p, regra=nc)
    add(f"{px}_AT_explicavel_justificativa", f"{sec}.3", s3, "Justificativa (quando Não aplicável) ou explicação da resposta", N, TXT, principio=p)
    add(f"{px}_AT_contrafactual", f"{sec}.3", s3, "Sem o princípio, o conteúdo e a justificação normativa do critério permaneceriam os mesmos?", N, CAT, SIM_NAO_INC_NA, principio=p, regra=nc)
    add(f"{px}_AT_contrafactual_justificativa", f"{sec}.3", s3, "Justificativa (quando Não aplicável) ou explicação da resposta", N, TXT, principio=p)
    add(f"{px}_AT_pergunta_auxiliar", f"{sec}.3", s3, "Pergunta auxiliar: qual papel o princípio exerceu na fundamentação, mesmo sem critério densificado? (informa a posição, não determina a atribuição)", N, TXT, principio=p)
    add(f"{px}_AT_justificativa", f"{sec}.3", s3, "Justificativa da atribuição normativa e uso específico de Atribuição de critério não demonstrada", N, TXT, principio=p)
    add(f"{px}_AT_efeito_teste", f"{sec}.3", s3, "Efeito do teste sobre posição, densificação, atribuição e concretização (alertas, sem correção automática)", N, TXT, principio=p)
    add(f"{px}_AT_evidencia", f"{sec}.3", s3, "Evidência, localização, autoria e posição institucional", N, EVID, principio=p)

    s4 = f"{sec}.4 {nome} — Concretização normativa"
    add(f"{px}_CN_concretizacao", f"{sec}.4", s4, "Concretização normativa", N, CAT, CONCR, principio=p, regra="Aplicar a tabela 7.4 (ver aba Regras 7.4 no dicionário).")
    add(f"{px}_CN_plano_evidencias", f"{sec}.4", s4, "Plano da síntese de concretização normativa e evidências associadas", N, TXT, principio=p)
    add(f"{px}_CN_combinacao", f"{sec}.4", s4, "Combinação entre posição, densificação e atribuição normativa considerada", N, TXT, principio=p)
    add(f"{px}_CN_justificativa", f"{sec}.4", s4, "Justificativa da classificação", N, TXT, principio=p)
    add(f"{px}_CN_seguranca", f"{sec}.4", s4, "Segurança", N, CAT, SEG, principio=p)
    add(f"{px}_CN_revisao_dirigida", f"{sec}.4", s4, "Revisão dirigida necessária?", N, CAT, SIM_NAO, principio=p)
    add(f"{px}_CN_revisao_motivo", f"{sec}.4", s4, "Revisão dirigida — motivo", N, TXT, principio=p, regra="Não aplicável se revisão dirigida = não.")
    add(f"{px}_CN_info_adicional", f"{sec}.4", s4, "Informação adicional necessária", N, TXT, principio=p)



def _bloco_8_9_10(px, nome, sec, parte):
    p = nome
    if parte == "8":
        _bloco8(px, nome, p)
    elif parte == "9":
        _bloco9(px, nome, p)
    else:
        _bloco10(px, nome, p)


def _bloco8(px, nome, p):
    s8 = f"8 Indicadores de função simbólica — {nome}"
    add(f"{px}_FS_nucleo_segmento", "8", s8, "Núcleo, segmento argumentativo e evidência de referência", N, EVID, principio=p)
    add(f"{px}_FS_plano", "8", s8, "Plano de atribuição da função simbólica", N, CAT, ["voto", "corrente", "núcleo", "decisão institucional"], principio=p)
    add(f"{px}_FS_plano_manifestacao", "8", s8, "Identificar a manifestação e seu vínculo com a decisão", N, TXT, principio=p)
    add(f"{px}_FS_entrada", "8", s8, "Pergunta de entrada: existe mobilização judicial ou expectativa constitucional documentalmente identificável que permita avaliar eventual função simbólica?", N, CAT, ["sim", "não", "inconclusivo"], principio=p)
    add(f"{px}_FS_evidencia_entrada", "8", s8, "Evidência da entrada e da mobilização judicial relevante (distinguir expectativa constitucional de mobilização judicial)", N, EVID, principio=p)
    add(f"{px}_FS_posicao_associada", "8", s8, "Posição associada do princípio na fundamentação (texto da posição)", N, TXT, principio=p)
    add(f"{px}_FS_configuracao", "8", s8, "Configuração da posição associada com Função simbólica demonstrada", N, CAT, ["configuração ordinária: Relevante sem participação determinante", "combinação excepcional", "não aplicável"], principio=p)
    add(f"{px}_FS_configuracao_demonstracao", "8", s8, "Fora da configuração ordinária: demonstração da mobilização relevante e compatibilidade com Baixa contribuição normativa", N, TXT, principio=p, regra="Não aplicável na configuração ordinária ou quando configuração = não aplicável.")
    add(f"{px}_FS_proeminencia", "8", s8, "Proeminência discursiva", N, CAT, ["ausente", "baixa", "média", "alta", "inconclusiva"], principio=p, regra="Não aplicável se entrada = não.")
    add(f"{px}_FS_evidencia_proeminencia", "8", s8, "Evidência de proeminência", N, EVID, principio=p)
    add(f"{px}_FS_baixa_contribuicao", "8", s8, "Baixa contribuição normativa", N, CAT, ["não demonstrada", "parcialmente demonstrada", "demonstrada", "inconclusiva"], principio=p, regra="Não aplicável se entrada = não.")
    add(f"{px}_FS_evidencia_baixa_contribuicao", "8", s8, "Evidência de baixa contribuição", N, EVID, principio=p)
    add(f"{px}_FS_discrepancia", "8", s8, "Discrepância interna", N, CAT, ["ausente", "parcial", "presente", "inconclusiva"], principio=p, regra="Não aplicável se entrada = não.")
    add(f"{px}_FS_compromisso_criterio", "8", s8, "Compromisso declarado × critério × comando × matéria não enfrentada", N, TXT, principio=p)
    add(f"{px}_FS_funcao_identificavel", "8", s8, "Função identificável (resposta múltipla; sem função identificada, registrar a ausência no campo de mecanismo)", N, CAT, ["Legitimadora", "Retórica", "Fórmula de compromisso", "Dilatória", "Deslocamento", "Álibi institucional", "Ocultação de assimetria", "Outra função — especificar: …"], "múltipla", principio=p, regra="'Outra função' nunca representa ausência de função. Não aplicável se entrada = não.")
    add(f"{px}_FS_mecanismo", "8", s8, "Mecanismo da função na estrutura argumentativa (cada função selecionada, mecanismo e evidência)", N, TXT, principio=p)
    add(f"{px}_FS_politico_ideologica", "8", s8, "Função político-ideológica", N, CAT, ["não demonstrada", "indiciária", "demonstrada no plano discursivo", "inconclusiva"], principio=p, regra="Não aplicável se entrada = não.")
    add(f"{px}_FS_evidencia", "8", s8, "Evidência, localização, autoria e posição institucional", N, EVID, principio=p)
    add(f"{px}_FS_funcao_simbolica", "8", s8, "Função simbólica", N, CAT, FS, principio=p, regra="Seção 8.1. Função simbólica demonstrada exige todos os requisitos cumulativos no mesmo princípio e plano e exame prévio das alternativas (seção 9).")
    add(f"{px}_FS_justificativa", "8", s8, "Justificativa da função simbólica e verificação dos requisitos cumulativos", N, TXT, principio=p)
    add(f"{px}_FS_alternativa", "8", s8, "Categoria alternativa considerada e razão da rejeição", N, TXT, principio=p)
    add(f"{px}_FS_limite_atribuicao", "8", s8, "Limite da atribuição institucional e vínculo com a síntese", N, TXT, principio=p)
    add(f"{px}_FS_seguranca", "8", s8, "Segurança", N, CAT, SEG, principio=p)



def _bloco9(px, nome, p):
    s9 = f"9 Explicações alternativas — {nome}"
    add(f"{px}_ALT_voto_segmento", "9", s9, "Voto/corrente/decisão e segmento", N, TXT, principio=p)
    add(f"{px}_ALT_plano_aspecto", "9", s9, "Plano e aspecto da inferência submetidos às alternativas", N, TXT, principio=p)
    for h, hip in enumerate(HIPOTESES, start=1):
        pre = f"{px}_ALT_H{h:02d}"
        rr = "Preencher para o princípio e plano examinados na seção 8. Com entrada negativa: 'Não aplicável' (padrão do gabarito da ADI 3355)."
        add(f"{pre}_fato_localizacao", "9", s9, f"{hip} — fato/condição e localização", N, EVID, principio=p, regra=rr)
        add(f"{pre}_evidencia_favoravel", "9", s9, f"{hip} — evidência favorável", N, EVID, principio=p, regra=rr)
        add(f"{pre}_evidencia_contraria", "9", s9, f"{hip} — evidência contrária", N, EVID, principio=p, regra=rr)
        add(f"{pre}_decisao", "9", s9, f"{hip} — decisão explicativa", N, CAT, DEC_HIP, principio=p, regra=rr)
        add(f"{pre}_aspecto_efeito", "9", s9, f"{hip} — aspecto/plano explicado e efeito sobre a função simbólica (questão remanescente)", N, TXT, principio=p, regra=rr)



def _bloco10(px, nome, p):
    s10 = f"10 Ausências, não mobilização — {nome}"
    if px == "MA":
        r10 = "Preencher quando analiticamente relevante; caso contrário, Não aplicável com justificativa."
    else:
        r10 = "Obrigatório quando a posição for Ausente, Presença documental não judicial, Voto não prevalecente, Genérica/ornamental, Relevante sem participação determinante ou Obstáculo processual/institucional; Não aplicável se Fundamento determinante ou Inconclusivo."
    add(f"{px}_AUS_aplicavel", "10", s10, "Regra de entrada da seção 10 atendida?", N, CAT, ["sim", "não — Não aplicável"], principio=p, regra=r10)
    add(f"{px}_AUS_pertinencia", "10", s10, "Pertinência jurídica", N, CAT, ["claramente", "potencialmente", "remotamente", "não pertinente", "inconclusiva"], principio=p, regra=r10)
    add(f"{px}_AUS_pertinencia_justificativa", "10", s10, "Justificativa da pertinência", N, TXT, principio=p, regra=r10)
    add(f"{px}_AUS_suscitacao", "10", s10, "Suscitação", N, CAT, ["pedido", "defesa", "parecer", "terceiro", "voto", "voto vencido", "nenhuma peça", "não verificável"], "múltipla", principio=p, regra=r10)
    add(f"{px}_AUS_evidencia_suscitacao", "10", s10, "Evidência e localização da suscitação", N, EVID, principio=p, regra=r10)
    add(f"{px}_AUS_enfrentamento", "10", s10, "Enfrentamento judicial", N, CAT, ["expresso", "implícito demonstrável", "não enfrentado", "prejudicado", "inconclusivo"], principio=p, regra=r10)
    add(f"{px}_AUS_evidencia_enfrentamento", "10", s10, "Evidência e localização do enfrentamento", N, EVID, principio=p, regra=r10)
    add(f"{px}_AUS_silenciamento", "10", s10, "Uso da expressão 'silenciamento' autorizado?", N, CAT, ["não", "sim – presentes pertinência clara, suscitação, não enfrentamento e suficiência documental"], principio=p, regra=r10 + " 'sim' só com as quatro condições cumulativas.")


# Ordem do instrumento: 7.1–7.3, depois seção 8, 9 e 10 para os três princípios.
for parte in ("7", "8", "9", "10"):
    for px, nome, art, sec in PRINCIPIOS:
        bloco_principio(px, nome, art, sec, parte)

# ------------------------------------------- 10.1 categorias prevalentes
s = "10.1 Categorias jurídicas prevalentes"
for k in range(1, MAXIMOS["categorias_prevalentes"] + 1):
    r = "Célula vazia se não houver esta entrada (linha não utilizada)."
    add(f"S10_CAT{k}_principio", "10.1", s, f"Categoria {k} — princípio do bloco da seção 10 a que a relação se refere", N, CAT, [p[1] for p in PRINCIPIOS], "múltipla", regra=r)
    add(f"S10_CAT{k}_categoria", "10.1", s, f"Categoria {k} — categoria", N, TXT, regra=r)
    add(f"S10_CAT{k}_fonte", "10.1", s, f"Categoria {k} — fonte", N, TXT, regra=r)
    add(f"S10_CAT{k}_posicao", "10.1", s, f"Categoria {k} — posição", N, TXT, regra=r)
    add(f"S10_CAT{k}_funcao", "10.1", s, f"Categoria {k} — função", N, TXT, regra=r)
    add(f"S10_CAT{k}_consequencia", "10.1", s, f"Categoria {k} — consequência", N, TXT, regra=r)
    add(f"S10_CAT{k}_relacao", "10.1", s, f"Categoria {k} — relação com o princípio", N, CAT, ["substituição explícita", "equivalência funcional", "concorrência", "adjacente", "sem relação", "Inconclusivo — evidência examinada insuficiente"], regra=r)
add("S10_interpretacao_qualitativa", "10.1", s, "Evidência e interpretação qualitativa da ausência/não mobilização", N, TXT)

# ---------------------------------------------------------------- seção 11
s = "11 Implementação, eficácia e limites"
add("S11_cumprimento", "11", s, "Há informação sobre cumprimento?", N, CAT, ["sim", "não", "parcial", "inconclusivo"])
add("S11_providencia", "11", s, "Providência adotada", N, TXT)
add("S11_destinatario", "11", s, "Destinatário", N, TXT)
add("S11_prazo", "11", s, "Prazo", N, TXT)
add("S11_mecanismo_controle", "11", s, "Mecanismo de controle", N, TXT)
add("S11_evidencia", "11", s, "Evidência de implementação", N, EVID)
add("S11_fonte", "11", s, "Fonte", N, CAT, ["decisão", "acompanhamento processual", "fonte externa identificada", "outra: …"], "múltipla")
add("S11_limite_inferencial", "11", s, "Limite inferencial (não confundir resolução/densificação com implementação, eficácia ou transformação material)", N, TXT)

# ---------------------------------------------------------------- seção 12
s = "12 Síntese analítica do núcleo"
add("S12_identificacao", "12", s, "Identificação do núcleo", N, TXT)
add("S12_resolucao_operativa", "12", s, "Resolução operativa", N, CAT, RESOL, regra="Deve coincidir com S06_resolucao_operativa.")
for px, nome, _, _ in PRINCIPIOS:
    add(f"S12_{px}_concretizacao", "12", s, f"{nome} — concretização normativa", N, CAT, CONCR, principio=nome, regra=f"Deve coincidir com {px}_CN_concretizacao.")
    add(f"S12_{px}_funcao_simbolica", "12", s, f"{nome} — função simbólica", N, CAT, FS, principio=nome, regra=f"Deve coincidir com {px}_FS_funcao_simbolica.")
add("S12_planos_registros", "12", s, "Planos da concretização normativa e da função simbólica e registros localizados associados", N, TXT)
add("S12_categorias_prevalentes", "12", s, "Categorias jurídicas prevalentes", N, TXT)
add("S12_assimetria", "12", s, "Assimetria entre os princípios", N, TXT)
add("S12_interpretacao", "12", s, "Interpretação qualitativa", N, TXT)
add("S12_insuficiencia", "12", s, "Insuficiência documental", N, TXT)
add("S12_revisao_dirigida", "12", s, "Pendência de revisão dirigida", N, CAT, SIM_NAO)
add("S12_revisao_variaveis_motivo", "12", s, "Pendência de revisão dirigida — variáveis e motivo", N, TXT, regra="Não aplicável se = não.")
add("S12_alerta_pseudorreplicacao", "12", s, "Alerta de pseudorreplicação", N, TXT)

# ---------------------------------------------------------------- seção 13
s = "13 Síntese da decisão"
for px, nome, _, _ in PRINCIPIOS:
    add(f"S13_{px}_observacao", "13", s, f"Tabela da síntese — observação do núcleo para {nome} (resolução, concretização e função simbólica da tabela são as colunas S12 da mesma linha)", N, TXT, principio=nome)
add("S13_resolveu", "13", s, "A decisão resolveu operativamente a controvérsia?", D, TXT)
add("S13_concretizados", "13", s, "Quais princípios foram normativamente concretizados?", D, TXT)
add("S13_ausentes_contextuais", "13", s, "Quais permaneceram ausentes, contextuais ou não densificados?", D, TXT)
add("S13_funcao_simbolica_nivel", "13", s, "Houve indício ou demonstração de função simbólica? Em qual nível?", D, TXT)
add("S13_categorias_estruturantes", "13", s, "Quais categorias estruturaram a fundamentação?", D, TXT)
add("S13_assimetria", "13", s, "Há assimetria entre Interesse nacional, Função social da propriedade e Meio ambiente?", D, TXT)
add("S13_ratio_reconstruida", "13", s, "A ratio institucional pôde ser reconstruída?", D, TXT)
add("S13_limites", "13", s, "Limites documentais e inferenciais", D, TXT)
add("S13_pendencias", "13", s, "Pendências de revisão que afetam a síntese (controles da seção 15; resultados provisórios)", D, TXT)
add("S13_pontos_comparaveis", "13", s, "Pontos comparáveis no conjunto das decisões", D, TXT)

# ---------------------------------------------------------------- seção 14
s = "14 Perfil multidimensional da decisão"
add("S14_resolucao_operativa", "14", s, "Resolução operativa", D, CAT, ["todos os núcleos", "parte dos núcleos", "ausente", "inconclusiva"])
for px, nome, _, _ in PRINCIPIOS:
    add(f"S14_{px}_concretizacao", "14", s, f"Concretização normativa — {nome}", D, CAT, CONCR[:5] + ["heterogênea", "Inconclusivo"], principio=nome, regra="Não agregar por maioria aritmética; 'heterogênea' quando os núcleos divergirem.")
    add(f"S14_{px}_funcao_simbolica", "14", s, f"Função simbólica — {nome}", D, CAT, FS[:4] + ["heterogênea", "Inconclusivo"], principio=nome)
add("S14_padrao_decisorio", "14", s, "Padrão decisório predominante", D, TXT)
add("S14_planos_incorporacao", "14", s, "Planos das evidências e condições de incorporação institucional", D, TXT)
add("S14_resultado_contraria_hipotese", "14", s, "Resultado que contraria a hipótese", D, TXT)
add("S14_conclusao_limitada", "14", s, "Conclusão limitada à decisão", D, TXT)
add("S14_controles_pendentes", "14", s, "Controles pendentes e repercussão na conclusão (remeter à seção 15)", D, TXT)

# ---------------------------------------------------------------- seção 15
s = "15 Controle de consistência, segurança e rastreabilidade"
add("S15_total_registros", "15", s, "Total de registros de controle desta linha", N, "dado")
for k in range(1, MAXIMOS["controles_s15"] + 1):
    r = "Célula vazia se não houver este registro (linha não utilizada)."
    pre = f"S15_K{k}"
    add(f"{pre}_referencia", "15", s, f"Controle {k} — decisão, núcleo, princípio, plano e variável", N, TXT, regra=r)
    add(f"{pre}_categoria_antes", "15", s, f"Controle {k} — categoria substantiva registrada antes da revisão dirigida", N, TXT, regra=r)
    add(f"{pre}_marcador", "15", s, f"Controle {k} — marcador administrativo do registro", N, CAT, ["nenhum"] + MARCADORES, regra=r)
    add(f"{pre}_marcador_motivo", "15", s, f"Controle {k} — motivo e campo a que se aplica o marcador", N, TXT, regra=r)
    add(f"{pre}_alternativa", "15", s, f"Controle {k} — categoria alternativa considerada", N, TXT, regra=r)
    add(f"{pre}_razao", "15", s, f"Controle {k} — razão da dúvida, incompatibilidade ou revisão", N, TXT, regra=r)
    add(f"{pre}_natureza", "15", s, f"Controle {k} — natureza do alerta", N, CAT, ["incompatibilidade entre categorias", "combinação não prevista", "insuficiência documental", "pendência de preenchimento", "exceção de Função simbólica demonstrada", "outra: …"], regra=r)
    add(f"{pre}_evidencia", "15", s, f"Controle {k} — evidência textual e localização", N, EVID, regra=r)
    add(f"{pre}_autoria", "15", s, f"Controle {k} — autoria e posição institucional", N, TXT, regra=r)
    add(f"{pre}_seguranca", "15", s, f"Controle {k} — grau de segurança", N, CAT, SEG, regra=r)
    add(f"{pre}_impacto", "15", s, f"Controle {k} — impacto potencial sobre síntese ou conclusão", N, CAT, ["nenhum", "possível", "demonstrado", "inconclusivo"], regra=r)
    add(f"{pre}_sensibilidade", "15", s, f"Controle {k} — análise de sensibilidade necessária? (se sim, registrar cenário)", N, TXT, regra=r)
    add(f"{pre}_decisao_final", "15", s, f"Controle {k} — decisão final", N, CAT, ["manter categoria", "alterar categoria", "manter inconclusivo — justificativa: …"], regra=r + " No pré-preenchimento: decisão final cabe à pesquisadora.")
    add(f"{pre}_status", "15", s, f"Controle {k} — status da revisão", N, CAT, ["não necessária", "pendente", "concluída"], regra=r)

# ---------------------------------------------------------------- seção 16
s = "16 Auditoria final"
AUD = [
    ("nucleos_autonomos", "Todos os núcleos têm problema, fundamento, resposta e consequência próprios?", ["sim", "não", "rever"]),
    ("resultado_fundamentos", "Resultado e fundamentos majoritários foram diferenciados?", ["sim", "não", "não aplicável"]),
    ("trechos_localizacao", "Todas as classificações têm trecho e localização verificável?", SIM_NAO),
    ("autoria_posicao", "Autoria e posição institucional foram registradas?", SIM_NAO),
    ("densificacao_contribuicao", "Densificações possuem Contribuição própria ou compartilhada demonstrada?", ["sim", "não", "não aplicável"]),
    ("fsd_requisitos", "Função simbólica demonstrada satisfaz todos os requisitos cumulativos?", ["sim", "não", "não aplicável"]),
    ("alternativas_testadas", "Explicações alternativas foram testadas antes de Indícios ou Função simbólica demonstrada?", ["sim", "não", "não aplicável"]),
    ("ausencia_simbolismo", "Ausência foi distinguida de simbolismo?", SIM_NAO),
    ("implementacao_separada", "Implementação foi separada de concretização normativa?", SIM_NAO),
    ("seguranca_baixa_revisao", "Pontos de segurança baixa ou inconclusiva foram submetidos à revisão dirigida?", ["sim", "não", "não aplicável"]),
    ("nucleos_aninhados", "Há alerta sobre núcleos aninhados na mesma decisão?", SIM_NAO),
    ("respostas_multiplas", "Respostas múltiplas foram registradas sem escolha silenciosa ou célula vazia ambígua?", ["sim", "não", "não aplicável"]),
    ("marcadores_regras", "Marcadores e células vazias obedecem às regras do protocolo?", SIM_NAO),
    ("combinacoes_compativeis", "As combinações entre posição, densificação, atribuição e concretização são compatíveis?", ["sim", "não", "rever"]),
    ("fs_regras", "Categorias de função simbólica obedecem às regras de aplicação?", ["sim", "não", "rever"]),
    ("alertas_sem_alteracao", "Alertas lógicos foram examinados sem alteração automática de códigos?", SIM_NAO),
    ("categoria_alterada_ratificada", "Toda categoria alterada foi ratificada pela pesquisadora?", ["sim", "não", "não aplicável"]),
    ("sensibilidade", "Categoria alternativa com impacto foi submetida à análise de sensibilidade?", ["sim", "não", "não aplicável"]),
    ("dens_institucional_incorporacao", "Densificação institucional está apoiada em incorporação institucional e não apenas em voto não prevalecente?", ["sim", "não", "não aplicável"]),
    ("generica_relevante_obstaculo", "Genérica/ornamental e Relevante sem participação determinante preservam Presença contextual/discursiva, e Obstáculo distingue ausência de mobilização de exame obstado?", ["sim", "não", "não aplicável"]),
    ("fd_sem_densificacao", "A combinação Fundamento determinante / Conteúdo não densificado / Atribuição não demonstrada / FD sem densificação demonstra papel determinante sem Presença contextual no mesmo segmento?", ["sim", "não", "não aplicável"]),
    ("lacuna_controle_proprio", "Incompatibilidade ou lacuna de regra gera controle próprio, sem conversão automática em concretização inconclusiva?", ["sim", "não", "não aplicável"]),
    ("fsd_fora_ordinaria", "Função simbólica demonstrada fora de Relevante sem participação determinante tem justificativa da exceção?", ["sim", "não", "não aplicável"]),
    ("fsd_entrada_mobilizacao", "Função simbólica demonstrada tem entrada afirmativa, mobilização relevante, proeminência média/alta, baixa contribuição demonstrada e discrepância presente?", ["sim", "não", "não aplicável"]),
    ("fsd_funcao_mecanismo", "Função simbólica demonstrada tem função identificável e mecanismo, função político-ideológica demonstrada e evidência localizada?", ["sim", "não", "não aplicável"]),
    ("fsd_mesmo_plano", "Todos os requisitos de Função simbólica demonstrada se referem ao mesmo princípio e plano, com alternativas afastadas?", ["sim", "não", "não aplicável"]),
    ("fs_categorias_distintas", "Categorias de função simbólica distinguem aplicabilidade, resultado negativo, indício e insuficiência, sem confusão com pendências administrativas?", ["sim", "não", "rever"]),
    ("alternativas_capacidade", "As alternativas foram avaliadas por sua capacidade explicativa, preservando fatos processuais e o alcance da inferência?", ["sim", "não", "não aplicável"]),
]
for i, (nm, q, cats) in enumerate(AUD, start=1):
    add(f"S16_{i:02d}_{nm}", "16", s, q, D, CAT, cats)
add("S16_pendencias_conferencia_manual", "16", s, "Pendências para conferência manual", D, TXT)
add("S16_notas", "16", s, "Notas da auditoria (justificativa item a item, quando necessária)", D, TXT)

# ------------------------------------------------------------- validação
s = "Validação da pesquisadora"
add("VAL_concorda", "Validação", s, "Concorda? (preenchido pela pesquisadora)", N, CAT, ["sim", "não", "parcialmente"], origem="validação da pesquisadora", regra="Vazio até a validação.")
add("VAL_correcoes", "Validação", s, "Correções (coluna e novo valor)", N, TXT, origem="validação da pesquisadora", regra="Vazio até a validação.")
add("VAL_comentario", "Validação", s, "Comentário", N, TXT, origem="validação da pesquisadora", regra="Vazio até a validação.")


# ===================================================================
# CATÁLOGO DE PERGUNTAS (formato longo do banco)
# ===================================================================
# No banco final cada linha é UMA RESPOSTA. Os campos do instrumento que
# acompanham uma classificação (evidência, localização/autoria, justificativa,
# categoria alternativa, segurança, "sim – explicar") não viram linhas
# próprias: são registrados nas colunas Trecho / Autoria e plano /
# Justificativa / Alternativa / Segurança da linha da classificação.
# A lista ABSORVE documenta, para cada pergunta, quais campos do instrumento
# ela absorve, garantindo que nenhum campo do questionário se perca.
import re as _re

ABSORVE = {
    "S02_caso_limitrofe": {"justificativa": "S02_caso_limitrofe_justificativa"},
    "S03_maioria_res_dif_fund": {"justificativa": "S03_maioria_res_dif_fund_explicar"},
    "S03_separar_nucleos": {"justificativa": "S03_separar_nucleos_explicar"},
    "S04_N_elegivel": {"justificativa": "S04_N_justificativa", "trecho": "S04_N_evidencia"},
    "S06_resolucao_operativa": {"trecho": "S06_evidencia", "autoria": "S06_localizacao_autoria",
                                "justificativa": "S06_justificativa", "alternativa": "S06_alternativa",
                                "seguranca": "S06_seguranca"},
    "S11_cumprimento": {"trecho": "S11_evidencia"},
    "S12_revisao_dirigida": {"justificativa": "S12_revisao_variaveis_motivo"},
    "S15_K_marcador": {"justificativa": "S15_K_marcador_motivo"},
    "S15_K_natureza": {"trecho": "S15_K_evidencia", "autoria": "S15_K_autoria", "seguranca": "S15_K_seguranca"},
}
for px, *_ in PRINCIPIOS:
    ABSORVE.update({
        f"{px}_B_posicao": {"trecho": f"{px}_B_evidencia", "autoria": f"{px}_B_localizacao_autoria",
                            "justificativa": f"{px}_B_justificativa", "alternativa": f"{px}_B_alternativa"},
        f"{px}_C_densificacao": {"trecho": f"{px}_C_evidencia", "autoria": f"{px}_C_localizacao_autoria",
                                 "justificativa": f"{px}_C_justificativa", "alternativa": f"{px}_C_alternativa"},
        f"{px}_AT_atribuicao": {"trecho": f"{px}_AT_evidencia", "justificativa": f"{px}_AT_justificativa"},
        f"{px}_AT_explicavel_outra_norma": {"justificativa": f"{px}_AT_explicavel_justificativa"},
        f"{px}_AT_contrafactual": {"justificativa": f"{px}_AT_contrafactual_justificativa"},
        f"{px}_CN_concretizacao": {"justificativa": f"{px}_CN_justificativa", "seguranca": f"{px}_CN_seguranca"},
        f"{px}_CN_revisao_dirigida": {"justificativa": f"{px}_CN_revisao_motivo"},
        f"{px}_FS_plano": {"justificativa": f"{px}_FS_plano_manifestacao"},
        f"{px}_FS_entrada": {"trecho": f"{px}_FS_evidencia_entrada"},
        f"{px}_FS_configuracao": {"justificativa": f"{px}_FS_configuracao_demonstracao"},
        f"{px}_FS_proeminencia": {"trecho": f"{px}_FS_evidencia_proeminencia"},
        f"{px}_FS_baixa_contribuicao": {"trecho": f"{px}_FS_evidencia_baixa_contribuicao"},
        f"{px}_FS_funcao_identificavel": {"justificativa": f"{px}_FS_mecanismo"},
        f"{px}_FS_politico_ideologica": {"trecho": f"{px}_FS_evidencia"},
        f"{px}_FS_funcao_simbolica": {"justificativa": f"{px}_FS_justificativa", "alternativa": f"{px}_FS_alternativa",
                                      "seguranca": f"{px}_FS_seguranca"},
        f"{px}_AUS_pertinencia": {"justificativa": f"{px}_AUS_pertinencia_justificativa"},
        f"{px}_AUS_suscitacao": {"trecho": f"{px}_AUS_evidencia_suscitacao"},
        f"{px}_AUS_enfrentamento": {"trecho": f"{px}_AUS_evidencia_enfrentamento"},
    })
    for h in range(1, 11):
        ABSORVE[f"{px}_ALT_H{h:02d}_decisao"] = {"trecho": f"{px}_ALT_H{h:02d}_fato_localizacao",
                                                 "justificativa": f"{px}_ALT_H{h:02d}_aspecto_efeito"}

TABELAS_VARIAVEIS = {"S04_N": "Núcleo do mapa nº", "S10_CAT": "Categoria nº", "S15_K": "Controle nº"}


def _colapsa(nome):
    for pre in TABELAS_VARIAVEIS:
        nome = _re.sub(rf"^{pre}\d+_", f"{pre}_", nome)
    return nome


def catalogo():
    """Lista ordenada de perguntas (uma por ID), com os campos absorvidos."""
    absorvidos = {v: k for k, d in ABSORVE.items() for v in d.values()}
    vistos, cat = set(), []
    for c in CAMPOS:
        if c["secao"] in ("ID", "Validação") or c["coluna"] in (
                "CTRL_fonte_texto", "CTRL_paginas_total", "CTRL_paginas_ocr", "CTRL_conferencia_automatica"):
            continue  # viram colunas fixas do banco longo ou são preenchidos pelo script
        pid = _colapsa(c["coluna"])
        if pid in vistos or pid in absorvidos:
            continue
        vistos.add(pid)
        q = dict(c)
        q["id_pergunta"] = pid
        q["descricao"] = _re.sub(r"^(Núcleo|Categoria|Controle) \d+ — ", "", q["descricao"])
        q["tabela_variavel"] = next((v for k, v in TABELAS_VARIAVEIS.items() if pid.startswith(k + "_")), "")
        if q["regra_entrada"].startswith("Célula vazia se"):
            q["regra_entrada"] = "Uma linha por entrada existente (tabela de tamanho variável)." + q["regra_entrada"].split(").", 1)[-1]
        ab = ABSORVE.get(pid, {})
        desc_por_nome = {_colapsa(x["coluna"]): x["descricao"] for x in CAMPOS}
        q["absorve"] = "; ".join(f"{papel} ← {_re.sub(r'^(Núcleo|Categoria|Controle) \d+ — ', '', desc_por_nome[n])}"
                                 for papel, n in ab.items())
        for k in ("coluna", "ordem"):
            q.pop(k)
        cat.append(q)
    # pergunta técnica usada apenas em decisões sem núcleo elegível (regra de parada)
    pos = next(i for i, q in enumerate(cat) if q["id_pergunta"].startswith("S05_"))
    cat.insert(pos, dict(id_pergunta="S05_S12_regra_parada", secao="5–12", bloco="Seções 5 a 12 (análise substantiva)",
                         descricao="Análise substantiva do núcleo (seções 5 a 12)", nivel="núcleo", principio="", plano="",
                         tipo="marcador", resposta="", categorias="Não aplicável", origem="regra de parada",
                         regra_entrada="Só em decisão sem núcleo elegível: uma linha com 'Não aplicável' (regra de parada).",
                         exemplo="Não aplicável", tabela_variavel="", absorve=""))
    for i, q in enumerate(cat, start=1):
        q["ordem"] = i
    return cat


# Colunas do banco longo (output 2): nome, descrição, origem.
COLUNAS_BANCO = [
    ("ID_linha", "Identificador único da linha (decisão + núcleo + item + pergunta).", "script"),
    ("ID_decisao", "Identificador estável da decisão, igual ao do banco SQLite (output 1).", "extração automática"),
    ("Decisão", "Nome do documento da decisão.", "extração automática"),
    ("Classe", "Classe processual (ADI, ACO, ADPF, RE).", "extração automática"),
    ("Data do julgamento", "Data final do julgamento (dd/mm/aaaa).", "extração automática + LLM"),
    ("Nível", "'decisão' (seções 1–4, 13, 14, 16) ou 'núcleo' (seções 5–12, 15).", "script"),
    ("Núcleo", "Número do núcleo elegível (vazio nas linhas de nível decisão; 0 = decisão sem núcleo elegível).", "LLM"),
    ("Título do núcleo", "Título curto do núcleo.", "LLM"),
    ("Seção", "Seção do questionário (1 a 16).", "dicionário"),
    ("Grupo da pergunta", "Bloco do questionário a que a pergunta pertence.", "dicionário"),
    ("Princípio", "Interesse nacional, Função social da propriedade ou Meio ambiente ecologicamente equilibrado (vazio quando não se aplica).", "dicionário"),
    ("Item", "Número da entrada nas tabelas variáveis (mapa de núcleos, categorias prevalentes, controles da seção 15).", "LLM"),
    ("ID_pergunta", "Código da pergunta no catálogo (output 3).", "dicionário"),
    ("Pergunta do questionário", "Texto do campo do questionário.", "dicionário"),
    ("Tipo de resposta", "categoria (única/múltipla), texto livre, dado ou evidência.", "dicionário"),
    ("Resposta", "Resposta baseada na leitura do documento: categoria do instrumento, marcador de dados ou texto.", "LLM"),
    ("Trecho (evidência literal)", "Trecho(s) literal(is) do acórdão que sustentam a resposta. Vários trechos separados por ' || '.", "LLM"),
    ("Página PDF", "Página(s) do PDF onde está cada trecho, na mesma ordem.", "LLM"),
    ("Página impressa", "Paginação impressa correspondente, lida do banco SQLite.", "script"),
    ("Autoria e plano", "Autor da manifestação e plano (voto, corrente, núcleo, decisão institucional) e posição institucional.", "LLM"),
    ("Justificativa", "Justificativa da resposta (inclui os campos 'justificar/explicar/motivo' do instrumento).", "LLM"),
    ("Categoria alternativa e razão", "Categoria alternativa considerada e razão da rejeição (obrigatória em casos limítrofes ou de segurança baixa).", "LLM"),
    ("Segurança", "Grau de segurança (alta, média, baixa, inconclusiva) — avaliação qualitativa, não probabilidade.", "LLM"),
    ("Origem da resposta", "LLM (leitura interpretativa), extração automática ou regra de salto aplicada pelo script.", "script"),
    ("Conferência automática", "Resultado da conferência por script (trecho localizado, domínio, compatibilidade).", "script"),
    ("Concorda?", "Validação da pesquisadora: sim / não / parcialmente.", "validação da pesquisadora"),
    ("Correções", "Correção proposta pela pesquisadora.", "validação da pesquisadora"),
    ("Comentário", "Comentário da pesquisadora.", "validação da pesquisadora"),
]


def contagem():
    fixos = [c for c in CAMPOS if not any(t in c["coluna"] for t in ("S04_N", "S10_CAT", "S15_K"))
             and not c["coluna"].startswith(("ID_", "CTRL_", "VAL_"))]
    return {
        "total_colunas": len(CAMPOS),
        "identificacao_controle_validacao": sum(c["coluna"].startswith(("ID_", "CTRL_", "VAL_")) for c in CAMPOS),
        "campos_fixos_questionario": len(fixos),
        "  dos quais secao 9 (alternativas)": sum(c["secao"] == "9" for c in fixos),
        "tabelas_variaveis (mapa, categorias, controles)": sum(any(t in c["coluna"] for t in ("S04_N", "S10_CAT", "S15_K")) for c in CAMPOS),
        "maximos": MAXIMOS,
    }


if __name__ == "__main__":
    nomes = [c["coluna"] for c in CAMPOS]
    assert len(nomes) == len(set(nomes)), "nomes de coluna duplicados"
    cat = catalogo()
    ids = [q["id_pergunta"] for q in cat]
    assert len(ids) == len(set(ids))
    Path("dicionario_campos.json").write_text(json.dumps({
        "catalogo": cat, "colunas_banco": [dict(coluna=a, descricao=b, origem=c) for a, b, c in COLUNAS_BANCO],
        "marcadores": MARCADORES, "campos_instrumento": CAMPOS}, ensure_ascii=False, indent=1), encoding="utf-8")
    absorvidos = sum(len(d) for d in ABSORVE.values())
    print(f"campos do instrumento (formato largo): {len(CAMPOS)}")
    print(f"perguntas no catálogo: {len(cat)}  (campos absorvidos nas colunas da linha: ~{absorvidos})")
    print(f"colunas do banco longo: {len(COLUNAS_BANCO)}")
