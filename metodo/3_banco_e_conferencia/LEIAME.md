# 3. Dicionário, conferência e montagem do banco

| Arquivo | Descrição |
|---|---|
| `02_dicionario.py` | Transcreve o questionário no catálogo de perguntas e gera `dicionario_campos.json`. |
| `03_dicionario_xlsx.py` | Gera o dicionário de dados em Excel. |
| `04_gerar_banco.py` | Monta o banco final (formato longo) a partir dos registros de cada decisão, aplica as regras de salto e a conferência automática. |
| `conferencia.py` | Verificações de trechos, domínio, completude e compatibilidade (usado pelo `04`). |
| `06_verificar_outputs.py` | Confere a correspondência entre o banco e o dicionário. |
| `estilo_abc.py` | Cores e estilos comuns às planilhas (usado pelo `03` e pelo `04`). |
| `dicionario_campos.json` | Catálogo de perguntas em formato de dados. |
| `dicionario_dados_banco_ABC.xlsx` | Dicionário de dados em Excel. |
