import matplotlib.pyplot as plt
from data_utils import DRIVE_NAMES, build_arg_parser, load_drive_csv, resolve_path, setup_korean_font

setup_korean_font()


def plot_acceleration_comparison(drive_dfs, output_dir):
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    fig.suptitle('OBD vs IMU 가속도 비교', fontsize=18, fontweight='bold')

    for row, drive_name in enumerate(DRIVE_NAMES):
        df = drive_dfs[drive_name]
        time = df['timestamps']
        obd_accel = df['ESP12.LONG_ACCEL']
        imu_accel = df['Vehicle_Accel_Forward']

        ax = axes[row, 0]
        ax.plot(time, obd_accel, 'b-', label='OBD (ESP12)', linewidth=0.8)
        ax.plot(time, imu_accel, 'r-', label='IMU (보정)', linewidth=0.8)
        ax.set_xlabel('시간 (초)', fontsize=11)
        ax.set_ylabel('가속도 (m/s²)', fontsize=11)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_title(f'{drive_name} - 시계열 비교', fontsize=12)

        ax = axes[row, 1]
        driving = df['EMS11.VS'] > 1
        ax.scatter(obd_accel[driving], imu_accel[driving], s=2, alpha=0.3, c='steelblue')
        ax.plot([-3, 3.3], [-3, 3.3], 'k--', linewidth=1.5, label='완벽한 일치')
        corr = df.loc[driving, ['ESP12.LONG_ACCEL', 'Vehicle_Accel_Forward']].corr().iloc[0, 1]
        ax.text(0.03, 0.95, f'상관계수: {corr:.4f}', transform=ax.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat'))
        ax.set_xlim(-6, 6)
        ax.set_ylim(-3, 3.3)
        ax.set_xlabel('OBD 가속도 (m/s²)', fontsize=11)
        ax.set_ylabel('IMU 가속도 (m/s²)', fontsize=11)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.set_title(f'{drive_name} - 산점도 (주행 중)', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / 'acceleration_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_esp_accel_analysis(drive_dfs, output_dir):
    fig, axes = plt.subplots(2, 3, figsize=(24, 12))
    fig.suptitle('ESP12.LONG_ACCEL 가속도 분석', fontsize=18, fontweight='bold')

    for row, drive_name in enumerate(DRIVE_NAMES):
        df = drive_dfs[drive_name]
        accel = df['ESP12.LONG_ACCEL']
        time = df['timestamps']
        speed = df['EMS11.VS']
        mean_accel = accel.mean()

        ax = axes[row, 0]
        ax.hist(accel, bins=50, color='steelblue', edgecolor='black', alpha=0.9)
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='0 m/s²')
        ax.axvline(x=mean_accel, color='green', linestyle='--', linewidth=2, label=f'평균: {mean_accel:.3f}')
        ax.set_xlabel('가속도 (m/s²)', fontsize=11)
        ax.set_ylabel('빈도', fontsize=11)
        ax.legend()
        ax.set_title(f'{drive_name} - 가속도 분포', fontsize=12)

        ax = axes[row, 1]
        ax.plot(time, accel, color='mediumpurple', linewidth=0.7, alpha=0.8)
        ax.axhline(y=0, color='red', linestyle='--', linewidth=1.5, label='0 m/s²')
        ax.axhline(y=mean_accel, color='green', linestyle='--', linewidth=1.5, label=f'평균: {mean_accel:.3f}')
        ax.set_xlabel('시간 (초)', fontsize=11)
        ax.set_ylabel('가속도 (m/s²)', fontsize=11)
        ax.legend()
        ax.set_title(f'{drive_name} - 시계열', fontsize=12)

        ax = axes[row, 2]
        scatter = ax.scatter(speed, accel, c=time, cmap='viridis', s=3, alpha=0.6)
        ax.axhline(y=0, color='red', linestyle='--', linewidth=1)
        ax.set_xlabel('속도 (km/h)', fontsize=11)
        ax.set_ylabel('가속도 (m/s²)', fontsize=11)
        ax.set_title(f'{drive_name} - 속도 vs 가속도', fontsize=12)
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('시간 (초)', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_dir / 'esp_accel_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    parser = build_arg_parser('OBD/IMU 가속도 비교 및 ESP12 가속도 단독 분석')
    args = parser.parse_args()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    drive_dfs = {
        drive_name: load_drive_csv(drive_name, data_dir=args.data_dir,
                                    export_as=f'{drive_name}_accel.csv', output_dir=args.output_dir)
        for drive_name in DRIVE_NAMES
    }
    plot_acceleration_comparison(drive_dfs, output_dir)
    plot_esp_accel_analysis(drive_dfs, output_dir)
