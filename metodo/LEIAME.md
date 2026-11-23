# Método

Arquivos do método, organizados pelas etapas descritas em `METODOLOGIA.md` (na raiz do repositório).

| Pasta | Etapa | Conteúdo principal |
|---|---|---|
| `1_extracao/` | Extração do texto dos PDFs | `01_extrair_pdfs.py` (script de extração), `00_inventario.py`, `requirements_extracao.txt`, `inventario.csv` e o banco `decisoes.sqlite` com o texto das 27 decisões |
| `2_codificacao/` | Codificação interpretativa | `BRIEFING_CODIFICACAO.md` (instruções dadas ao modelo), textos de referência (capítulo 6, questionário, prompt da pesquisadora, catálogo de perguntas), `dump_texto.py`, três registros de codificação usados como modelo e o relatório de calibração |
| `3_banco_e_conferencia/` | Dicionário, conferência e montagem do banco | `02_dicionario.py`, `03_dicionario_xlsx.py`, `04_gerar_banco.py`, `conferencia.py`, `06_verificar_outputs.py`, `estilo_abc.py`, `dicionario_campos.json` e `dicionario_dados_banco_ABC.xlsx` |
