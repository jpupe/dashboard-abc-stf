# Metodologia: construção do banco A/B/C e do painel em Streamlit

*Relatório de método para o apêndice da tese de Suzy Sousa (UFPA). Versão de 23/11/2026.*

Este documento descreve como foram produzidos:

- o banco final `data/banco_ABC_STF_mineracao.xlsx` (planilha única, uma linha por resposta do questionário);
- o painel em Streamlit deste repositório (`app.py`).

Ele registra o que foi de fato executado, os números obtidos, as ferramentas usadas e as limitações.

> **Natureza dos resultados.** Todas as classificações do banco são um **pré-preenchimento assistido por inteligência artificial**. Elas permanecem **provisórias até a validação da pesquisadora**, a quem cabe a decisão final sobre cada uma. O banco tem colunas próprias para essa validação.

---

## 1. Objetivo e escopo

O objetivo foi aplicar o *Instrumento de análise dos núcleos decisórios e de classificação pelo índice A/B/C* (versão 5.0) a um conjunto fechado de **27 decisões do Supremo Tribunal Federal sobre direito minerário** e transformar o resultado em:

- um banco de dados auditável;
- um dicionário de dados;
- um painel visual para a banca.

O escopo foi definido pela pesquisadora: os 27 PDFs da pasta do projeto cujo nome começa por ADI, ACO, ADPF ou RE. Nenhuma decisão de fora desse conjunto foi incluída.

| Classe | Decisões |
|---|---|
| ACO | ACO 399 AgR |
| ADI | 2586, 2656, 3352 MC, 3355, 3356, 3357, 3470, 3937, 4031, 4606, 4785, 4786, 4787, 4846, 5077, 6233, 6650, 6672, 7273 MC-Ref, 7273, 7332 |
| ADPF | 109, 935 MC-Ref |
| RE | 228800, 1427694 RG, 1431558 |

Duas inclusões ficaram registradas no controle do banco:

- **ADPF 935 MC-Ref (cavidades naturais subterrâneas):** a triagem automática da planilha de seleção a havia excluído; a pesquisadora a incluiu na revisão.
- **ACO 399 AgR:** consta como "não selecionada" na planilha de seleção, mas está na pasta do projeto.

---

## 2. Fontes metodológicas e hierarquia

A codificação seguiu, nesta ordem de prevalência:

1. **Capítulo 6 da tese**, com as regras de construção e preenchimento do questionário.
2. **Instrumento A/B/C, versão 5.0**: o questionário, suas categorias, as regras de compatibilidade (seção 7.4) e os requisitos de função simbólica (seção 8.1).
3. **Prompt de análise elaborado pela pesquisadora (v5.0).** Todas as suas regras analíticas foram mantidas:
   - etapas de leitura, triagem, mapa de núcleos e preenchimento;
   - regra de parada;
   - separação entre resolução operativa, posição, densificação, atribuição, concretização e função simbólica;
   - tratamento das ausências;
   - auditoria.

   Só o formato de saída foi adaptado: em vez de um DOCX por decisão, um registro estruturado por decisão, consolidado no banco.

**Fonte primária dos fatos.** É exclusivamente o texto de cada decisão, extraído para o banco SQLite (seção 4). Nenhuma lacuna foi completada com conhecimento externo, memória, internet ou suposição.

**Regras não alteradas.** Nenhuma variável, categoria ou regra foi criada, excluída, renomeada ou fundida. Tensões ou lacunas entre o capítulo e o questionário foram registradas como **pendências metodológicas** para a pesquisadora, sem que se inventasse uma regra.

---

## 3. Visão geral do procedimento

O procedimento aprovado pela pesquisadora tem três etapas, seguidas da validação humana:

