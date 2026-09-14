# Execução local

## Pipeline de dados

A pipeline exige Python 3 e as bibliotecas listadas em `requirements.txt`. Não exige MATLAB, GPU nem acesso ao código do simulador.

Para não interferir nas bibliotecas de outros projetos, crie um ambiente virtual na raiz deste repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts/pipeline.py
```

Sem argumentos, a pipeline executa o modo `dataset`, lê `dataset_projeto.npz` e `metadata.json` em `data/simulacoes_100/` e grava as três saídas em `data/processed/`.

### Formas de execução

Começar no dataset padrão:

```powershell
.\.venv\Scripts\python scripts/pipeline.py
```

Começar em outro dataset:

```powershell
.\.venv\Scripts\python scripts/pipeline.py dataset CAMINHO/DATASET
```

`CAMINHO/DATASET` é a pasta que contém obrigatoriamente `dataset_projeto.npz` e `metadata.json`. A ausência de qualquer um deles interrompe a execução com uma mensagem de erro.

Executar todo o fluxo a partir das simulações:

```powershell
.\.venv\Scripts\python scripts/pipeline.py simulations CAMINHO/SIMULACOES
```

Gerar somente o dataset intermediário:

```powershell
.\.venv\Scripts\python scripts/pipeline.py generate-dataset CAMINHO/SIMULACOES
```

Nesse último modo, a saída padrão é `data/generated/`, contendo `dataset_projeto.npz` e `metadata.json`.

O diretório de saída é o único parâmetro opcional adicional:

```powershell
.\.venv\Scripts\python scripts/pipeline.py dataset CAMINHO/DATASET --output-dir CAMINHO/SAIDA
.\.venv\Scripts\python scripts/pipeline.py simulations CAMINHO/SIMULACOES --output-dir CAMINHO/SAIDA
.\.venv\Scripts\python scripts/pipeline.py generate-dataset CAMINHO/SIMULACOES --output-dir CAMINHO/SAIDA
```

### Validação com poucas simulações

`--max-simulations` limita a quantidade de arquivos lidos e é destinado principalmente à validação da pipeline. O valor mínimo é sete para que treino, validação e teste não fiquem vazios.

```powershell
.\.venv\Scripts\python scripts/pipeline.py simulations CAMINHO/SIMULACOES --max-simulations 10 --output-dir CAMINHO/TESTE
```

O split usa internamente a regra fixa 42. Esse número inicializa a seleção pseudoaleatória dos cenários e faz com que a mesma entrada gere sempre a mesma divisão. Ele não precisa ser informado na chamada.

Os logs padrão mostram o modo selecionado, os diretórios, a quantidade de arquivos, o progresso da leitura, a estrutura encontrada, o split, a normalização, as validações e a gravação. Por isso, não existe uma opção adicional de log detalhado.

Os arquivos `.mat` ocupam aproximadamente 1,53 GB e não fazem parte do repositório. O código Python que os lê está em `scripts/gerar_dataset.py`, e o recorte de 100 cenários permite executar a entrega sem esses arquivos.

### Saída esperada com o recorte publicado

```text
INFO | Pipeline iniciada.
INFO | Modo: fluxo a partir do dataset já criado.
INFO | Dataset validado: 100 cenários, 61 instantes e alvo PercAccomplished.
INFO | Divisão por cenário validada: 70 treino, 15 validação e 15 teste.
INFO | dataset_esn.npz: 100 cenários, 61 instantes, alvo PercAccomplished.
INFO | Resumo: 85 concluídos e 15 não concluídos até o horizonte.
INFO | Pipeline concluída com sucesso.
```

## Consulta da saída anterior

A demonstração da tabela temporal da Atividade 01 continua disponível e usa somente a biblioteca padrão do Python 3:

```sh
python scripts/demo.py
```

Ela apresenta 100 cenários, 6.100 registros e exemplos concluído e não concluído. O CSV pode ser aberto em um editor ou planilha usando UTF-8, separador vírgula e ponto decimal. O exemplo do projeto está em `data/EV_00000.xlsx`.
