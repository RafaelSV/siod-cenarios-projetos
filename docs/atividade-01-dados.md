# Atividade 01 — Caracterização e avaliação inicial dos dados

**Projeto:** Análise de cenários de execução de projetos de P&D

**Responsável:** Rafael S. Valadão

## 1. Fonte e critério de seleção

A fonte principal é o conjunto de resultados do simulador dinâmico utilizado no mestrado. Ele representa a execução de um projeto sob hipóteses de retrabalho, trabalho não previsto, pressão de cronograma, pressão gerencial e variação da capacidade. Esses dados sustentam a comparação de condições que podem comprometer a conclusão e apoiar decisões de planejamento.

Esta atividade analisa `data/simulacoes_100/dataset_projeto.npz`, com **100 cenários sintéticos**, e `data/EV_00000.xlsx`, que descreve o projeto de exemplo. O arquivo `metadata.json`, na mesma pasta do NPZ, descreve seus campos. A geração dos cenários faz parte da proposta, mas o código do simulador permanece no ambiente do mestrado. As curvas são resultados calculados, não observações de execução real.

A seleção toma os índices NumPy **0, 100, 200, ..., 9900** do conjunto original de 10.000 cenários. Cada caso preserva seus 61 instantes. A regra é determinística, não filtra resultados favoráveis e limita o tamanho da entrega. Entretanto, a seleção sistemática pode refletir a ordem dos dados e **não garante representatividade estatística**. Ela é adequada para verificar estrutura, qualidade e viabilidade inicial, não para estimar probabilidades operacionais.

## 2. Caracterização técnica

| Aspecto | Caracterização |
|---|---|
| Origem e produção | Experimentos do simulador do mestrado, lote `20260818_225211`; organização dos experimentos e da amostra por Rafael S. Valadão |
| Obtenção | Extração dos resultados previamente calculados; cópia da planilha de exemplo |
| Acesso | Arquivos locais incluídos no repositório do projeto; consulta não exige o simulador |
| Formato principal | NPZ comprimido e metadados JSON UTF-8; CSV adicional para consulta |
| Estrutura | NPZ com eixos cenário, instante e variável; IDs originais no vetor `simulation_id`. Na tabela em memória, a chave é `simulation_id` + `SimTime` |
| Dimensão da amostra | 100 cenários; X com dimensão (100, 61, 6), Y com (100, 61, 19). O notebook seleciona 10 colunas e produz 6.100 linhas em memória. NPZ de 289.088 bytes; CSV de 565.695 bytes |
| Dimensão da origem | 10.000 cenários da mesma estrutura de projeto; contagem registrada em `data/proveniencia.json` |
| Intervalo temporal | 0 a 60 tu, com passo de 1 tu e 61 instantes por cenário |
| Excel | 20.752 bytes; abas `Projeto`, `Equipe` e `Atividades`; cadastro de um projeto, quatro membros de exemplo e sete atividades |
| Atualização | Por execução de novos experimentos; sem periodicidade fixa de coleta |
| Restrições | Somente o exemplo e resultados sintéticos integram a entrega; código do simulador e cadastros de outros projetos não são disponibilizados |
| Rastreabilidade | Hashes SHA-256 do NPZ, metadados e Excel; correspondência numérica com o CSV existente |

O cadastro do projeto ocupa `Projeto!A2:H2`, a equipe principal `Equipe!A2:M5` e as atividades `Atividades!A2:AR8`. Notas e tabelas auxiliares fora desses blocos não são registros do cadastro principal. O notebook lê diretamente o Excel, sem depender do CSV auxiliar de atividades.

## 3. Avaliação inicial da qualidade

| Verificação | Resultado na amostra |
|---|---|
| Valores ausentes na tabela analisada | 0 em todas as 10 colunas (0%) |
| Valores não finitos na tabela analisada | 0 |
| Linhas integralmente duplicadas | 0 |
| Chaves cenário/instante duplicadas | 0 |
| Nomes de colunas duplicados | 0 |
| Grade temporal | Todos os 100 cenários possuem exatamente os instantes 0 a 60 |
| Parâmetros dentro do mesmo cenário | Constantes nos 61 instantes, conforme a estrutura experimental |
| Combinações de parâmetros repetidas entre cenários | 0 |
| Valores fora dos intervalos experimentais documentados | 0 |
| Progresso fora de 0 a 100% ou com quedas | 0; tolerância de 10⁻⁶ na verificação de quedas |
| Trabalho realizado ou restante negativo | 0 |
| Formato/codificação | NPZ numérico e metadados JSON UTF-8; tabela conferida contra o CSV UTF-8 existente |
| Ausentes nos oito campos de atividades selecionados | 0 |
| Ausentes em ID, nome, dedicação e capacidade dos quatro membros | 0 |
| IDs de atividade ou membro duplicados | 0 nos blocos principais |
| Duração e esforço das atividades | Duração = término − início; esforço = duração × taxa, dentro da tolerância numérica |
| Predecessoras | Sem referências inválidas, ciclos, autorreferências ou início anterior ao término de predecessor |
| Fórmulas do Excel | 427 fórmulas; nenhuma sem resultado armazenado e nenhum erro de célula detectado; o notebook lê os resultados armazenados. Recálculo de teste após a remoção da aba, com Artifact Tool, sem erros detectados |

