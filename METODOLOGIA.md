# Metodologia: construção do banco A/B/C e do painel em Streamlit

*Apêndice de método da tese de Suzy Sousa (UFPA).*

Este documento descreve o método empregado na produção de:

- o banco final `data/banco_ABC_STF_mineracao.xlsx`;
- o painel em Streamlit deste repositório (`app.py`).

> **Natureza dos resultados.** As classificações do banco são um **pré-preenchimento assistido por inteligência artificial**. Elas permanecem **provisórias até a validação da pesquisadora**, a quem cabe a decisão final sobre cada uma.

---

## 1. Objetivo e escopo

Foi aplicado o *Instrumento de análise dos núcleos decisórios e de classificação pelo índice A/B/C* (versão 5.0) a um conjunto fechado de **27 decisões do Supremo Tribunal Federal sobre direito minerário**. O resultado foi organizado em um banco de dados auditável, um dicionário de dados e um painel visual.

| Classe | Decisões |
|---|---|
| ACO | ACO 399 AgR |
| ADI | 2586, 2656, 3352 MC, 3355, 3356, 3357, 3470, 3937, 4031, 4606, 4785, 4786, 4787, 4846, 5077, 6233, 6650, 6672, 7273 MC-Ref, 7273, 7332 |
| ADPF | 109, 935 MC-Ref |
| RE | 228800, 1427694 RG, 1431558 |

---

## 2. Fontes metodológicas

A codificação seguiu, nesta ordem de prevalência:

1. o **capítulo 6 da tese** (regras de construção e preenchimento do questionário);
2. o **Instrumento A/B/C, versão 5.0**, com suas categorias, as regras de compatibilidade (seção 7.4) e os requisitos de função simbólica (seção 8.1);
3. o **prompt de análise da pesquisadora (v5.0)**, com as etapas de leitura, triagem, mapa de núcleos, preenchimento, regra de parada e auditoria.

A **fonte primária dos fatos** é exclusivamente o texto de cada decisão. Nenhuma lacuna foi completada com conhecimento externo.

Nenhuma variável, categoria ou regra do instrumento foi criada, excluída ou modificada. As tensões entre o capítulo e o questionário foram registradas como **pendências metodológicas** para a pesquisadora.

---

## 3. Visão geral do procedimento

O procedimento tem três etapas, seguidas da validação humana:

```
PDFs das decisões
   │  (1) EXTRAÇÃO por script: texto página a página, OCR nas páginas escaneadas
   ▼
decisoes.sqlite  ── única fonte de texto da codificação
   │  (2) INTERPRETAÇÃO por modelo de linguagem: leitura integral e preenchimento
   │      do questionário segundo o capítulo de regras e o instrumento
   ▼
um registro por decisão
   │  (3) CONFERÊNCIA AUTOMÁTICA por script: trechos, domínio, completude, compatibilidade
   ▼
banco_ABC_STF_mineracao.xlsx  ──►  (4) VALIDAÇÃO pela pesquisadora
   │
   ▼
painel Streamlit (lê só o Excel)
```

A divisão de tarefas é a seguinte:

- **Scripts:** fazem a extração, a conferência e a montagem do banco.
- **Modelo de linguagem:** faz a leitura interpretativa e o preenchimento, em sessões de trabalho e não por chamadas automatizadas a partir de scripts.
- **Pesquisadora:** valida cada classificação.

---

## 4. Etapa 1: extração do texto

O script `metodo/scripts/01_extrair_pdfs.py` faz a extração em cinco passos:

1. **Extrai o texto página por página** (PyMuPDF). Para cada página guarda o número no PDF, a paginação impressa e a peça a que pertence (ementa, voto, extrato de ata etc.).
2. **Aplica OCR** (Tesseract, português, 300 dpi) às páginas sem camada de texto legível. São 98 páginas, em quatro decisões escaneadas: ADI 2586, ADI 2656, ADI 3352 MC e RE 228800.
3. **Elimina a repetição de conteúdo** que a camada de assinatura digital dos PDFs do STF produz. Quando a página aparece duas vezes, guarda só a cópia mais completa.
4. **Extrai por regra os campos que são só dado:** classe, número, unidade da federação, relator, data, órgão julgador, meio de julgamento e resultado do extrato de ata. Se acórdão e ata divergem, prevalece a ata e a divergência é registrada.
5. **Grava tudo num banco SQLite** (`decisoes.sqlite`): decisões, páginas, metadados e o hash do arquivo de origem.

