"""Figura científica de dois cenários existentes, sem inferência ou nova simulação."""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
groups = defaultdict(list)
with (ROOT/'data/cenarios.csv').open(encoding='utf-8',newline='') as stream:
    for row in csv.DictReader(stream):
        groups[int(row['simulation_id'])].append(row)
fig, ax = plt.subplots(figsize=(9,5.2),layout='constrained')
for desired, color in [(True,'#23649e'),(False,'#ba4c28')]:
    for sid, rows in sorted(groups.items()):
        progress = [float(r['PercAccomplished']) for r in rows]
        if any(p >= 100 for p in progress) == desired:
            time = [float(r['SimTime']) for r in rows]
            ax.plot(time,progress,color=color,linewidth=2.2,label=f'Cenário {sid} - '+('concluído' if desired else 'não concluído no horizonte'))
            break
ax.axhline(100,color='#555555',linewidth=1,linestyle='--')
ax.set(xlabel='Tempo simulado (tu)',ylabel='Progresso simulado (%)',
       title='Dois cenários existentes do simulador',xlim=(0,60))
ax.grid(alpha=.2)
ax.legend(loc='upper left')
fig.supxlabel('Dados sintéticos. Os casos diferem em vários parâmetros; não isolam efeito causal.',fontsize=9)
fig.savefig(ROOT/'docs/cenarios-exemplo.png',dpi=160)
plt.close(fig)
