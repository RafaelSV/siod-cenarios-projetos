# Roteiro de apresentação

## Pitch da Aula 01

Meu projeto propõe uma ferramenta de geração e análise de cenários para apoiar o planejamento de projetos de pesquisa e desenvolvimento. O usuário é o responsável pelas decisões sobre cronograma e capacidade da equipe. Sem informações sobre a evolução do projeto em diferentes condições, esse responsável precisa decidir com base no plano e na experiência, sem quantificar como retrabalho, trabalho não previsto e pressões podem comprometer a conclusão.

No mestrado, já tenho um simulador dinâmico e um conjunto de 10 mil cenários de um projeto de exemplo, com sete atividades e 61 instantes por cenário. A geração dessas simulações faz parte da proposta: ela permite estimar o progresso sob diferentes hipóteses de execução. Também existem redes ESN, NARX e LSTM que aproximam a curva produzida pelo simulador a partir dos parâmetros do cenário e do tempo.

A hipótese é que a ferramenta melhore a identificação de condições que comprometem a conclusão, em comparação com o planejamento baseado apenas no cronograma, na capacidade prevista e na experiência, sem acesso a cenários simulados. Pretendo comparar acertos, omissões e falsos alertas na identificação de cenários críticos, com e sem as informações da ferramenta. A referência inicial será o desfecho simulado.

A primeira versão utiliza os cenários já gerados para apresentar progresso e conclusão. Para a semana três, a meta é permitir a seleção e comparação dos casos em uma tela. A integração de redes ao serviço pode vir depois, aproveitando o trabalho existente.

O maior risco é a diferença entre o simulador e a execução real. O teste inicial previsto é variar um parâmetro por vez e verificar a coerência das curvas e da conclusão. Os dados disponíveis são sintéticos; uma aplicação operacional dependerá de medições reais e calibração. A entrega inclui o Excel de exemplo, uma amostra com 100 cenários e uma demonstração executável.

## Pitch da Aula 02

Na Aula 1, defini o problema de apoiar o planejamento de projetos de P&D por meio da comparação de cenários de execução. Nesta segunda etapa, implementei a primeira pipeline reproduzível que transforma os resultados do simulador em dados estruturados para as etapas posteriores da ferramenta.

A entrada principal é o diretório com as simulações em arquivos `.mat`. Como o conjunto completo possui 10 mil arquivos e ocupa aproximadamente 1,53 GB, ele não foi incluído no repositório. Para permitir a reprodução da entrega, a pipeline também pode começar em um dataset intermediário com 100 cenários já publicado no projeto. Existe ainda um modo que somente converte as simulações para esse dataset intermediário.

No fluxo completo, a implementação em Python valida a estrutura de cada simulação, extrai os cinco parâmetros do cenário, o tempo e as séries do projeto, e monta os tensores de entrada e saída. Em seguida, seleciona `PercAccomplished` como alvo, divide os cenários entre treino, validação e teste e calcula a normalização apenas com o conjunto de treino, evitando vazamento de informação.

A pipeline produz três saídas: o NPZ normalizado para treinamento, um JSON com o esquema e os parâmetros de normalização, e um CSV com o resumo legível de cada cenário. Na amostra publicada, foram processados 100 cenários com 61 instantes, divididos em 70 para treino, 15 para validação e 15 para teste. O resumo identificou 85 cenários concluídos e 15 não concluídos no horizonte, sem descarte ou correção de registros.

A implementação mostrou que a conversão dos `.mat` pode ser feita sem disponibilizar o código privado do simulador e que o dataset existente já contém as sequências necessárias para o treinamento. Também deixou claro que a preparação precisa separar cenários antes de normalizar e oferecer saídas diferentes para consumo técnico e para conferência humana. Com isso, a camada de dados está pronta para a etapa de treinamento e posterior uso das estimativas na comparação de alternativas de planejamento.