```
PDFs das decisões
   │  (1) EXTRAÇÃO por script: texto página a página, OCR nas páginas escaneadas
   ▼
decisoes.sqlite  ── única fonte de texto da codificação
   │  (2) INTERPRETAÇÃO por modelo de linguagem: leitura integral e preenchimento
   │      do questionário, seguindo o capítulo de regras e o instrumento
   ▼
um registro (JSON) por decisão
   │  (3) CONFERÊNCIA AUTOMÁTICA por script: trechos, domínio, completude, compatibilidade
   ▼
banco_ABC_STF_mineracao.xlsx  ──►  (4) VALIDAÇÃO pela pesquisadora (colunas amarelas)
   │
   ▼
painel Streamlit (lê só o Excel)
```

A leitura interpretativa e o preenchimento dos campos **não foram feitos por um script que chama a IA**. Foram feitos pelo modelo de linguagem em sessões de trabalho, lendo o texto extraído (seção 6). Os scripts cuidam só da extração, da conferência e da montagem do banco.

---

## 4. Etapa 1: inventário e extração do texto (script `01_extrair_pdfs.py`)

### 4.1 Inventário

As 27 decisões somam **2.154 páginas** e cerca de **671 mil palavras**. Para cada decisão foram registrados:

- número de páginas;
- existência de camada de texto;
- presença das peças (ementa, acórdão, relatório, votos, extrato de ata);
- faixa de tamanho.

Nove decisões têm mais de 70 páginas e foram lidas em partes. O inventário completo está em `metodo/inventario.csv`.

### 4.2 Extração

O script `metodo/scripts/01_extrair_pdfs.py`:

- **Seleciona os arquivos** cujo nome começa por ADI, ACO, ADPF ou RE e avisa se não encontrar exatamente 27.
- **Extrai o texto página por página** com PyMuPDF, guardando a página do PDF, a paginação impressa (quando localizável) e a peça (ementa, voto, extrato de ata etc.).
- **Aplica OCR** (Tesseract, idioma português, 300 dpi) às páginas sem texto legível. Conta como sem texto legível a página com menos de 20 palavras de três ou mais letras; o critério evita confundir capas escaneadas com camada residual de letras soltas. Foram **98 páginas de OCR**, todas em quatro decisões escaneadas: ADI 2586, ADI 2656, ADI 3352 MC e RE 228800.
- **Remove a duplicação da camada de texto.** Nos PDFs de inteiro teor do STF, a camada de texto de muitas páginas traz a mesma página duas vezes, uma por camada de assinatura digital. Quando uma cópia está contida na outra, o script guarda só a mais completa e marca a página. Isso ocorreu em **2.031 páginas**. Nenhum texto distinto é descartado.
- **Extrai por regra os campos que são só dado** (tabela `metadados`):
  - classe, número, unidade da federação, relator, redator e data;
  - órgão julgador e meio de julgamento;
  - resultado do extrato de ata (a última entrada "Decisão:");
  - comparação "unanimidade × maioria" entre acórdão e ata.

  Quando acórdão e ata divergem, prevalece a ata e a divergência é registrada. Foi assim que o script detectou sozinho o erro material da ADI 7273 MC-Ref: o texto do acórdão diz "por maioria" e a ata registra unanimidade.
- **Grava tudo em SQLite** (`decisoes.sqlite`), nas tabelas `decisoes`, `paginas`, `metadados`, `execucoes` e `inventario`, com o hash SHA-256 do arquivo de origem. O script pode ser executado de novo sem duplicar registros.

### 4.3 Fonte provisória em texto

Nove decisões longas estavam no projeto apenas como **texto já convertido**, sem o PDF original, por limite de armazenamento do projeto: ADI 3356, 3357, 3470, 3937, 4785, 4786, 4787, 7332 e ADPF 109 (1.530 páginas no total).

O script lê esses textos com a opção `--textos` e separa as páginas pelo rodapé "Inteiro Teor do Acórdão – Página N de M", que o STF imprime em todas as páginas. A origem dessas páginas fica registrada como `texto_projeto`.

Quando os PDFs originais forem anexados, basta reexecutar o script: o PDF sempre prevalece sobre o texto.

