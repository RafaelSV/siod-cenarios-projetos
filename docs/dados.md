# Dados disponíveis e limites da proposta

## Fonte principal utilizável agora

Os resultados foram produzidos pelo simulador do projeto `modelagem_leizer-main`. O conjunto utilizado é `Resultados_MC/20260818_225211/Dataset_Redes_Python`. São 10.000 cenários de uma estrutura de projeto com sete atividades e 61 instantes em unidades de tempo (`tu`), sem conversão automática para dias ou meses. Trabalho usa unidades de trabalho (`wu`).

O arquivo NPZ contém `X` com dimensão `(10000, 61, 6)` e `Y` com dimensão `(10000, 61, 19)`. As cinco hipóteses do cenário permanecem constantes no tempo. `SimTime` é a sexta entrada. O código `Avaliacao_incertezas.m` configura intervalos de 0 a 30 para retrabalho, trabalho não previsto e pressões, e de -20% a +30% para variação de capacidade. Esses intervalos são escolhas experimentais, sem calibração empírica demonstrada nesta entrega.

Os dados já estão disponíveis localmente. Sua geração é parte da proposta: o simulador estima a evolução do projeto sob diferentes hipóteses, produzindo informações para avaliar alternativas de planejamento. A atualização ocorre por nova execução de experimentos. Responsável pela amostra: Rafael S. Valadão.

## Amostra incluída

- `data/simulacoes_100/dataset_projeto.npz`: recorte dos 100 cenários, preservando entradas, 19 saídas, indicadores de conclusão e IDs originais. O notebook da Atividade 01 lê esta cópia local; os nomes dos campos estão em `data/simulacoes_100/metadata.json`.
- `data/cenarios.csv`: 100 cenários, 6.100 registros, 10 colunas. Seleção dos índices NumPy 0, 100, ..., 9900, sem seleção por desfecho. Cada linha representa um instante de um cenário.
- `data/EV_00000.xlsx`: projeto de exemplo, com as abas `Projeto`, `Equipe` e `Atividades`. Os nomes dos membros e descrições de atividades são genéricos (`Name 01`, `Descrição Atividade 1` etc.). A planilha inclui fórmulas, predecessoras e parâmetros de planejamento. A aba `TabelaSIGITEC` foi removida preventivamente para reduzir o risco de exposição de dados sigilosos.
- `data/atividades.csv`: sete atividades e seis atributos numéricos extraídos de `Modelo/EV_00000.xlsx`, para leitura rápida. Não inclui a rede de predecessoras. A planilha de exemplo preserva a estrutura completa do arquivo de entrada.
- `data/proveniencia.json`: regra de seleção, contagens verificadas e hashes SHA-256 da fonte NPZ e dos CSVs. Os hashes são apenas registros informativos de proveniência e não são usados como validação bloqueante pela pipeline.

A amostra contém resultados existentes e tem finalidade demonstrativa. Ela não deve substituir o conjunto completo para treinamento ou estimativas de frequência. O código do simulador e do estimador permanece no ambiente do mestrado; a leitura dos `.mat` e a preparação do dataset desta atividade estão versionadas neste repositório.

## Saídas preparadas pela pipeline

A execução padrão começa no recorte publicado em `data/simulacoes_100/` e grava três arquivos em `data/processed/`:

- `dataset_esn.npz`: entrada técnica para treinamento, com `X` de dimensão `(100, 61, 6)`, `Y` de dimensão `(100, 61, 1)`, identificadores dos cenários e índices de treino, validação e teste;
- `metadata_esn.json`: nomes dos campos, dimensões, regra do split e médias e desvios necessários para aplicar e inverter a normalização;
- `resumo_cenarios.csv`: uma linha por cenário, com os cinco parâmetros, conjunto atribuído, progresso final, indicação de conclusão, tempo de conclusão e percentual faltante.

O alvo selecionado é `PercAccomplished`. O split é feito por cenário, com 70 casos para treino, 15 para validação e 15 para teste na amostra publicada. Média e desvio são calculados exclusivamente com o conjunto de treino e depois aplicados aos três conjuntos. Portanto, o NPZ processado é adequado como entrada da etapa de treinamento, enquanto o CSV serve para conferência e análise legível dos resultados.

A pipeline também pode começar diretamente no diretório das simulações `.mat`. Nesse modo, ela lê a estrutura do projeto e as séries temporais em Python, gera o dataset intermediário e continua pela mesma preparação. O modo `generate-dataset` encerra após criar `dataset_projeto.npz` e `metadata.json` na mesma pasta.

## Dicionário mínimo

