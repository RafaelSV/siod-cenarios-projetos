"""Demonstração da amostra existente. Python 3, sem dependências externas."""
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / 'data' / 'cenarios.csv'
    groups = defaultdict(list)
    keys = set()
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            sid, time = int(row['simulation_id']), float(row['SimTime'])
            key = (sid, time)
            if key in keys:
                raise ValueError(f'Instante duplicado: {key}')
            keys.add(key)
            for name, value in row.items():
                if not math.isfinite(float(value)):
                    raise ValueError(f'Valor inválido: {sid}, {name}')
            groups[sid].append(row)
    if not groups:
        raise ValueError('Amostra vazia')
    completed = 0
    results = []
    for sid, rows in sorted(groups.items()):
        times = [float(row['SimTime']) for row in rows]
        if times != list(range(61)):
            raise ValueError(f'Grade temporal inesperada no cenário {sid}')
        progress = [float(row['PercAccomplished']) for row in rows]
        reached = [t for t, p in zip(times, progress) if p >= 100]
        completed += bool(reached)
        results.append((sid, bool(reached), progress[-1], reached[0] if reached else None))
    print('DADOS SINTÉTICOS - consulta de simulações existentes, sem nova previsão')
    print(f'{len(groups)} cenários; {len(keys)} registros; sem chaves duplicadas ou valores não finitos.')
    print(f'Concluídos até 60 tu: {completed}/{len(groups)} ({completed/len(groups):.1%}).')
    print('Essa frequência descreve a amostra, não a probabilidade real de conclusão.')
    print('Exemplos (um concluído e um não concluído, quando disponíveis):')
    for status in (True, False):
        example = next((r for r in results if r[1] == status), None)
        if example:
            sid, done, final, time = example
            print(f'  Cenário {sid}: progresso final={final:.3f}%; conclusão={time if done else "não observada"} tu')
    print('Colunas:', ', '.join(next(iter(groups.values()))[0]))


if __name__ == '__main__':
    main()