**Resultado:** 2.154 páginas, com cerca de 671 mil palavras.

Nove decisões longas foram lidas a partir de texto já convertido. São elas: ADI 3356, 3357, 3470, 3937, 4785, 4786, 4787, 7332 e ADPF 109. Nelas, as páginas foram separadas pelo rodapé "Inteiro Teor do Acórdão – Página N de M", que o STF imprime em todas as páginas.

O inventário das decisões (páginas, OCR, peças presentes e tamanho) está em `metodo/inventario.csv`.

---

## 5. Etapa 2: dicionário de dados

O questionário completo, da seção 1 à 16, foi transcrito num **catálogo de 392 perguntas**, gerado pelos scripts `02_dicionario.py` e `03_dicionario_xlsx.py`. Para cada pergunta, o catálogo registra:

- código;
- seção e grupo;
- texto;
- nível (decisão ou núcleo);
- princípio;
- tipo de resposta;
- categorias permitidas;
- regra de entrada.

**Prefixos dos códigos.** Indicam o princípio:

| Prefixo | Princípio |
|---|---|
| `IN_` | Interesse nacional (art. 176, § 1º) |
| `FSP_` | Função social da propriedade (art. 170, III) |
| `MA_` | Meio ambiente ecologicamente equilibrado (art. 225) |

**Sufixos dos códigos.** Indicam o bloco do questionário:

| Sufixo | Bloco |
|---|---|
| `_B_` | Posição na fundamentação |
| `_C_` | Densificação |
| `_AT_` | Atribuição normativa |
| `_CN_` | Concretização |
| `_FS_` | Função simbólica |
| `_ALT_` | Explicações alternativas |
| `_AUS_` | Ausências |

**Campos que acompanham cada classificação.** O questionário pede evidência textual, localização e autoria, justificativa, categoria alternativa e grau de segurança. Esses campos são registrados em colunas próprias da linha da classificação. A coluna "Campos absorvidos" do catálogo indica onde cada campo do instrumento foi registrado.

O dicionário (`metodo/dicionario_dados_banco_ABC.xlsx`) reúne as abas Leia-me, Colunas do banco, Catálogo de perguntas, Regras 7.4 e Marcadores. O catálogo também está disponível em formato de dados (`metodo/dicionario_campos.json`) e em texto (`metodo/catalogo_perguntas.txt`).

---

## 6. Etapa 3: codificação interpretativa

### 6.1 Modelo de IA

| Item | Descrição |
|---|---|
| Modelo | **Claude Opus 5.5**, identificador `claude-opus-5-5`, desenvolvido pela Anthropic |
| Período de uso | 20 a 23 de novembro de 2026 |
| Forma de uso | Sessões de trabalho com acesso ao texto extraído, sem chamadas automatizadas a partir de scripts |
| Instruções | Prompt do projeto, prompt metodológico da pesquisadora, capítulo 6, questionário v5.0 e catálogo de perguntas (consolidados em `metodo/BRIEFING_CODIFICACAO.md`) |

Cada decisão foi lida **integralmente** a partir do banco SQLite. As decisões longas foram lidas em partes (voto a voto) e passaram depois por uma consolidação final do mapa de núcleos, da maioria quanto ao fundamento e das sínteses.

Em razão do volume, a leitura foi distribuída entre instâncias do mesmo modelo, que trabalharam em paralelo com instruções idênticas.

### 6.2 Procedimento por decisão

1. **Leitura e controle documental.** Verifica se as peças permitem reconstruir a decisão institucional. Diferencia o resultado proclamado dos fundamentos que tiveram adesão suficiente.
2. **Triagem e nexo minerário (seções 1 e 2).** Registra:
   - o objeto minerário;
   - a centralidade da mineração;
   - se o caso é limítrofe;
   - os limites do material disponível.
