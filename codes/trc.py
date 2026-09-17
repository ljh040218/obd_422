"""PCAN-View 1.1 Classic CAN frames, retaining source row and relative time."""
from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class Frame:
    source_line: int
    message_number: int
    timestamp: float
    direction: str
    can_id: int
    extended: bool
    data: bytes


def read_frames(path, audit):
    audit.update(version=None, source_header=[], frames=0, malformed=0,
                 errors=[], first_frame_s=None, last_frame_s=None)
    with open(path, encoding='latin-1') as stream:
        for line_number, line in enumerate(stream, 1):
            text = line.strip()
            if not text:
                continue
            if text.startswith(';'):
                audit['source_header'].append(text)
                if text.startswith(';$FILEVERSION='):
                    audit['version'] = text.split('=', 1)[1]
                continue
            if audit['version'] != '1.1':
                raise ValueError('Only PCAN-View TRC 1.1 Classic CAN is supported')
            try:
                parts = text.split()
                if not re.fullmatch(r'\d+\)', parts[0]):
                    raise ValueError('Invalid message number')
                number, timestamp = int(parts[0][:-1]), float(parts[1])/1000
                direction, token = parts[2], parts[3]
                if not re.fullmatch(r'[0-9a-fA-F]{1,8}', token):
                    raise ValueError('Invalid CAN ID')
                can_id, dlc = int(token, 16), int(parts[4])
                data = bytes(int(part, 16) for part in parts[5:])
                if (not math.isfinite(timestamp) or timestamp < 0 or not 0 <= dlc <= 8
                    or len(data) != dlc or can_id > 0x1FFFFFFF):
                    raise ValueError('Invalid timestamp, CAN ID or data length')
                # PCAN 1.1 represents extended IDs with eight hex digits.
                extended = len(token) == 8 or can_id > 0x7FF
            except (ValueError, IndexError) as error:
                audit['malformed'] += 1
                audit['errors'].append(dict(source_line=line_number, text=text, error=str(error)))
                continue
            audit['frames'] += 1
            start, end = audit['first_frame_s'], audit['last_frame_s']
            audit['first_frame_s'] = timestamp if start is None else min(start, timestamp)
            audit['last_frame_s'] = timestamp if end is None else max(end, timestamp)
            yield Frame(line_number, number, timestamp, direction, can_id, extended, data)
    if audit['version'] != '1.1':
        raise ValueError('Missing or unsupported TRC version header')
