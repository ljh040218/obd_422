"""Inspect decoded numeric MF4 channels and export causal time alignment."""
import csv
import math
import numpy as np
import pandas as pd
from asammdf import MDF

INVENTORY_FIELDS = ['channel', 'unit', 'samples', 'numeric', 'finite_samples',
                    'nonfinite_samples', 'unique_values', 'varying', 'minimum',
                    'maximum', 'first_time_s', 'last_time_s', 'median_period_s',
                    'timestamp_reversals', 'timestamp_duplicates']


def inspect_mf4(path):
    rows, signals = [], {}
    with MDF(path) as mdf:
        for name, locations in mdf.channels_db.items():
            for group, index in locations:
                if mdf.masters_db.get(group) == index:
                    continue
                signal = mdf.get(group=group, index=index)
                key = name if len(locations) == 1 else f'{name}@{group}:{index}'
                x, t = np.asarray(signal.samples), np.asarray(signal.timestamps)
                numeric = x.ndim == 1 and x.dtype.kind in 'biuf'
                finite = np.isfinite(x) if numeric else np.zeros(len(x), dtype=bool)
                values, dt = x[finite], np.diff(t)
                unique = len(np.unique(values))
                rows.append(dict(channel=key, unit=signal.unit, samples=len(x), numeric=numeric,
                    finite_samples=int(finite.sum()), nonfinite_samples=int((~finite).sum()),
                    unique_values=unique, varying=unique > 1,
                    minimum=float(values.min()) if len(values) else None,
                    maximum=float(values.max()) if len(values) else None,
                    first_time_s=float(t.min()) if len(t) else None,
                    last_time_s=float(t.max()) if len(t) else None,
                    median_period_s=float(np.median(dt[dt > 0])) if np.any(dt > 0) else None,
                    timestamp_reversals=int((dt < 0).sum()), timestamp_duplicates=int((dt == 0).sum())))
                if numeric and len(t):
                    if not np.isfinite(t).all() or (t < 0).any():
                        raise ValueError(f'Invalid relative timestamps: {key}')
                    order = np.argsort(t, kind='stable')
                    signals[key] = (t[order].copy(), x[order].astype(float), signal.unit)
    return rows, signals


def zoh(timestamps, samples, grid, max_age):
    if not math.isfinite(max_age) or max_age < 0:
        raise ValueError('max_age must be finite and nonnegative')
    t, x = np.asarray(timestamps), np.asarray(samples)
    if len(t) != len(x) or not np.isfinite(t).all() or np.any(np.diff(t) < 0):
        raise ValueError('Timestamps must be finite, sorted and match samples')
    out, age = np.full(len(grid), np.nan), np.full(len(grid), np.nan)
    if len(t):
        idx = np.searchsorted(t, grid, side='right')-1
        present = idx >= 0
        age[present] = grid[present]-t[idx[present]]
        valid = present & (age <= max_age+1e-9)
        out[valid] = x[idx[valid]]
        out[~np.isfinite(out)] = np.nan
    return out, age


def export_aligned(signals, path, step=.01, max_age=.5, end=None, age_path=None):
    if not math.isfinite(step) or step <= 0:
        raise ValueError('step must be finite and positive')
    if not math.isfinite(max_age) or max_age < 0:
        raise ValueError('max_age must be finite and nonnegative')
    if end is None:
        end = max((s[0][-1] for s in signals.values()), default=0.)
    if not math.isfinite(end) or end < 0:
        raise ValueError('end must be finite and nonnegative')
    grid = np.arange(int(np.floor(end/step+1e-10))+1, dtype=float)*step
    columns, ages = {'relative_time_s': grid}, {'relative_time_s': grid}
    for name in sorted(signals):
        t, values, _ = signals[name]
        columns[name], age = zoh(t, values, grid, max_age)
        if age_path is not None:
            ages[name] = age
    frame = pd.DataFrame(columns)
    frame.to_csv(path, index=False, encoding='utf-8-sig')
    if age_path is not None:
        pd.DataFrame(ages).to_csv(age_path, index=False, encoding='utf-8-sig')
    return frame, dict(method='causal last observation', step_s=step, max_age_s=max_age,
                      rows=len(grid), columns=len(frame.columns), last_grid_s=float(grid[-1]),
                      ungridded_tail_s=end-float(grid[-1]),
                      missing_counts=frame.isna().sum().to_dict())


def export_original_csv(signals, path):
    # Long format grouped by channel; times are original, not a uniform grid.
    with open(path, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['channel', 'relative_time_s', 'value', 'unit'])
        for name in sorted(signals):
            t, x, unit = signals[name]
            writer.writerows((name, time, value, unit) for time, value in zip(t, x))