---

## 5. Etapa 2: dicionário de dados e catálogo de perguntas

### 5.1 Transcrição do questionário

O questionário completo, seções 1 a 16, foi transcrito em uma lista ordenada de campos (`metodo/scripts/02_dicionario.py`). Para cada campo foram registrados:

- seção e bloco;
- descrição;
- nível (decisão ou núcleo) e princípio;
- tipo de resposta (categoria única ou múltipla, texto, evidência, dado);
- categorias permitidas e regra de entrada;
- origem do preenchimento.

Os blocos que se repetem por princípio recebem prefixos:

- `IN_`: interesse nacional, art. 176, § 1º;
- `FSP_`: função social da propriedade, art. 170, III;
- `MA_`: meio ambiente ecologicamente equilibrado, art. 225.

Dentro de cada princípio, os sufixos indicam a dimensão:

| Sufixo | Dimensão |
|---|---|
| `_B_` | Dimensão B (posição na fundamentação) |
| `_C_` | Dimensão C (densificação) |
| `_AT_` | Atribuição normativa e contrafactual |
| `_CN_` | Concretização normativa |
| `_FS_` | Indicadores de função simbólica |
| `_ALT_H01…H10_` | As dez explicações alternativas |
| `_AUS_` | Ausências |

### 5.2 Formato longo

Na primeira versão, o banco foi pensado com uma linha por núcleo e uma coluna por campo, o que dava 685 colunas. Depois da primeira entrega, o formato foi revisto para o **formato longo**: **uma linha por resposta**, com as colunas Decisão, Núcleo, Grupo da pergunta, Princípio, Pergunta do questionário e Resposta.

Motivos da mudança:

- **Filtrar fica simples.** Por exemplo, "todas as decisões × posição do interesse nacional".
- **A validação passa a ser por resposta,** e não por linha de 685 campos.
- **Tabelas de tamanho variável** (mapa de núcleos, categorias prevalentes, registros de controle) viram apenas mais linhas, sem máximo de colunas.
- **O painel** consome o formato longo diretamente.

### 5.3 Campos absorvidos

O questionário pede, junto de cada classificação, evidência textual, localização e autoria, justificativa, categoria alternativa e grau de segurança. Esses campos **não viram linhas próprias**. Eles ficam nas colunas Trecho, Página PDF, Página impressa, Autoria e plano, Justificativa, Categoria alternativa e razão e Segurança da linha da classificação.

O catálogo registra, para cada pergunta, quais campos do instrumento ela absorve (coluna "Campos absorvidos"). Assim, nenhum campo do questionário se perde.

### 5.4 Resultado

- **392 perguntas no catálogo**, que equivalem aos 685 campos do formato largo.
- **28 colunas no banco.**

O dicionário (`dicionario_dados_banco_ABC.xlsx`, gerado por `03_dicionario_xlsx.py`) tem cinco abas: Leia-me, Colunas do banco, Catálogo de perguntas, Regras 7.4 e Marcadores.

---

## 6. Etapa 3: codificação interpretativa

### 6.1 Modelo de IA e forma de uso

| Item | Descrição |
|---|---|
| Modelo | **Claude Opus 5.5**, identificador `claude-opus-5-5`, desenvolvido pela Anthropic |
| Período de uso | 20 a 23 de novembro de 2026 |
| Forma de uso | Sessões de trabalho no ambiente do Claude, com acesso ao texto extraído e às ferramentas de leitura de arquivos. Sem chamadas automatizadas de API a partir de scripts. |
| Instruções dadas ao modelo | O prompt do projeto; o prompt metodológico da pesquisadora (v5.0, `metodo/BRIEFING_CODIFICACAO.md` e regras nele referidas); o capítulo 6; o questionário v5.0; o catálogo de perguntas |
| Unidade de trabalho | Uma decisão por vez, lida **integralmente** a partir do banco SQLite, com marcadores de página |

