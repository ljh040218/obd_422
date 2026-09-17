import argparse
import gc
import importlib.metadata
import json
import math
from pathlib import Path
import platform
from codes.definitions import load_database, save_definitions, sha256, write_csv
from codes.decoder import convert
from codes.mf4_io import inspect_mf4, export_aligned, export_original_csv, INVENTORY_FIELDS
from codes.plots import plot_drive, plot_comparison
from codes.report import write_availability

ROOT = Path(__file__).resolve().parent


def select_signals(signals, requested):
    selected = [n for n in requested if n in signals]
    # A different DBC can run without this package's example plot selection.
    if not selected:
        selected = sorted(signals)[:8]
    return selected


def run(inputs, dbc, output, plot_config=None, step=.01, max_age=.5, raw_csv=False):
    inputs, dbc, output = [Path(p).resolve() for p in inputs], Path(dbc).resolve(), Path(output).resolve()
    if not inputs or not all(p.is_file() for p in inputs) or not dbc.is_file():
        raise FileNotFoundError('Input TRC or DBC file does not exist')
    if len({p.stem.casefold() for p in inputs}) != len(inputs):
        raise ValueError('Input TRC stems must be unique to avoid output collisions')
    if not math.isfinite(step) or step <= 0 or not math.isfinite(max_age) or max_age < 0:
        raise ValueError('step must be positive; max-age must be nonnegative; both finite')
    requested = []
    if plot_config is not None:
        requested = json.loads(Path(plot_config).read_text(encoding='utf-8-sig'))['signals']
        if not isinstance(requested, list) or not all(isinstance(n, str) for n in requested):
            raise ValueError('plot configuration signals must be a list of channel names')
        requested = list(dict.fromkeys(requested))
    database = load_database(dbc)
    # Use a clean result destination so obsolete outputs cannot masquerade as this run.
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f'Result directory is not empty; choose a new --output-dir: {output}')
    output.mkdir(parents=True, exist_ok=True)
    definitions = save_definitions(database, dbc, output/'definitions')
    summary = dict(python=platform.python_version(), dbc_file=str(dbc), dbc_sha256=sha256(dbc),
                   definition_count=len(definitions), message_count=len(database.messages),
                   libraries={n: importlib.metadata.version(n) for n in
                              ['cantools', 'asammdf', 'numpy', 'pandas', 'matplotlib']}, drives={})
    frames, inventories, plot_names, units = {}, {}, [], {}
    had_errors = False
    for source in inputs:
        drive, destination = source.stem, output/source.stem
        destination.mkdir()
        print(f'[{drive}] TRC -> DBC -> original-time MF4', flush=True)
        audit = convert(source, database, destination/f'{drive}.mf4')
        write_csv(destination/'can_id_inventory.csv', audit['can_ids'],
                  ['direction', 'can_id_hex', 'is_extended_frame', 'frames'])
        had_errors |= bool(audit['parser']['malformed'] or audit['decode_errors'])
        inventory, signals = inspect_mf4(destination/f'{drive}.mf4') if audit['mf4_written'] else ([], {})
        write_csv(destination/'signal_inventory.csv', inventory, INVENTORY_FIELDS)
        print(f'[{drive}] {len(signals)} CAN signals -> CSV / PNG', flush=True)
        end = audit['parser']['last_frame_s'] or 0.
        frame, export_info = export_aligned(signals, destination/'signals_aligned.csv', step, max_age,
                                            end, destination/'sample_age_seconds.csv')
        if raw_csv:
            export_original_csv(signals, destination/'signals_original.csv')
        selected = select_signals(signals, requested)
        small = frame[['relative_time_s']+selected].copy()
        small.to_csv(destination/'selected_signals.csv', index=False, encoding='utf-8-sig')
        images = plot_drive(frame, signals, selected, destination/'plots', drive, end)
        frames[drive], inventories[drive] = small, inventory
        plot_names += [n for n in selected if n not in plot_names]
        units.update({n: signals[n][2] for n in selected})
        summary['drives'][drive] = dict(input_file=str(source), input_sha256=sha256(source),
            first_frame_s=audit['parser']['first_frame_s'], last_frame_s=end,
            frames=audit['parser']['frames'], status_counts=audit['status_counts'],
            decoded_channels=len(signals), raw_signal_samples=audit['raw_signal_samples'],
            unknown_ids=audit['unknown_ids'], malformed=audit['parser']['malformed'],
            decode_errors=audit['decode_errors'], length_warnings=audit['length_warnings'], selected=selected,
            requested_not_observed=[n for n in requested if n not in signals],
            export=export_info, plots=images, original_csv=raw_csv)
        del frame, signals
        gc.collect()
    plot_comparison(frames, units, plot_names, output/'drive_comparison.png')
    write_availability(output/'signal_availability.csv', definitions, inventories)
    summary['status'] = 'completed_with_errors' if had_errors else 'completed'
    if had_errors:
        raise RuntimeError('Results written, but some frames failed. See decode_audit.json.')
    print(f'Completed: {output}', flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, nargs='+', help='One or more TRC files')
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data', help='Used when --input is omitted')
    parser.add_argument('--dbc', type=Path, default=ROOT/'definitions/hyundai_kia_generic.dbc')
    parser.add_argument('--output-dir', '--output', type=Path, default=ROOT/'results')
    parser.add_argument('--plot-config', type=Path, default=ROOT/'definitions/plot_signals.json')
    parser.add_argument('--step', type=float, default=.01)
    parser.add_argument('--max-age', type=float, default=.5)
    parser.add_argument('--raw-csv', action='store_true', help='Also export large original-time long CSV')
    args = parser.parse_args()
    sources = args.input if args.input else sorted(args.data_dir.glob('*.trc'))
    run(sources, args.dbc, args.output_dir, args.plot_config, args.step, args.max_age, args.raw_csv)
