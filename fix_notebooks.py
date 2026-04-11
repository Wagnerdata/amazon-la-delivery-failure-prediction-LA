import json
import re
from pathlib import Path

NOTEBOOKS_DIR = Path('notebooks')

# ── Exact string replacements keyed by notebook ──────────────────────────────
REPLACEMENTS_BY_NB = {
    '01_project_description.ipynb': [
        # Financial Impact section — wrong cost, rate, count, recall
        ('**$8–12** (redelivery + CS contact)',      '**$17** (redelivery + CS contact)'),
        ('**$8-12** (redelivery + CS contact)',      '**$17** (redelivery + CS contact)'),
        ('**~19.4%** → ~1,455 failures in 7,500 packages',
         '**~0.70%** → ~25 failures in 3,559 packages'),
        ('~1,455 failures in 7,500 packages',        '~25 failures in 3,559 packages'),
        ('1,455 failures in 7,500 packages',         '25 failures in 3,559 packages'),
        ('46% of failures',                          '80% of failures'),
        ('7,500 packages',                           '3,559 packages'),
        ('7,500',                                    '3,559'),
    ],
    '06_final_report.ipynb': [
        ('int(25 * 0.46 * 0.30)',   'int(25 * 0.80 * 0.30)'),
        ('int(25*0.46*0.30)',        'int(25*0.80*0.30)'),
        ('int(25 * 0.46)',           'int(25 * 0.80)'),
        ('int(25*0.46)',             'int(25*0.80)'),
        ('Model recall (46%)',       'Model recall (80%)'),
        ('recall=0.46',              'recall=0.80'),
        ('recall = 0.46',            'recall = 0.80'),
    ],
}

def fix_notebook(path, replacements):
    nb = json.loads(path.read_text(encoding='utf-8'))
    changes = []

    for cell_idx, cell in enumerate(nb['cells']):
        original = ''.join(cell['source'])
        fixed = original

        for old, new in replacements:
            if old in fixed:
                fixed = fixed.replace(old, new)
                changes.append(f"  cell {cell_idx}: '{old[:60]}' → '{new[:60]}'")

        if fixed != original:
            lines = fixed.split('\n')
            cell['source'] = [line + '\n' for line in lines]
            if cell['source']:
                cell['source'][-1] = cell['source'][-1].rstrip('\n')

    return nb, changes

# ── Process ───────────────────────────────────────────────────────────────────
total_changes = 0
for nb_name, replacements in REPLACEMENTS_BY_NB.items():
    path = NOTEBOOKS_DIR / nb_name
    if not path.exists():
        print(f'⚠  Not found: {nb_name}')
        continue

    nb_fixed, changes = fix_notebook(path, replacements)

    if changes:
        path.write_text(
            json.dumps(nb_fixed, ensure_ascii=False, indent=1),
            encoding='utf-8'
        )
        print(f'✓ Fixed {nb_name} ({len(changes)} changes):')
        for c in changes:
            print(c)
        total_changes += len(changes)
    else:
        print(f'✓ Clean {nb_name} — no changes needed')

print(f'\nTotal changes: {total_changes}')
