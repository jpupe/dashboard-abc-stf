# 1. Extração do texto

| Arquivo | Descrição |
|---|---|
| `01_extrair_pdfs.py` | Extrai o texto dos PDFs página por página, aplica OCR (Tesseract, português) às páginas escaneadas e grava tudo em SQLite. Instruções de uso no cabeçalho do script. |
| `requirements_extracao.txt` | Bibliotecas Python necessárias ao script (além do Tesseract OCR com o idioma português). |
| `00_inventario.py` | Gera o inventário das decisões a partir do banco SQLite. |
| `inventario.csv` | Inventário: páginas, OCR, peças presentes, tamanho e observações de cada decisão. |
| `decisoes.sqlite` | Banco com o texto extraído das 27 decisões (tabelas `decisoes`, `paginas`, `metadados`, `execucoes` e `inventario`). |

Uso: `python 01_extrair_pdfs.py PASTA_DOS_PDFS [--textos PASTA_TXT] [--db decisoes.sqlite]`
