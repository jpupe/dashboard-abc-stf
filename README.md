# Painel das Decisões do STF em Direito Minerário — Índice A/B/C

Dashboard em Streamlit do projeto de tese de **Suzy Sousa (UFPA)**. Mostra, de forma visual, o resultado da aplicação do
*Instrumento de análise dos núcleos decisórios e de classificação pelo índice A/B/C* (v5.0) a 27 decisões do STF
sobre direito minerário.

> As classificações são um pré-preenchimento assistido por IA e são **provisórias até a validação da pesquisadora**.
> O painel mostra esse aviso enquanto houver classificação não validada.

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
Os scripts, o dicionário de dados e os documentos de apoio estão em `metodo/`.

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