3. **Mapa de núcleos (seção 4).** Um núcleo só é elegível quando reúne, cumulativamente:
   - problema jurídico próprio;
   - fundamentação própria;
   - resposta própria;
   - consequência própria;
   - conexão substantiva com o direito minerário.

   Os núcleos não elegíveis ficam no mapa, com o requisito que faltou. A regra de parada foi avaliada em todas as decisões.
4. **Preenchimento das seções 5 a 16** para cada núcleo elegível, com os três princípios analisados separadamente.
5. **Sustentação de cada classificação substantiva.** Toda classificação traz:
   - um trecho literal curto, de uma única página;
   - a página do PDF;
   - a autoria e o plano (voto, corrente ou decisão institucional);
   - a justificativa;
   - nos casos limítrofes, a categoria alternativa descartada e a razão.
6. **Marcadores do instrumento.** Campos aplicáveis nunca ficam vazios. Quando falta resposta substantiva, usa-se o marcador correspondente:
   - "Não aplicável";
   - "Informação não disponível ou não localizada";
   - "Inconclusivo";
   - "Registro provisório pendente de conferência".
7. **Controles (seção 15).** Cada dúvida capaz de alterar uma categoria vira um registro de controle, para revisão dirigida da pesquisadora.

Os erros materiais dos acórdãos (lei estranha ao caso, número de dispositivo trocado, divergência entre acórdão e ata) foram registrados no controle documental, sem correção do texto. As dependências entre decisões do conjunto também foram registradas: julgamentos conjuntos, cautelar e mérito, aplicação integral de precedente.

### 6.3 Critérios de interpretação uniformes

Para garantir a uniformidade entre decisões, a codificação adotou estes critérios, calibrados pela comparação com o gabarito da pesquisadora:

- **Forma de mobilização.** É "literal" quando o dispositivo do princípio é citado. Fora disso, é "conteúdo equivalente demonstrado".
- **Plano.** Quando a ata adota o resultado "nos termos do voto do Relator", o plano é a decisão institucional, por remissão. As ressalvas de votos convergentes vão para os controles.
- **Alcance.** É "indeterminado" quando não há critério densificado.
- **Maioria quanto ao fundamento.** É "parcial" quando um ministro convergente rejeita uma razão adicional do voto condutor.
- **Discrepância interna.** É "parcial" quando há distância entre o compromisso declarado e o critério operativo, sem que haja contradição.
- **Art. 176, § 1º, usado só como regra de competência.** Registra-se como caso-chave para a revisão da pesquisadora.

### 6.4 Regras de salto do instrumento

Quando o próprio instrumento determina "Não aplicável", o script que monta o banco preenche o marcador e registra a origem "regra de salto". Isso acontece em três situações:

| Situação | O que fica "Não aplicável" |
|---|---|
| Princípio ausente ou só em peça não judicial | Densificação e perguntas condicionadas ao critério |
| Pergunta de entrada da seção 8 negativa | Indicadores de função simbólica e explicações alternativas |
| Regra de entrada da seção 10 não atendida | Campos de ausência |

---

## 7. Etapa 4: conferência automática

Os scripts `conferencia.py` e `04_gerar_banco.py` verificam cada resposta em quatro pontos:

1. **Trechos.** Todo trecho citado deve existir no texto extraído, na página indicada. A comparação tolera hifenização, quebras de linha, aspas e reticências.
2. **Domínio.** Toda categoria usada deve estar entre as permitidas para a pergunta, ou ser um marcador do instrumento.
3. **Completude.** Toda pergunta aplicável deve ter resposta ou marcador.
4. **Compatibilidade.** As combinações devem respeitar as regras da seção 7.4 (posição, densificação, atribuição e concretização) e os requisitos cumulativos da função simbólica (seção 8.1). As sínteses devem ser coerentes com os blocos de origem.

O resultado aparece na coluna "Conferência automática" de cada linha. Os alertas não alteram respostas; a decisão é da pesquisadora.

**Resultado final da conferência:**

| Verificação | Resultado |
|---|---|
| Trechos citados | 2.015, todos localizados na página indicada |
| Categorias fora do domínio | nenhuma |
| Alertas de compatibilidade | nenhum |
| Campos aplicáveis sem resposta | nenhum |

---

## 8. Calibração com o gabarito da pesquisadora

