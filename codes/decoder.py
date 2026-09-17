"""Decode received CAN frames exclusively against the external DBC."""
from array import array
from collections import Counter
import csv
from pathlib import Path
import numpy as np
from asammdf import MDF, Signal
from .definitions import channel_names
from .trc import read_frames

FRAME_FIELDS = ['source_line', 'message_number', 'relative_time_s', 'direction',
                'can_id_hex', 'is_extended_frame', 'dlc', 'data_hex', 'status', 'detail']


def convert(trc_path, database, mf4_path):
    trc_path, mf4_path = Path(trc_path), Path(mf4_path)
    destination = mf4_path.parent
    destination.mkdir(parents=True, exist_ok=True)
    messages = {(m.frame_id, m.is_extended_frame): m for m in database.messages}
    names = channel_names(database)
    metadata = {names[(m.frame_id, m.is_extended_frame, s.name)]: s
                for m in database.messages for s in m.signals}
    series, parser = {}, {}
    statuses, ids, unknown, errors = Counter(), Counter(), Counter(), Counter()
    length_warnings = Counter()
    with (destination/'frames_raw.csv').open('w', encoding='utf-8-sig', newline='') as raw, \
         (destination/'frames_unresolved.csv').open('w', encoding='utf-8-sig', newline='') as unresolved:
        rw, uw = (csv.DictWriter(stream, fieldnames=FRAME_FIELDS) for stream in [raw, unresolved])
        rw.writeheader()
        uw.writeheader()
        for f in read_frames(trc_path, parser):
            ids[(f.direction, f.can_id, f.extended)] += 1
            values, message, detail = {}, None, ''
            if f.direction != 'Rx':
                status = 'transmitted' if f.direction == 'Tx' else 'other_direction'
            else:
                message = messages.get((f.can_id, f.extended))
                if message is None:
                    status = 'no_dbc_definition'
                    unknown[f'0x{f.can_id:03X}/{"extended" if f.extended else "standard"}'] += 1
                elif len(f.data) < message.length:
                    status = 'dbc_decode_error'
                    detail = f'Frame length {len(f.data)} != DBC length {message.length}'
                else:
                    try:
                        if len(f.data) > message.length:
                            detail = f'Frame length {len(f.data)} > DBC length {message.length}; only DBC-defined bytes decoded'
                            length_warnings[f'0x{f.can_id:03X}: {detail}'] += 1
                        values = message.decode(f.data, decode_choices=False,
                                                scaling=True, allow_truncated=False, allow_excess=True)
                        status = 'decoded_dbc'
                    except (ValueError, KeyError, TypeError) as error:
                        status, detail = 'dbc_decode_error', str(error)
                    except Exception as error:
                        # A bad received frame must not discard other valid frames.
                        status, detail = 'dbc_decode_error', f'{type(error).__name__}: {error}'
            if status == 'dbc_decode_error':
                errors[f'0x{f.can_id:03X}: {detail}'] += 1
            statuses[status] += 1
            row = dict(source_line=f.source_line, message_number=f.message_number,
                       relative_time_s=f.timestamp, direction=f.direction,
                       can_id_hex=f'0x{f.can_id:03X}', is_extended_frame=f.extended,
                       dlc=len(f.data), data_hex=f.data.hex(' ').upper(), status=status, detail=detail)
            rw.writerow(row)
            if f.direction == 'Rx' and status != 'decoded_dbc':
                uw.writerow(row)
            for signal_name, value in values.items():
                name = names[(message.frame_id, message.is_extended_frame, signal_name)]
                if name not in series:
                    series[name] = (array('d'), array('d'))
                series[name][0].append(f.timestamp)
                series[name][1].append(float(value))
    reordered = []
    if series:
        with MDF(version='4.10') as mdf:
            mdf.header.comment = ('TRC relative timestamps preserved. Wall-clock timezone unspecified.\n'
                                  + '\n'.join(parser['source_header']))
            for name, (times, values) in series.items():
                t, x = np.asarray(times), np.asarray(values)
                if np.any(np.diff(t) < 0):
                    reordered.append(name)
                    order = np.argsort(t, kind='stable')
                    t, x = t[order], x[order]
                mdf.append(Signal(samples=x, timestamps=t, name=name,
                                  unit=metadata[name].unit or '',
                                  comment='DBC decoded Rx data; original relative timestamps; no resampling'))
            mdf.save(mf4_path, overwrite=True)
    return dict(parser=parser, status_counts=dict(statuses), signal_count=len(series),
                raw_signal_samples=sum(len(v[0]) for v in series.values()),
                unknown_ids=dict(unknown), decode_errors=dict(errors), length_warnings=dict(length_warnings),
                reordered_channels=reordered, mf4_written=bool(series),
                can_ids=[dict(direction=d, can_id_hex=f'0x{i:03X}', is_extended_frame=e, frames=n)
                         for (d, i, e), n in sorted(ids.items())],
                mf4_header_time='conversion time; use original relative timestamps and source header')
