"""Read DBC definitions with cantools; CSV files are derived views, never inputs."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import cantools


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_database(path):
    database = cantools.database.load_file(str(path), database_format='dbc', strict=True)
    keys = [(m.frame_id, m.is_extended_frame) for m in database.messages]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate message ID/frame format in DBC')
    return database


def channel_names(database):
    counts = Counter(f'{m.name}.{s.name}' for m in database.messages for s in m.signals)
    result = {}
    for m in database.messages:
        for s in m.signals:
            name = f'{m.name}.{s.name}'
            if counts[name] > 1:
                name = f'{m.frame_id:X}_{"extended" if m.is_extended_frame else "standard"}.{name}'
            result[(m.frame_id, m.is_extended_frame, s.name)] = name
    return result


MESSAGE_FIELDS = ['message', 'can_id_hex', 'can_id_decimal', 'is_extended_frame',
                  'frame_bytes', 'senders', 'receivers', 'cycle_time_ms', 'comment',
                  'source_dbc', 'source_sha256']
SIGNAL_FIELDS = ['channel', 'message', 'signal', 'can_id_hex', 'can_id_decimal',
                 'is_extended_frame', 'frame_bytes', 'start_bit', 'bit_length',
                 'byte_order', 'signed', 'is_float', 'factor', 'offset', 'unit',
                 'minimum', 'maximum', 'receivers', 'is_multiplexer',
                 'multiplexer_signal', 'multiplexer_ids', 'choices', 'comment',
                 'source_dbc', 'source_sha256']


def registry(database, source):
    source = Path(source)
    provenance = dict(source_dbc=source.name, source_sha256=sha256(source))
    names = channel_names(database)
    messages, signals = [], []
    for m in database.messages:
        common = dict(message=m.name, can_id_hex=f'0x{m.frame_id:03X}',
                      can_id_decimal=m.frame_id, is_extended_frame=m.is_extended_frame,
                      frame_bytes=m.length, **provenance)
        messages.append(dict(**common, senders=json.dumps(m.senders),
                             receivers=json.dumps(sorted(m.receivers)),
                             cycle_time_ms=m.cycle_time, comment=m.comment or ''))
        for s in m.signals:
            signals.append(dict(**common,
                channel=names[(m.frame_id, m.is_extended_frame, s.name)], signal=s.name,
                start_bit=s.start, bit_length=s.length, byte_order=s.byte_order,
                signed=s.is_signed, is_float=s.is_float, factor=s.scale, offset=s.offset,
                unit=s.unit or '', minimum=s.minimum, maximum=s.maximum,
                receivers=json.dumps(s.receivers), is_multiplexer=s.is_multiplexer,
                multiplexer_signal=s.multiplexer_signal or '',
                multiplexer_ids=json.dumps(s.multiplexer_ids or []),
                choices=json.dumps({str(k): str(v) for k, v in (s.choices or {}).items()}, ensure_ascii=False),
                comment=s.comment or ''))
    return messages, signals


def save_definitions(database, source, directory):
    messages, signals = registry(database, source)
    write_csv(Path(directory)/'message_definitions.csv', messages, MESSAGE_FIELDS)
    write_csv(Path(directory)/'signal_definitions.csv', signals, SIGNAL_FIELDS)
    return {r['channel']: r for r in signals}
