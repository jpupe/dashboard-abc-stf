# Painel das Decisões do STF em Direito Minerário — Índice A/B/C

Dashboard em Streamlit do projeto de tese de **Suzy Sousa (UFPA)**. Mostra, de forma visual, o resultado da aplicação do
*Instrumento de análise dos núcleos decisórios e de classificação pelo índice A/B/C* (v5.0) a 27 decisões do STF
sobre direito minerário.

> As classificações são um pré-preenchimento assistido por IA e são **provisórias até a validação da pesquisadora**.
> O painel mostra esse aviso enquanto houver classificação não validada.

## Por onde começar

| # | O quê | Onde |
|---|---|---|
| 1 | **Banco para validar**: uma linha por resposta, com trecho, página e justificativa; validação nas colunas amarelas do fim | [`data/banco_ABC_STF_mineracao.xlsx`](data/banco_ABC_STF_mineracao.xlsx) |
| 2 | **Dicionário de dados**: significado de cada coluna e de cada pergunta | [`revisao_pesquisadora/dicionario_dados_banco_ABC.xlsx`](revisao_pesquisadora/dicionario_dados_banco_ABC.xlsx) |
| 3 | **Pendências para revisão**: o que pede decisão da pesquisadora primeiro | [`revisao_pesquisadora/pendencias_para_a_pesquisadora.md`](revisao_pesquisadora/pendencias_para_a_pesquisadora.md) |
| 4 | **Metodologia** para o apêndice da tese | [`METODOLOGIA.docx`](METODOLOGIA.docx) (Word) e [`METODOLOGIA.md`](METODOLOGIA.md) |
| 5 | **Script de extração** dos PDFs | [`metodo/1_extracao/01_extrair_pdfs.py`](metodo/1_extracao/01_extrair_pdfs.py) |

Depois da validação, o Excel preenchido substitui o arquivo de mesmo nome em `data/`, e o painel passa a mostrar as classificações validadas.

## Organização do repositório

```
app.py                      painel (Streamlit)
data/                       banco final e contorno dos estados para o mapa
METODOLOGIA.md / .docx      método completo
revisao_pesquisadora/       pendências e dicionário de dados
metodo/
  1_extracao/               script de extração, inventário e texto das decisões (SQLite)
  2_codificacao/            instruções ao modelo, textos de referência, modelos e calibração
  3_banco_e_conferencia/    dicionário, conferência automática e montagem do banco
```

## O que o painel mostra
- **Painel geral** (inspirado no painel de monitoramento do CNJ): mapa por localidade, detalhamento de cada decisão,
  concretização normativa por categoria, relatores, palavras-chave e a tabela de princípios por núcleo, com trecho
  ilustrativo e página.
- **Índice A/B/C**: resolução operativa (A), posição de cada princípio na fundamentação (B), densificação (C),
  concretização normativa e função simbólica lado a lado.
- **Linha do tempo** das decisões.
- **Ficha da decisão**: resumo, núcleos, classificação dos três princípios e trechos com página.
- **Sobre o método**.

Filtros na barra lateral: classe, período, princípio e decisão.

## Dados
- `data/banco_ABC_STF_mineracao.xlsx` — banco final (aba `Banco`, uma linha por resposta do questionário). É a única
  fonte dos dados do painel.
- `data/brasil_ufs.geojson` — contorno simplificado dos estados, só para desenhar o mapa
  (fonte: codeforamerica/click_that_hood).

Para atualizar o painel depois da validação da pesquisadora, substitua o Excel em `data/` (mesmo nome) e faça commit.

## Metodologia
O método completo (extração, codificação, conferência, calibração, banco e painel) está em
[`METODOLOGIA.md`](METODOLOGIA.md), também disponível em Word ([`METODOLOGIA.docx`](METODOLOGIA.docx)) para o apêndice da tese.
Os arquivos do método estão em `metodo/`, organizados por etapa.

## Rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar no Streamlit Community Cloud (gratuito)
1. Acesse https://share.streamlit.io e entre com a conta do GitHub.
2. Clique em **Create app** → *Deploy a public app from GitHub*.
3. Escolha este repositório, branch `main`, arquivo `app.py`, e defina a URL (ex.: `painel-abc-stf.streamlit.app`).
4. Clique em **Deploy**. O link gerado é o que a banca abre no navegador.