Há três cuidados de interpretação e preparação:

- **Estrutura do Excel:** a aba `Equipe` inclui tabelas auxiliares com valores numéricos abaixo do cadastro. Uma leitura da aba inteira como uma única tabela produziria falsos membros, ausências e duplicidades. O notebook delimita o primeiro bloco contíguo antes de avaliar a qualidade.
- **Tipos e identificadores:** `predecessoras` mistura cinco inteiros e duas listas em texto. O valor 0 indica ausência de predecessora. O cadastro usa `EV-00000`, enquanto o nome do arquivo usa `EV_00000`; uma integração deve mapear essa diferença explicitamente. Os nomes de pessoas e atividades são genéricos, sem necessidade de agrupamento por grafias variantes nesta amostra.
- **Referência temporal:** a planilha informa 12 meses, equivalentes a 52,8 tu pela convenção de 4,4 semanas por mês. O último término de atividade é 45 tu, e a simulação vai até 60 tu. São referências diferentes. A análise usa conclusão até o horizonte de 60 tu, sem declarar atraso contratual a partir desse indicador.

Faltam trajetórias reais de progresso para calibração e validação, uma definição única de prazo para alertas de atraso e cenários controlados que variem um parâmetro por vez para investigar seu efeito isolado. A amostra contém somente uma estrutura de projeto, sem evidência de generalização para outras estruturas.

## 4. Dicionário mínimo

Tipos abaixo descrevem a interpretação dos campos. Exemplos numéricos longos estão arredondados para leitura; os arquivos preservam os valores originais.

| Campo | Significado | Tipo | Exemplo | Observação / problema |
|---|---|---|---|---|
| `simulation_id` | Índice do cenário na origem | Inteiro | 0 | Base zero; não é ID de projeto real |
| `Expected_Rew` | Hipótese de retrabalho | Decimal (%) | 4,793 | Parâmetro experimental, constante no cenário |
| `Expected_WU` | Hipótese de trabalho não previsto | Decimal (%) | 6,848 | Não é medição real de escopo adicional |
| `PCronograma` | Pressão de cronograma no modelo | Decimal (%) | 4,914 | Interpretação definida pelo modelo |
| `PGestor` | Pressão gerencial no modelo | Decimal (%) | 29,610 | Não é avaliação observada de um gestor |
| `Variacao_Capacidade_Base_Pct` | Variação sobre a capacidade de base | Decimal (%) | 21,126 | Valores negativos representam redução |
| `SimTime` | Instante da simulação | Numérico (tu) | 0 | Passo 1; não contém data de medição real |
| `PercAccomplished` | Progresso calculado pelo simulador | Decimal (%) | 7,875 | Limiar de conclusão: 100%; não presumir equivalência direta com WD dividido pelo esforço planejado |
| `WD` | Trabalho realizado | Decimal (wu) | 4.692,197 | O trabalho executado pode incluir efeitos da dinâmica; não é percentual |
| `WRemaining` | Trabalho restante | Decimal (wu) | 50.234,172 | Não é tempo restante |
| `project_id` | Identificador no cadastro | Texto | EV-00000 | Difere da grafia no nome do arquivo |
| `project_cost_tu` | Duração em tu usada no cadastro | Decimal (tu) | 52,8 | Nome pode sugerir custo, mas a nota da planilha indica semanas |
| `task_id` | Identificador da atividade | Inteiro | 1 | Chave no projeto de exemplo |
| `expected_ini_tu` | Início planejado | Numérico (tu) | 0 | Coordenada temporal da atividade |
| `expected_end_tu` | Término planejado | Numérico (tu) | 12 | Não confundir com horizonte do experimento |
| `expected_duration` | Duração planejada | Numérico (tu) | 12 | Conferida contra término menos início |
| `expected_wu` | Esforço planejado | Decimal (wu) | 11.580 | Soma das atividades: 54.912 wu |
| `expected_workrate` | Taxa planejada | Decimal (wu/tu) | 965 | Conferida contra esforço e duração |
| `predecessoras` | Atividades que devem terminar antes | Inteiro ou texto | `1,2,3` | Converter para lista; 0 significa nenhuma |
| `dedication_tu` | Tempo de dedicação do membro | Decimal (tu) | 52,8 | Campo do bloco principal da equipe |
| `capacity` | Capacidade semanal do membro | Decimal (wu/tu) | 300 | Capacidade de base, não a variação percentual do cenário |
| `concluiu_ate_60` | Indicador derivado de conclusão até 60 tu | Booleano | Verdadeiro | Exige pelo menos um instante com progresso ≥ 100% |
| `tempo_conclusao_tu` | Primeiro instante de conclusão | Decimal anulável (tu) | 43 | Ausente quando a conclusão não foi observada no horizonte |
| `deficit_final_pp` | Diferença positiva entre 100% e progresso final | Decimal (pp) | 3,871 | Pontos percentuais, não trabalho em wu |

