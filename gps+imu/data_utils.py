import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR
DEFAULT_OUTPUT_DIR = SCRIPT_DIR

DRIVE_NAMES = ['drive_01', 'drive_02']


def setup_korean_font():
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False


def resolve_path(path_str):
    """상대경로, 절대경로 입력 모두 처리한다. 상대경로는 현재 작업 디렉토리 기준으로 해석된다."""
    return Path(path_str).expanduser().resolve()


def build_arg_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--data-dir', type=str, default=str(DEFAULT_DATA_DIR),
                         help='OBD/GPS/IMU 병합 CSV가 있는 폴더 (생략 시 스크립트와 같은 폴더)')
    parser.add_argument('--output-dir', type=str, default=str(DEFAULT_OUTPUT_DIR),
                         help='결과 이미지 및 변환 CSV를 저장할 폴더 (생략 시 스크립트와 같은 폴더)')
    return parser


def get_merged_csv_path(drive_name, data_dir):
    return resolve_path(data_dir) / f'{drive_name}_final.csv'


def load_drive_csv(drive_name, data_dir=DEFAULT_DATA_DIR, export_as=None, output_dir=DEFAULT_OUTPUT_DIR):
    """OBD/GPS/IMU 병합 CSV를 읽고, export_as가 주어지면 output_dir 아래에
    동일한 이름으로 다시 저장한 뒤 그 파일을 재로딩하여 반환한다."""
    csv_path = get_merged_csv_path(drive_name, data_dir)
    df = pd.read_csv(csv_path)

    if export_as is not None:
        out_dir = resolve_path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / export_as
        df.to_csv(out_path, index=False)
        df = pd.read_csv(out_path)

    return df