| Campo | Significado e unidade |
|---|---|
| `simulation_id` | Índice original do cenário no NPZ, base zero; não identifica uma pessoa ou um projeto real |
| `Expected_Rew` | Hipótese percentual de retrabalho |
| `Expected_WU` | Hipótese percentual de trabalho não previsto |
| `PCronograma` | Parâmetro percentual de pressão de cronograma no modelo |
| `PGestor` | Parâmetro percentual de pressão gerencial no modelo |
| `Variacao_Capacidade_Base_Pct` | Variação percentual da capacidade em relação à base |
| `SimTime` | Instante de simulação em tu, de 0 a 60 |
| `PercAccomplished` | Percentual de progresso calculado pelo simulador |
| `WD` | Trabalho realizado, em wu |
| `WRemaining` | Trabalho restante, em wu |
| `task_id` | Identificador numérico da atividade no plano representativo |
| `expected_ini_tu`, `expected_end_tu` | Início e término planejados, em tu |
| `expected_duration` | Duração planejada, em tu |
| `expected_wu` | Esforço planejado, em wu |
| `expected_workrate` | Taxa planejada de trabalho, em wu/tu |

A chave do CSV de cenários é `(simulation_id, SimTime)`. Os campos são numéricos, com ponto decimal. Nenhum campo publicado é um histórico observado de execução real.

## Auditoria executada

O conjunto completo possui 8.674 cenários que atingem 100% até 60 tu e 1.326 que não atingem. A amostra tem 85 concluídos e 15 não concluídos. Portanto, a frequência da amostra (85%) difere da frequência do conjunto (86,74%). Nenhuma das duas é uma probabilidade calibrada de sucesso de projetos reais.

As matrizes de entrada e saída do conjunto completo não têm NaN ou infinito. Os 1.326 NaNs em `TempoConclusaoProjeto` correspondem aos cenários sem conclusão observada até o horizonte. Esse indicador não foi imputado. Na demonstração, ele é recalculado como o primeiro instante com `PercAccomplished >= 100`. Ausência de conclusão até 60 tu não significa que o projeto nunca terminará.

Os índices de treino, validação e teste têm 7.000, 1.500 e 1.500 elementos, sem sobreposição e cobrindo os 10.000 cenários. Isso verifica separação entre cenários, mas não prova generalização a novas estruturas de projeto ou a projetos reais.

Na execução publicada da pipeline, os 100 cenários foram processados sem descarte, correção ou alerta. As três saídas foram reabertas e tiveram dimensões e contagens conferidas. A desnormalização recuperou os valores originais dentro da precisão `float32`, e o resumo reproduziu os indicadores calculados diretamente da trajetória de `PercAccomplished`.

O fluxo iniciado nos arquivos `.mat` foi validado com dez simulações. Foram encontradas sete tarefas, 61 instantes e 53 séries em cada arquivo; o dataset intermediário coincidiu com o resultado produzido anteriormente para os mesmos casos. Essa execução valida a reprodução técnica da conversão, mas não substitui a avaliação do conjunto completo nem a validação do simulador com projetos reais.

## Dados cadastrais disponíveis, não publicados

A planilha `Projetos/EVsprojetosSIGITEC/dados_sigitec_projetos.xlsx` tem 10 registros de projetos, 144 de equipe e 155 de atividades, contando linhas com primeira coluna preenchida, sem contar formatação residual. Os cabeçalhos abrangem cadastro, orçamento, equipe, datas e atividades. A inspeção não confirmou uma série com data de medição e percentual efetivamente executado. Cadastro de planejamento e trajetória de execução são fontes diferentes.

`EV_Floco.xlsx` e o cadastro SIGITEC não foram incluídos. A entrega disponibiliza o exemplo `EV_00000.xlsx`, seu extrato numérico e saídas sintéticas.

## Limites de capacidade identificados no código

| Componente existente | O que foi confirmado | Limite da conclusão |
|---|---|---|
| `Modelo/RodaSimulacao.m` | Carrega projeto e parâmetros e chama o simulador | Não recebe automaticamente medições de um sistema real |
| `scripts/gerar_dataset.py` | Lê os `.mat` e monta o dataset de projeto com parâmetros, tempo e resultados | Não coleta novos projetos reais |
| `scripts/pipeline.py` | Valida, divide e normaliza as sequências para a ESN | A rede agregada ainda não recebe como entradas as datas e o plano de qualquer novo projeto |
| `RedesPython/config.py` | Configuração padrão prevê `PercAccomplished` com ESN, NARX e LSTM | Comparação entre redes é avaliação computacional do simulador |
| `estima_parametros/roda_estimador.m` | Por padrão gera nova simulação de `EV_00000` e amostra 0, 5, 10, 15 e 20% do tempo | Essas medições são sintéticas, não evidência real |
| `estima_parametros/estimador_tasks.m` | Extrai curvas de `P.Runtime(...).SimData` | Uso de histórico real exige entrada compatível, adaptação e validação |

Não foram executados MATLAB, CasADi, treinamento de redes ou validação com gestores nesta entrega. Executaram-se a extração, a auditoria dos dados e a demonstração de consulta. Não há otimização automática de recursos nem recomendação causal de intervenção comprovada.