### 6.2 Procedimento por decisão

O procedimento seguiu as etapas do prompt metodológico da pesquisadora.

1. **Leitura e controle documental.** O modelo leu todas as peças, verificou se elas permitiam reconstruir a decisão institucional e diferenciou o resultado proclamado dos fundamentos com adesão suficiente.
2. **Triagem e nexo minerário (seções 1 e 2).** Identificou o objeto minerário, a centralidade, se o caso é limítrofe e os limites do material.
3. **Mapa e elegibilidade dos núcleos (seção 4).**
   - Um núcleo só é elegível com problema, fundamentação, resposta e consequência próprios, cumulativamente, e com conexão substantiva com o direito minerário.
   - Votos e correntes não criam núcleos.
   - Os núcleos não elegíveis ficam no mapa, com o requisito não demonstrado.
   - A regra de parada foi avaliada em todas as decisões. Nenhuma das 27 ficou sem núcleo elegível.
4. **Preenchimento completo das seções 5 a 16** para cada núcleo elegível, com os três princípios analisados separadamente.
5. **Registro da sustentação.** Toda classificação substantiva traz:
   - trecho literal curto, de uma única página;
   - página do PDF;
   - autoria e plano (voto, corrente ou decisão institucional);
   - justificativa;
   - nos casos limítrofes, a categoria alternativa descartada e a razão.
6. **Marcadores do instrumento.** Campos aplicáveis nunca ficaram vazios. Quando não havia resposta substantiva, foi usado o marcador correspondente: "Não aplicável", "Informação não disponível ou não localizada", "Inconclusivo", "Campo aplicável ainda não preenchido" ou "Registro provisório pendente de conferência".
7. **Controles (seção 15).** Toda dúvida que pudesse alterar uma categoria virou um registro de controle, para revisão dirigida da pesquisadora. Nenhuma categoria foi ajustada só para "caber" nas regras.

**Decisões longas.** Foram lidas em partes, voto a voto ou por blocos de páginas, com notas por parte e uma passada final de consolidação para o mapa de núcleos, a maioria quanto ao fundamento e as sínteses. As partes lidas ficaram registradas no campo `CTRL_partes_processadas` de cada decisão.

**Erros materiais dos acórdãos.** Lei estranha ao caso, número de lei ou de parágrafo trocado, "por maioria" contra ata unânime e situações semelhantes foram registrados em `CTRL_inconsistencias`, sem corrigir o texto da decisão.

### 6.3 Regras de salto aplicadas por script

Quando o próprio instrumento determina "Não aplicável", o script que monta o banco preenche o marcador e registra a origem "regra de salto":

- posição *Ausente* ou *Presença documental não judicial* → densificação e perguntas condicionadas ao critério;
- pergunta de entrada da seção 8 negativa → indicadores da seção 8 e explicações alternativas da seção 9;
- regra de entrada da seção 10 não atendida → campos da seção 10.

As sínteses da seção 12, quando não escritas, são copiadas dos blocos de origem.

### 6.4 Organização do trabalho

**Primeiras decisões.** As três primeiras (ADI 3355, ADI 6650 e ADI 7273 MC-Ref) foram codificadas na sessão principal e serviram de modelo de formato.

**Demais decisões.** As 24 restantes, que somam cerca de 600 mil palavras, foram distribuídas entre **14 instâncias auxiliares do mesmo modelo**, executadas em paralelo:

- uma por decisão longa;
- uma para cada grupo de três decisões curtas ou médias.

**Instruções comuns.** Todas receberam o mesmo pacote: `metodo/BRIEFING_CODIFICACAO.md` com as regras, os ajustes de calibração e os modelos.

**Fechamento de cada instância.** Cada uma só terminou depois de zerar, na conferência automática da sua decisão:

- trechos não localizados;
- categorias fora do domínio;
- campos pendentes.

**Interrupções.** As execuções foram interrompidas duas vezes por limite de uso da conta. Todas foram retomadas do ponto em que pararam, sem perda nem recomeço.

