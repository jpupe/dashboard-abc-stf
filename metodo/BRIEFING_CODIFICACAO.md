# Briefing para a codificação das decisões (agentes auxiliares)

Projeto: tese de doutorado de Suzy Sousa (UFPA). Aplicação do "Instrumento de análise dos núcleos decisórios e de classificação pelo índice A/B/C" (v5.0) a decisões do STF sobre direito minerário. Você faz o **pré-preenchimento** de uma ou mais decisões. Todas as classificações são provisórias; quem decide é a pesquisadora. Trabalhe em **português**.

Pasta do projeto: `/home/claude/projeto` (rode todos os comandos a partir dela).

## 1. Leia antes de começar (obrigatório, nesta ordem)

1. `metodo/regras_capitulo6_limpo.txt`: capítulo 6 da tese (regras de construção e preenchimento). É vinculante.
2. `metodo/questionario_v5.txt`: o questionário completo, com as categorias e as regras 7.4 e 8.1. É vinculante.
3. `metodo/prompt_suzy_v5.md`: as regras analíticas da pesquisadora.
4. `metodo/catalogo_perguntas.txt`: as 392 perguntas do banco, com o código (ID_pergunta), as categorias permitidas e os campos "absorvidos" em cada linha.
5. Modelos já aprovados:
   - `codificacao/ADI_6650.json`: concretização institucional do meio ambiente.
   - `codificacao/ADI_7273_MC-Ref.json`: cautelar, com dois controles.
   - `codificacao/ADI_3355.json`: princípio relevante sem participação determinante; seção 9 completa; maioria parcial.

   Siga **exatamente** o formato deles.

## 2. Leitura da decisão

- O texto vem SEMPRE do banco SQLite (`decisoes.sqlite`). Nunca use memória ou conhecimento externo sobre o caso.
- Para gerar o texto de leitura, com marcadores `=== [p.N | impr.M] ===`:
  `python3 -I scripts/dump_texto.py decisoes.sqlite ID_DECISAO leitura/ID_DECISAO.txt`
- Leia o arquivo inteiro com a ferramenta Read. Arquivos grandes devem ser lidos em partes, com `offset`/`limit`, até o fim. Nenhuma página pode ficar sem leitura.
- **Decisões longas:** leia em partes (por exemplo, voto a voto) e anote em notas próprias os trechos e as páginas de cada parte. No fim, faça uma passada de consolidação (mapa de núcleos, maioria quanto ao fundamento e sínteses). Registre as partes em `CTRL_partes_processadas`.
- `N` é a página do PDF, a que vai no JSON. `impr.` é a paginação impressa; o script a preenche sozinho.

## 3. Formato do JSON (`codificacao/ID_DECISAO.json`)

```
{"id_decisao": "ADI_4606", "rotulo": "ADI 4606", "data_final": "dd/mm/aaaa",
 "decisao": { ID_pergunta: resposta, ... },          # seções 1–4 (exceto o mapa), 13, 14, 16 e CTRL_*
 "mapa": [ {S04_N_questao, S04_N_regra_comando, S04_N_consequencia, S04_N_elegivel}, ... ],  # todos os núcleos
 "nucleos": [ {"n": 1, "titulo": "...", "respostas": {ID: resposta},
              "categorias": [ {S10_CAT_*: ...}, ... ], "controles": [ {S15_K_*: ...}, ... ]} ] }
```

- **Resposta** é uma string com a resposta, ou um objeto:
  `{"r": resposta, "t": [["trecho literal", pagina_pdf], ...], "a": "autoria e plano", "j": "justificativa", "alt": "categoria alternativa e razão", "s": "alta|média|baixa|inconclusiva"}`.
- Pergunta categórica: `r` deve ser exatamente uma das categorias permitidas do catálogo, ou um marcador. Em resposta múltipla, separe as categorias com `" ; "`. Em "outro: …", escreva `"outro: descrição"`.
- Os campos que o catálogo marca como ABSORVE não entram como perguntas próprias. Eles vão para `t`, `a`, `j`, `alt` e `s` da pergunta que os absorve. Exemplos: a evidência da posição vai para `t` de `IN_B_posicao`; a justificativa da concretização vai para `j` de `IN_CN_concretizacao`.
- **Decisão sem núcleo elegível (regra de parada):** use `"nucleos": []`. O script gera a linha "Não aplicável". O mapa e as seções 1–4, 13, 14 e 16 continuam obrigatórios.

## 4. Trechos (são conferidos por script; erre para menos, nunca para mais)

- O trecho é cópia **literal** do arquivo de leitura, de **uma única página**. Use de 8 a 40 palavras.
- O trecho não pode atravessar quebra de página.
- Não inclua cabeçalhos ("Voto - MIN. …", "ADI 3355 / RJ"), números de página nem a expressão "Supremo Tribunal Federal", que é removida do arquivo de leitura.
- Para pular um trecho do meio, use reticências (`...`). Cada parte entre as reticências precisa existir na mesma página.
- Nas páginas de OCR (decisões antigas escaneadas), copie como saiu no texto de leitura, mesmo com erros de OCR.

## 5. O que o script preenche sozinho (não escreva)

