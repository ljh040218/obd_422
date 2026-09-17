"""CAN signal PNG plots; channel selection is configuration, units come from data."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.alpha': .2})


def finish(fig, path, title):
    fig.suptitle(title, fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_drive(frame, signals, names, directory, drive, end):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    names = [n for n in names if n in signals]
    files = []
    for page, start in enumerate(range(0, len(names), 4), 1):
        subset = names[start:start+4]
        fig, axes = plt.subplots(len(subset), 1, figsize=(13, 3*len(subset)), squeeze=False)
        for ax, name in zip(axes.flat, subset):
            unit = signals[name][2] or 'unit unspecified'
            ax.step(frame.relative_time_s, frame[name], where='post', lw=.9, color='#126782')
            ax.set(xlabel='Time since TRC start (s)', ylabel=unit, title=name,
                   xlim=(0, max(end, .01)))
        filename = f'{page:02d}_can_timeseries.png'
        finish(fig, directory/filename, f'{drive} | DBC CAN | causal time grid')
        files.append(filename)
    if names:
        subset = names[:4]
        fig, axes = plt.subplots(len(subset), 1, figsize=(13, 3*len(subset)), squeeze=False)
        for ax, name in zip(axes.flat, subset):
            t, x, unit = signals[name]
            ax.scatter(t, x, s=2, color='#126782', rasterized=True)
            ax.set(xlabel='Original receive time (s)', ylabel=unit or 'unit unspecified',
                   title=name, xlim=(0, max(end, .01)))
        finish(fig, directory/'original_samples.png', f'{drive} | original samples; no interpolation')
        files.append('original_samples.png')
        fig, axes = plt.subplots(len(subset), 1, figsize=(13, 3*len(subset)), squeeze=False)
        for ax, name in zip(axes.flat, subset):
            ax.hist(frame[name].dropna(), bins=35, color='#126782')
            ax.set(xlabel=f'{name} ({signals[name][2] or "unit unspecified"})', ylabel='Grid rows')
        finish(fig, directory/'distributions.png', f'{drive} | distributions on held time grid')
        files.append('distributions.png')
    varying = [n for n in names if frame[n].nunique() > 1][:10]
    if len(varying) >= 2:
        corr = frame[varying].corr(min_periods=2)
        fig, ax = plt.subplots(figsize=(11, 9))
        im = ax.imshow(np.ma.masked_invalid(corr.to_numpy()), vmin=-1, vmax=1, cmap='RdBu_r')
        ax.grid(False)
        ax.set_xticks(range(len(varying)), varying, rotation=45, ha='right', fontsize=8)
        ax.set_yticks(range(len(varying)), varying, fontsize=8)
        fig.colorbar(im, ax=ax, label='Pearson correlation (pairwise available grid rows)')
        finish(fig, directory/'correlation.png', f'{drive} | descriptive correlation; not causation')
        files.append('correlation.png')
    return files


def plot_comparison(frames, units, names, path):
    names = [n for n in names if any(n in frame for frame in frames.values())][:4]
    if len(frames) < 2 or not names:
        return False
    fig, axes = plt.subplots(len(names), 1, figsize=(13, 3*len(names)), squeeze=False)
    for ax, name in zip(axes.flat, names):
        for drive, frame in frames.items():
            if name in frame:
                ax.step(frame.relative_time_s, frame[name], where='post', lw=.9, label=drive)
        ax.set(xlabel="Each recording's relative time (s)", ylabel=units.get(name) or 'unit unspecified', title=name)
        ax.legend()
    finish(fig, path, 'CAN recordings | relative time, not route-aligned')
    return True