## 5. Análise exploratória reproduzível

O notebook [01_exploracao_dados.ipynb](../notebooks/01_exploracao_dados.ipynb) carrega o recorte local, verifica os hashes e a correspondência com o CSV, delimita as tabelas do Excel e executa as inspeções acima. Os gráficos ficam incorporados às células: distribuição dos cinco parâmetros, mediana e amplitude das curvas de progresso e distribuição do tempo de conclusão.

As distribuições dos parâmetros usam **uma linha por cenário**, evitando tratar suas 61 repetições como novas observações independentes. A amplitude entre curvas não é intervalo de confiança. A comparação exploratória não estima causalidade nem calibra probabilidades de projetos reais.

| Indicador | Resultado nos 100 cenários |
|---|---:|
| Concluídos até 60 tu | 85 |
| Não concluídos até 60 tu | 15 |
| Frequência de conclusão | 85% |
| Tempo médio de conclusão, somente entre concluídos | 48,235 tu |
| Mediana do tempo de conclusão, somente entre concluídos | 47 tu |
| Progresso final médio | 98,772% |
| Déficit final médio entre os não concluídos | 8,188 pp |

O NPZ também preserva os indicadores originais de conclusão. Os 15 tempos de conclusão ausentes, recalculados pelo notebook, representam ausência de conclusão observada, não falha de coleta. Não são preenchidos com zero nem com o limite de 60 tu. Esses campos adicionais não entram na contagem de ausências das 10 colunas analisadas. A frequência de 86,74% na origem aparece apenas como referência de procedência; os resultados desta entrega se referem à amostra de 100.

### Reprodução

No ambiente Python do notebook, instale `pandas`, `numpy`, `openpyxl`, `matplotlib` e `ipykernel`. Abra o notebook pela raiz do projeto ou pela pasta `notebooks` e execute todas as células. A primeira célula registra as versões das bibliotecas usadas.

O caminho de entrada fica em `ARQUIVO_CENARIOS`, na primeira célula de código:

```python
ARQUIVO_CENARIOS = DATA / 'simulacoes_100' / 'dataset_projeto.npz'
```

O NPZ e seu `metadata.json` estão em `data/simulacoes_100/`. Todos os arquivos necessários à execução estão no repositório.

## 6. Síntese técnica

**Disponibilidade.** Os dados necessários à análise inicial de cenários estão disponíveis: o Excel de um projeto de exemplo e 100 trajetórias sintéticas completas, extraídas de uma base de 10.000 cenários. O notebook carrega a amostra sem o simulador e reproduz sua caracterização. Isso sustenta a exploração do comportamento modelado, mas não demonstra previsão operacional de projetos reais.

**Principal problema.** A limitação principal é a representatividade: a amostra vem de uma única estrutura e de uma seleção sistemática sem garantia estatística. O CSV não apresentou ausentes ou duplicidades. No Excel, notas, blocos auxiliares e tipos mistos de predecessoras exigem delimitação e tratamento antes de uma integração automatizada.

**Informações faltantes.** Não há histórico real de progresso confirmado para calibração ou validação. Também falta definir a referência de prazo para um alerta de atraso: o término das atividades, a duração cadastrada e o horizonte simulado são diferentes. Os cenários analisados não foram construídos para isolar o efeito de uma única variável.

**Efeito sobre a proposta.** A análise preserva o problema, a hipótese e a arquitetura da Aula 01: apoiar o planejamento com geração e análise de cenários. Ela delimita os indicadores como resultados sintéticos dentro de um horizonte definido. A comparação de decisões com e sem a ferramenta ainda precisa ser avaliada; não se infere esse benefício somente pela qualidade técnica dos arquivos.

**Risco principal.** O risco é transferir diretamente o comportamento do simulador para decisões reais, interpretando frequências amostrais como probabilidades ou não conclusão até 60 tu como atraso contratual. A evolução exige calibração com observações reais, definição do prazo e avaliação em outras estruturas de projeto. A ampliação para 10.000 cenários melhora a cobertura do experimento, mas não elimina essas limitações.