---

## 7. Etapa 4: conferência automática (`conferencia.py` e `04_gerar_banco.py`)

Para cada resposta, o script verifica:

1. **Trechos.** O trecho citado existe no texto do banco SQLite, na página indicada.
   - A comparação tolera hifenização, quebras de linha, aspas e espaços, e aceita reticências para elipses.
   - Se o trecho não estiver na página indicada, o script procura nas vizinhas e avisa.
   - Trechos que atravessam a quebra de página são aceitos quando as duas páginas juntas os contêm.
2. **Domínio.** Toda categoria usada está entre as permitidas para a pergunta, ou é um marcador do instrumento.
3. **Completude.** Toda pergunta aplicável tem resposta ou marcador.
4. **Compatibilidade.** O script aplica as regras da seção 7.4, combinando posição, densificação, atribuição e concretização:
   - Ausente exige densificação "Não aplicável" e concretização "Não mobilizado".
   - Concretização no caso ou institucional exige todos os seus requisitos.
   - Voto não prevalecente não admite densificação institucional.

   Aplica também os requisitos cumulativos de "Função simbólica demonstrada" (seção 8.1) e verifica a coerência entre as sínteses da seção 12 e os blocos de origem.

O resultado de cada linha fica na coluna **Conferência automática**, e o resumo por decisão fica em `relatorio_conferencia.json`. Alertas de compatibilidade não alteram respostas: a decisão é da pesquisadora.

**Testes da conferência.** Ela foi testada com casos negativos (trecho inventado, página errada, categoria inexistente, combinação incompatível) para confirmar que detecta erros.

**Correções durante a codificação.** A conferência identificou trechos citados que atravessavam quebras de página com cabeçalho no meio, ou que dependiam de texto removido do arquivo de leitura. Esses trechos foram substituídos por trechos equivalentes da mesma página.

**Resultado final.**

| Verificação | Resultado |
|---|---|
| Trechos citados | **2.015**, todos localizados na página indicada |
| Categorias fora do domínio | 0 |
| Alertas das regras 7.4 e 8.1 | 0 |
| Campos aplicáveis sem resposta | 0 |

---

## 8. Etapa 5: calibração com o gabarito da pesquisadora (ADI 3355)

A ADI 3355, preenchida manualmente pela pesquisadora, foi codificada pelo modelo e comparada campo a campo com o gabarito. A comparação considerou os itens categóricos comparáveis.

- **Concordância:** **84% (98 de 117 itens)**. Nas sínteses das seções 12 e 14, foi de **100%**.
- **Ressalva:** esse número é **otimista**. O gabarito já havia sido lido no projeto piloto, e o teste real é a validação nas demais decisões.

Detalhes por seção estão em `metodo/calibracao_ADI_3355.md`.

As divergências levaram a cinco ajustes de interpretação, aplicados a todas as decisões seguintes:

| Ajuste | Regra adotada |
|---|---|
| A1 | Forma de mobilização "literal" só quando o dispositivo do princípio é citado |
| A2 | Quando a ata adota o resultado "nos termos do voto do Relator", o plano é a decisão institucional, por remissão |
| A3 | Sem critério densificado, o alcance é "indeterminado" |
| A4 | Registro de todos os macrocampos e marcadores com apoio documental |
| A5 | Discrepância interna "parcial" quando há distância, sem contradição, entre o compromisso declarado e o critério operativo |

Duas divergências foram mantidas e encaminhadas à pesquisadora, por envolverem a hierarquia entre fontes:

- maioria quanto ao fundamento "parcial" × "identificável";
- "Não aplicável — justificar" no contrafactual sem critério, como manda o instrumento v5.0, × "sim", como marcado no gabarito.

---

## 9. Etapa 6: o banco final (`banco_ABC_STF_mineracao.xlsx`)

