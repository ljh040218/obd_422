import argparse
from pathlib import Path
from codes.definitions import write_csv
from codes.mf4_io import inspect_mf4, export_aligned, export_original_csv, INVENTORY_FIELDS
from codes.report import write_json


def analyze(source, destination, names=None, step=.01, max_age=.5, raw_csv=False):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    inventory, signals = inspect_mf4(source)
    if names:
        missing = [name for name in names if name not in signals]
        if missing:
            raise ValueError(f'Selected numeric channels not found: {missing}')
        signals = {name: signals[name] for name in dict.fromkeys(names)}
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError('Choose an empty --output-dir')
    destination.mkdir(parents=True, exist_ok=True)
    write_csv(destination/'signal_inventory.csv', inventory, INVENTORY_FIELDS)
    _, export = export_aligned(signals, destination/'signals_aligned.csv', step, max_age)
    if raw_csv:
        export_original_csv(signals, destination/'signals_original.csv')
    summary = dict(input_file=str(source), numeric_signals=len(signals), export=export,
                   note='Already-decoded numeric MF4 only. Raw bus-event MF4 requires a separate decoder.')
    write_json(destination/'inspection.json', summary)
    print(f'Completed: {destination}', flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mf4', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--signals', nargs='+')
    parser.add_argument('--step', type=float, default=.01)
    parser.add_argument('--max-age', type=float, default=.5)
    parser.add_argument('--raw-csv', action='store_true')
    args = parser.parse_args()
    analyze(args.mf4, args.output_dir, args.signals, args.step, args.max_age, args.raw_csv)