- **Regras de salto.** Se `*_B_posicao` for Ausente ou Presença documental não judicial, o script preenche os campos `*_C_*` e as perguntas contrafactuais do 7.x.3 que faltarem. Se `*_FS_entrada` = "não", preenche os indicadores da seção 8 e toda a seção 9 do princípio. Se `*_AUS_aplicavel` = "não — Não aplicável", preenche o resto da seção 10.
- Mesmo nesses casos, **escreva sempre**: `*_B_posicao`, `*_B_plano_voto`, `*_B_forma_mobilizacao`, `*_B_posicao_voto_decisao`, `*_B_conexao`, `*_B_mobilizacao_obstaculo`, `*_C_densificacao`, os campos `*_AT_*` (situação, atribuição, outras fontes, pergunta auxiliar, efeito do teste e critério/plano), os campos `*_CN_*`, `*_FS_nucleo_segmento`, `*_FS_plano`, `*_FS_entrada` e `*_FS_funcao_simbolica`. Escreva também a seção 10 completa quando aplicável e as perguntas S05, S06, S11, S12 e S13 do núcleo.
- Com `*_FS_entrada` = "sim", preencha TODA a seção 8 e TODA a seção 9 do princípio (10 hipóteses: `_decisao`, `_evidencia_favoravel`, `_evidencia_contraria`), como no modelo.
- A seção 12 (`S12_*_concretizacao`, `S12_*_funcao_simbolica`, `S12_resolucao_operativa`), quando omitida, é copiada dos blocos de origem.
- Página impressa, origem e conferência ficam por conta do script.

## 6. Ajustes de calibração (valem para todas as decisões)

- **A1:** forma de mobilização "literal" só quando o dispositivo do princípio é citado (art. 176, § 1º; art. 170, III; art. 225). Nome do princípio sem o dispositivo, ou outro dispositivo com o mesmo conteúdo: "conteúdo equivalente demonstrado".
- **A2:** quando a ata adota o resultado "nos termos do voto do Relator", o plano é a decisão institucional, por remissão. Ressalvas de votos convergentes vão para um controle da seção 15.
- **A3:** sem critério densificado, mas com a avaliação aplicável, o alcance é "indeterminado".
- **A4:** marque todos os macrocampos e marcadores auxiliares com apoio documental.
- **A5:** discrepância interna "parcial" quando não há contradição direta, mas há distância entre o compromisso declarado e o critério operativo.
- **Maioria quanto ao fundamento:** razão adicional de um voto rejeitada por outro ministro convergente torna a maioria "parcial".
- **Sem critério demonstrável:** "explicável por outra norma" e contrafactual recebem "Não aplicável — justificar" (instrumento v5.0, 7.x.3).
- **Art. 176, § 1º, usado só como regra de competência,** sem desenvolver a cláusula "interesse nacional": registre o fato, avalie a posição com cuidado e abra um controle S15 marcando "caso-chave para a revisão da pesquisadora".

## 7. Inconsistências e dependências

- Registre em `CTRL_inconsistencias`, com trecho, os erros materiais do acórdão: lei estranha ao caso, parágrafos trocados, número de lei errado, "por maioria" contra ata unânime. Não corrija o texto. Se acórdão e ata divergirem, vale a ata.
- Em `CTRL_dependencias`, registre a aplicação integral de outro precedente do conjunto, cautelar × mérito e julgamentos conjuntos. O conjunto tem: ACO 399 AgR; ADI 2586, 2656, 3352 MC, 3355, 3356, 3357, 3470, 3937, 4031, 4606, 4785, 4786, 4787, 4846, 5077, 6233, 6650, 6672, 7273 MC-Ref, 7273, 7332; ADPF 109, ADPF 935 MC-Ref; RE 228800, RE 1427694 RG, RE 1431558.
- Toda dúvida metodológica vai para `CTRL_pendencias_metodologicas` e, se afetar uma categoria, para um controle S15. Não crie regra nova.
- Nunca ajuste uma categoria só para passar na conferência. Combinação que pareça não prevista vira controle S15.

## 8. Conferência (obrigatória antes de terminar)

Para cada decisão sua, rode a conferência numa pasta temporária SÓ SUA:

```
mkdir -p tmp/ID_DECISAO/j && cp codificacao/ID_DECISAO.json tmp/ID_DECISAO/j/
python3 -I scripts/04_gerar_banco.py tmp/ID_DECISAO/j decisoes.sqlite dicionario_campos.json tmp/ID_DECISAO/banco.xlsx
python3 -I -c "import json;r=json.load(open('tmp/ID_DECISAO/relatorio_conferencia.json'));[print(k,v) for x in r.values() for k,v in x.items()]"
```

- Corrija até zerar: `trechos_nao_localizados`, `fora_do_dominio` e `pendencias_completude`.
- `alertas_compatibilidade`: reexamine a evidência. Se a categoria estiver certa, mantenha-a e documente num controle S15.
- **Não altere** nada em `scripts/`, `dicionario_campos.json`, `decisoes.sqlite`, nem os JSON de outras decisões.

## 9. Relatório final (sua resposta, curta)

Para cada decisão:
- núcleos (total / elegíveis);
- posição e concretização de cada princípio;
- resultado da conferência;
- inconsistências e pendências para a pesquisadora;
- casos-chave.

Não repita o JSON.