O banco é gerado por script (`04_gerar_banco.py`) a partir dos registros de cada decisão. Assim, pode ser **regerado** depois das correções da pesquisadora.

**Estrutura.** Planilha única "Banco", com 16.811 linhas e 28 colunas:

| Grupo | Colunas |
|---|---|
| Identificação | ID da linha, ID da decisão, Decisão, Classe, Data do julgamento |
| Localização da pergunta | Nível (decisão ou núcleo), Núcleo, Título do núcleo, Seção, Grupo da pergunta, Princípio, Item (para as tabelas variáveis) |
| Pergunta | ID da pergunta, Pergunta do questionário, Tipo de resposta |
| Resposta e sustentação | Resposta, Trecho (evidência literal), Página PDF, Página impressa (lida automaticamente do SQLite), Autoria e plano, Justificativa, Categoria alternativa e razão, Segurança |
| Controle | Origem da resposta, Conferência automática |
| Validação (colunas amarelas, no fim) | **Concorda?**, **Correções**, **Comentário** |

**Formatação.**

- cabeçalho congelado e filtros em todas as colunas;
- quebra de texto nas colunas longas;
- célula "Seção" colorida pelo grupo do questionário, na paleta do piloto aprovado;
- células de conferência alaranjadas quando há algo a conferir.

**Coerência com o dicionário.** O script `06_verificar_outputs.py` verifica três coisas:

- as colunas do banco coincidem, uma a uma e na mesma ordem, com a aba "Colunas do banco" do dicionário;
- todo código de pergunta usado existe no catálogo;
- os identificadores de linha são únicos.

### 9.1 Números do banco

| Indicador | Valor |
|---|---|
| Decisões | 27 |
| Páginas lidas | 2.154 (98 por OCR) |
| Núcleos identificados nos mapas | 98 |
| Núcleos elegíveis analisados | 43 |
| Combinações núcleo × princípio | 129 |
| Respostas (linhas do banco) | 16.811 |
| Respostas da leitura interpretativa (LLM) | 12.433 |
| Respostas por regra de salto do instrumento | 4.034 |
| Sínteses copiadas e contagens por script | 344 |
| Trechos literais citados e conferidos | 2.015 |
| Registros de controle (seção 15) para revisão dirigida | 115 |

---

## 10. O painel em Streamlit (`app.py`)

### 10.1 Escolha da ferramenta

O painel foi feito para uma banca de ciências humanas, pouco habituada a ferramentas de dados. Por isso, os requisitos foram:

- acesso gratuito pelo navegador;
- linguagem simples;
- poucos números por tela.

O Power BI foi descartado por causa da licença. O Streamlit permite publicar de graça no Streamlit Community Cloud, com um link que a banca abre sem instalar nada.

**Referência visual.** O layout segue o "Painel de Monitoramento das Decisões da Corte IDH em relação ao Brasil" (CNJ, Unidade de Monitoramento e Fiscalização), indicado pela pesquisadora como inspiração. Dele vêm:

- a faixa de título em degradê azul;
- o mapa por localidade ao lado do detalhamento do caso, em faixas azuis;
- o gráfico de rosca com o total ao centro;
- os quadros de lista e de palavras-chave;
- a tabela larga de cabeçalho escuro.

### 10.2 ETL

O script segue o fluxo extração → transformação → carga.

1. **Extração.** Lê **apenas** a aba "Banco" do Excel final, com o caminho configurável no topo do script. O painel não lê os PDFs, o SQLite nem os registros intermediários. A única exceção é o arquivo `data/brasil_ufs.geojson`, que traz só o contorno dos estados, usado para desenhar o mapa.
2. **Transformação.**
   - Monta a tabela de **decisões**: uma linha por decisão, com objeto, resultado, relator, data, ano e estado de origem.
   - Monta a tabela de **núcleos**: uma linha por núcleo elegível, com título, questão e resolução operativa.
   - Monta a **visão longa núcleo × princípio**, uma linha por combinação, a partir dos códigos `IN_`, `FSP_` e `MA_`. Cada linha traz posição (B), densificação (C), atribuição, concretização, função simbólica e o trecho ilustrativo com página.
   - Mantém os **marcadores de dados como categorias próprias**: eles não são descartados.
   - Considera **validada** a combinação núcleo × princípio cuja linha de concretização tem a coluna "Concorda?" preenchida.