A ADI 3355 foi preenchida manualmente pela pesquisadora e codificada também pelo modelo, para comparação campo a campo dos itens categóricos.

- **Concordância geral:** 84% (98 de 117 itens).
- **Sínteses dos núcleos e da decisão:** 100%.

O número é otimista, porque o gabarito já era conhecido. A medida real de qualidade é a validação da pesquisadora nas demais decisões.

As divergências da calibração deram origem aos critérios uniformes da seção 6.3. O detalhamento por seção está em `metodo/calibracao_ADI_3355.md`.

---

## 9. Etapa 5: o banco final

O banco `banco_ABC_STF_mineracao.xlsx` é gerado por script (`04_gerar_banco.py`) a partir dos registros de cada decisão. Por isso pode ser regerado depois das correções da pesquisadora.

É uma **planilha única em formato longo**, com **uma linha por resposta**:

| Grupo de colunas | Colunas |
|---|---|
| Identificação | Decisão, classe, data do julgamento, nível (decisão ou núcleo), núcleo e título do núcleo |
| Pergunta | Seção, grupo da pergunta, princípio, item (nas tabelas variáveis), código e texto da pergunta, tipo de resposta |
| Resposta e sustentação | Resposta, trecho literal, página do PDF, página impressa, autoria e plano, justificativa, categoria alternativa, segurança |
| Controle | Origem da resposta, resultado da conferência automática |
| Validação (colunas amarelas, no fim) | **Concorda?**, **Correções**, **Comentário** |

Na planilha, o cabeçalho fica congelado e há filtros em todas as colunas. A célula da seção é colorida pelo grupo do questionário. As células com algo a conferir ficam em destaque.

O script `06_verificar_outputs.py` confirma que as colunas do banco correspondem, uma a uma, às do dicionário e que toda pergunta usada existe no catálogo.

| Indicador | Valor |
|---|---|
| Decisões | 27 |
| Páginas lidas | 2.154 (98 por OCR) |
| Núcleos identificados nos mapas | 98 |
| Núcleos elegíveis analisados | 43 |
| Combinações núcleo × princípio | 129 |
| Respostas (linhas do banco) | 16.811 |
| Trechos literais citados e conferidos | 2.015 |
| Registros de controle para revisão dirigida | 115 |

---

## 10. O painel em Streamlit

### 10.1 Propósito e referência visual

O painel apresenta o banco a uma banca de ciências humanas. Por isso foi pensado com acesso gratuito pelo navegador, linguagem simples e poucos números por tela. É publicado no Streamlit Community Cloud.

O layout segue o *Painel de Monitoramento das Decisões da Corte IDH em relação ao Brasil* (CNJ), indicado pela pesquisadora. Dele vêm:

- a faixa de título em degradê azul;
- o mapa por localidade ao lado do detalhamento do caso;
- o gráfico de rosca com o total ao centro;
- os quadros de lista e de palavras-chave;
- a tabela larga de cabeçalho escuro.

### 10.2 ETL

O script `app.py` faz extração, transformação e carga:

1. **Extração.** Lê apenas a aba "Banco" do Excel final. O arquivo `data/brasil_ufs.geojson` contém só o contorno dos estados, usado para desenhar o mapa. A fonte é uma versão simplificada do *click_that_hood*, da Code for America.
2. **Transformação.** Monta três tabelas:
   - **decisões:** objeto, resultado, relator, data e estado de origem;
   - **núcleos:** título, questão e resolução operativa;
   - **núcleo × princípio:** posição, densificação, atribuição, concretização, função simbólica, trecho ilustrativo com página e situação da validação.

   Os marcadores do instrumento são mantidos como categorias próprias. Uma classificação conta como validada quando a coluna "Concorda?" está preenchida.
3. **Carga.** Os dados ficam em memória, com cache do Streamlit.

### 10.3 Conteúdo

- **Aviso.** Enquanto houver classificação não validada, o painel mostra um aviso permanente com a quantidade pendente.
- **Indicadores.** Decisões, núcleos analisados, período coberto e classificações validadas.
- **Painel geral:**
  - mapa das decisões por estado de origem;
  - detalhamento de cada decisão;
  - rosca da concretização normativa;
  - relator e órgão julgador;
  - palavras-chave (macrocampos e marcadores do instrumento);
  - tabela de princípios por núcleo, com trecho ilustrativo, página e situação da validação.
