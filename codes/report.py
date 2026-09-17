"""Write machine-readable run summaries and DBC signal availability."""
from .definitions import write_csv


def write_summary(path, value):
    """Flatten nested audit data into a readable CSV, without creating JSON files."""
    rows = []
    def visit(item, key):
        if isinstance(item, dict):
            if not item:
                rows.append(dict(item=key, value='', type='dict'))
            for name, child in item.items():
                visit(child, f'{key}.{name}' if key else str(name))
        elif isinstance(item, (list, tuple)):
            if not item:
                rows.append(dict(item=key, value='', type='list'))
            for index, child in enumerate(item):
                visit(child, f'{key}[{index}]')
        else:
            rows.append(dict(item=key, value='' if item is None else item,
                             type=type(item).__name__))
    visit(value, '')
    write_csv(path, rows, ['item', 'value', 'type'])


def write_availability(path, definitions, inventories):
    lookups = {drive: {r['channel']: r for r in rows} for drive, rows in inventories.items()}
    fields = ['channel', 'can_id_hex', 'unit']
    for drive in lookups:
        fields += [f'{drive}_{field}' for field in ['present', 'samples', 'varying', 'minimum', 'maximum']]
    rows = []
    for name, definition in definitions.items():
        row = {k: definition[k] for k in ['channel', 'can_id_hex', 'unit']}
        for drive, lookup in lookups.items():
            entry = lookup.get(name, {})
            row[f'{drive}_present'] = name in lookup
            for field in ['samples', 'varying', 'minimum', 'maximum']:
                row[f'{drive}_{field}'] = entry.get(field, '')
        rows.append(row)
    write_csv(path, rows, fields)