3. **Carga.** Os dados ficam em memória com cache do Streamlit (`st.cache_data`).

### 10.3 Conteúdo

**Aviso permanente.** Enquanto houver classificação não validada, o painel mostra quantas faltam e lembra que os resultados são provisórios.

**Indicadores do topo.** Decisões, núcleos analisados, período coberto e classificações validadas.

**Abas.**

| Aba | Conteúdo |
|---|---|
| Painel geral | Mapa das decisões por estado de origem; detalhamento de cada decisão (objeto e resultado); rosca da concretização normativa (núcleo × princípio); relator e órgão julgador; palavras-chave (macrocampos e marcadores do instrumento); tabela de princípios por núcleo, com posição, concretização, função simbólica, trecho ilustrativo, página e situação da validação |
| Índice A/B/C | Dimensão A (resolução operativa); Dimensão B (posição de cada princípio na fundamentação, lado a lado); Dimensão C (densificação); concretização normativa e função simbólica, lado a lado |
| Linha do tempo | Decisões por data e classe, coloridas pela concretização do meio ambiente; núcleos concretizadores por ano e princípio |
| Ficha da decisão | Objeto, resultado, relator, núcleos e classificação dos três princípios, com o trecho do acórdão e a página; inconsistências documentais registradas |
| Sobre o método | Explicação em linguagem simples do índice e do procedimento |

**Filtros na barra lateral.** Classe processual, período, princípio e decisão.

**Rodapé.** Remete a este apêndice de método.

### 10.4 Decisões técnicas

**Mapa.** É desenhado como um gráfico comum, com longitude e latitude, a partir do contorno dos estados guardado no repositório. A versão inicial usava um fundo de mapa externo e falhou num ambiente sem acesso à internet. O contorno é uma versão simplificada do arquivo `brazil-states.geojson` do projeto *click_that_hood* (Code for America).

**Posição das decisões no mapa.**

- Cada decisão fica na capital do estado de origem do processo.
- Ações contra leis federais aparecem em Brasília.
- Decisões do mesmo estado ficam num pequeno círculo em volta da capital.

**Tabelas.** São renderizadas em HTML com rolagem, para reproduzir o visual do painel de referência. Os textos vindos do banco são escapados antes da exibição.

**Testes.** O painel foi testado com o `AppTest` do próprio Streamlit, com e sem filtros, sem nenhuma exceção. A aparência de cada aba foi conferida por capturas de tela num navegador sem interface.

### 10.5 Publicação e atualização

Para publicar, siga o passo a passo do `README.md`: em share.streamlit.io, crie o app a partir deste repositório (branch `main`, arquivo `app.py`).

Para atualizar o painel depois da validação da pesquisadora, substitua `data/banco_ABC_STF_mineracao.xlsx` por um arquivo de mesmo nome e faça commit. O painel recalcula as contagens, e o aviso de validação some quando todas as classificações estiverem validadas.

---

## 11. Papel da pesquisadora

O modelo fez um **pré-preenchimento**. A pesquisadora revisa cada resposta nas colunas amarelas do banco:

- **Concorda?**: sim, não ou parcialmente;
- **Correções**;
- **Comentário**.

Para orientar a revisão, foram preparados:

- **Os registros de controle da seção 15**, para revisão dirigida. Para vê-los, filtre a coluna "Grupo da pergunta" pela seção 15.
- **O documento `metodo/pendencias_para_a_pesquisadora.md`**, que reúne:
  - as escolhas de uniformização entre decisões julgadas em conjunto (grupo do amianto; ADIs 4785, 4786 e 4787);
  - os casos-chave do interesse nacional, em que o art. 176, § 1º, aparece só como regra de competência ou não é mobilizado;
  - as dúvidas de inclusão e de regra de parada;
  - as questões de método que o instrumento não resolve.

