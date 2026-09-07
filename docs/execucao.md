# Execução local

A demonstração usa somente a biblioteca padrão do Python 3. Não exige MATLAB, GPU ou acesso ao projeto original.

Na raiz deste repositório:

```sh
python scripts/demo.py
```

Saída esperada: 100 cenários, 6.100 registros, 85 concluídos até 60 tu, sem chaves duplicadas ou valores não finitos. Os exemplos exibidos incluem um caso concluído e um não concluído.

Os CSVs podem ser abertos diretamente em um editor ou planilha, escolhendo UTF-8, separador vírgula e ponto decimal. O exemplo completo está em `data/EV_00000.xlsx`. `docs/cenarios-exemplo.png` mostra duas curvas já disponíveis. Não é uma nova inferência de rede neural.

Para regenerar apenas a figura:

```sh
python -m pip install matplotlib
python scripts/figura.py
```

O critério de seleção da amostra e a origem dos dados estão em `docs/dados.md`. O CSV de atividades é um extrato numérico da planilha de exemplo.

## Estado do protótipo

O simulador do mestrado gera os cenários que alimentam a proposta. Neste repositório, a consulta em terminal e a figura utilizam resultados já calculados. O próximo incremento é uma tela de seleção e comparação. A execução do simulador e o treinamento das redes permanecem no ambiente do mestrado.