- **Índice A/B/C:**
  - resolução operativa (A);
  - posição de cada princípio na fundamentação (B);
  - densificação (C);
  - concretização normativa e função simbólica, lado a lado.
- **Linha do tempo.** Decisões por data e classe; núcleos concretizadores por ano e princípio.
- **Ficha da decisão.** Objeto, resultado, núcleos e a classificação dos três princípios, com o trecho do acórdão e a página.
- **Sobre o método.** Explicação do índice em linguagem simples.
- **Filtros.** Classe processual, período, princípio e decisão.

No mapa, cada decisão aparece na capital do estado de origem do processo. As ações contra leis federais aparecem em Brasília. O mapa é desenhado a partir do contorno dos estados guardado no próprio repositório e não depende de serviço externo. O painel foi testado com o `AppTest` do Streamlit, com e sem filtros.

### 10.4 Atualização

Após a validação da pesquisadora, a atualização do painel consiste na substituição de `data/banco_ABC_STF_mineracao.xlsx` por um arquivo de mesmo nome no repositório. O painel recalcula as contagens, e o aviso desaparece quando todas as classificações estiverem validadas.

---

## 11. Papel da pesquisadora

A pesquisadora revisa cada resposta nas colunas amarelas do banco: **Concorda?** (sim, não ou parcialmente), **Correções** e **Comentário**.

Para orientar a revisão, há dois apoios:

- **Registros de controle da seção 15**, localizáveis no banco pelo filtro da coluna "Grupo da pergunta".
- **Documento `metodo/pendencias_para_a_pesquisadora.md`.** Reúne:
  - as escolhas de uniformização entre decisões julgadas em conjunto;
  - os casos-chave do interesse nacional;
  - as questões de método que o instrumento não resolve.

---

## 12. Limitações

1. **Pré-preenchimento.** Até a validação, as classificações refletem a leitura do modelo orientada pelo instrumento.
2. **Calibração.** A concordância com o gabarito da ADI 3355 está inflada pelo conhecimento prévio do gabarito.
3. **Texto convertido.** Nove decisões longas foram lidas de texto convertido, com a paginação reconstituída pelo rodapé do STF.
4. **OCR.** Quatro decisões antigas são escaneadas. Trechos ilegíveis não foram usados como evidência.
5. **Votos ausentes.** Em algumas decisões não constam os votos escritos de parte dos ministros, o que limita a reconstrução da maioria quanto ao fundamento.
6. **Julgamentos conjuntos.** Decisões julgadas em conjunto foram codificadas separadamente, pela leitura de cada uma. As diferenças de classificação entre elas estão registradas para uniformização pela pesquisadora.

---

## 13. Reprodutibilidade

Os scripts do método estão em `metodo/scripts/`. A ordem de execução é:

```bash
python 01_extrair_pdfs.py PASTA_PDFS --textos PASTA_TXT --db decisoes.sqlite
python 00_inventario.py decisoes.sqlite
python 02_dicionario.py
python 03_dicionario_xlsx.py dicionario_campos.json dicionario_dados_banco_ABC.xlsx
python 04_gerar_banco.py PASTA_JSON decisoes.sqlite dicionario_campos.json banco_ABC_STF_mineracao.xlsx
python 06_verificar_outputs.py banco_ABC_STF_mineracao.xlsx dicionario_dados_banco_ABC.xlsx
```

| Componente | Versão |
|---|---|
| Python | 3.13 |
| PyMuPDF | 2.1 |
| Tesseract OCR | 5.3.4 (dados `por`) |
| pytesseract | 0.3.13 |
| openpyxl | 3.1.5 |
| pandas | 3.0.5 |
| Streamlit | 1.67 |
| Plotly | 7.1 |

O banco SQLite com o texto extraído das 27 decisões está em `metodo/decisoes.sqlite`, e três registros de codificação usados como modelo (ADI 3355, ADI 6650 e ADI 7273 MC-Ref) estão em `metodo/codificacao/`. Os PDFs das decisões e os demais registros por decisão ficam no projeto da pesquisadora. O painel depende apenas do Excel final.
