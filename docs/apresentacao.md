# Roteiro de apresentação

## Pitch da Aula 01

Meu projeto propõe uma ferramenta de geração e análise de cenários para apoiar o planejamento de projetos de pesquisa e desenvolvimento. O usuário é o responsável pelas decisões sobre cronograma e capacidade da equipe. Sem informações sobre a evolução do projeto em diferentes condições, esse responsável precisa decidir com base no plano e na experiência, sem quantificar como retrabalho, trabalho não previsto e pressões podem comprometer a conclusão.

No mestrado, já tenho um simulador dinâmico e um conjunto de 10 mil cenários de um projeto de exemplo, com sete atividades e 61 instantes por cenário. A geração dessas simulações faz parte da proposta: ela permite estimar o progresso sob diferentes hipóteses de execução. Também existem redes ESN, NARX e LSTM que aproximam a curva produzida pelo simulador a partir dos parâmetros do cenário e do tempo.

A hipótese é que a ferramenta melhore a identificação de condições que comprometem a conclusão, em comparação com o planejamento baseado apenas no cronograma, na capacidade prevista e na experiência, sem acesso a cenários simulados. Pretendo comparar acertos, omissões e falsos alertas na identificação de cenários críticos, com e sem as informações da ferramenta. A referência inicial será o desfecho simulado.

A primeira versão utiliza os cenários já gerados para apresentar progresso e conclusão. Para a semana três, a meta é permitir a seleção e comparação dos casos em uma tela. A integração de redes ao serviço pode vir depois, aproveitando o trabalho existente.

O maior risco é a diferença entre o simulador e a execução real. O teste inicial previsto é variar um parâmetro por vez e verificar a coerência das curvas e da conclusão. Os dados disponíveis são sintéticos; uma aplicação operacional dependerá de medições reais e calibração. A entrega inclui o Excel de exemplo, uma amostra com 100 cenários e uma demonstração executável.