Nenhuma categoria foi alterada para uniformizar decisões, porque essa decisão cabe à pesquisadora. Depois das correções, o banco é regerado por script e o painel passa a mostrar as classificações validadas.

---

## 12. Limitações

1. **Natureza provisória.** Até a validação, as classificações refletem a leitura do modelo, orientada pelo instrumento, e não a decisão da pesquisadora.
2. **Concordância com o gabarito.** Os 84% da ADI 3355 estão inflados pelo conhecimento prévio do gabarito.
3. **Fonte em texto.** Nove decisões longas foram lidas do texto convertido do projeto, e não do PDF original. A paginação foi reconstituída pelo rodapé do STF.
4. **OCR.** Quatro decisões antigas são escaneadas. Na ADI 3352 MC há trechos ilegíveis, que não foram usados como evidência e estão registrados como limite documental.
5. **Votos ausentes.** Em várias decisões não constam os votos escritos de parte dos ministros, o que limita a reconstrução da maioria quanto ao fundamento.
6. **Leitura distribuída.** As decisões longas foram lidas em partes, e as 24 decisões finais foram codificadas por instâncias paralelas do mesmo modelo, com as mesmas instruções. Entre decisões julgadas em conjunto, isso produziu **divergências de critério**, que ficaram registradas para uniformização pela pesquisadora.
7. **Extração por regra.** Metadados como relator e data foram lidos por expressões regulares e conferidos na leitura interpretativa. Em páginas de OCR, alguns não foram extraídos automaticamente e foram preenchidos na leitura.

---

## 13. Reprodutibilidade

**Scripts.** Estão em `metodo/scripts/`:

| Script | Função |
|---|---|
| `01_extrair_pdfs.py` | Extração dos PDFs para SQLite (página a página, OCR, metadados) |
| `00_inventario.py` | Inventário e controle documental |
| `02_dicionario.py` | Dicionário de campos e catálogo de perguntas |
| `03_dicionario_xlsx.py` | Geração do dicionário em Excel |
| `04_gerar_banco.py` | Banco longo a partir dos registros por decisão, com regras de salto e conferência |
| `conferencia.py` | Verificações de trechos, domínio, completude e compatibilidade |
| `06_verificar_outputs.py` | Coerência entre banco e dicionário |
| `dump_texto.py` | Texto de leitura com marcadores de página |
| `listar_perguntas.py` | Catálogo em texto |
| `estilo_abc.py` | Paleta e estilos comuns |

**Ordem de execução.**

```bash
python 01_extrair_pdfs.py PASTA_PDFS --textos PASTA_TXT --db decisoes.sqlite
python 00_inventario.py decisoes.sqlite
python 02_dicionario.py
python 03_dicionario_xlsx.py dicionario_campos.json dicionario_dados_banco_ABC.xlsx
python 04_gerar_banco.py PASTA_JSON decisoes.sqlite dicionario_campos.json banco_ABC_STF_mineracao.xlsx
python 06_verificar_outputs.py banco_ABC_STF_mineracao.xlsx dicionario_dados_banco_ABC.xlsx
```

**Versões usadas.**

| Componente | Versão |
|---|---|
| Python | 3.13 |
| PyMuPDF | 2.1 |
| Tesseract OCR | 5.3.4, dados `por` |
| pytesseract | 0.3.13 |
| openpyxl | 3.1.5 |
| pandas | 3.0.5 |
| Streamlit | 1.67 |
| Plotly | 7.1 |

**Arquivos que não estão neste repositório.** Os PDFs das decisões, o banco SQLite e os registros intermediários por decisão ficam no projeto da pesquisadora. O painel depende apenas do Excel final.
