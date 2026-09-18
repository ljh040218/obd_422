import matplotlib.pyplot as plt
from data_utils import DRIVE_NAMES, build_arg_parser, load_drive_csv, resolve_path, setup_korean_font

setup_korean_font()


def plot_timeseries(df, drive_name, output_dir):
    fig, axes = plt.subplots(5, 1, figsize=(16, 12))
    fig.suptitle(f'{drive_name} 주행 데이터 분석', fontsize=16, fontweight='bold')

    time = df['timestamps']

    ax = axes[0]
    ax.plot(time, df['EMS11.VS'], 'b-', label='OBD 속도', linewidth=1)
    ax.plot(time, df['GPS_Speed'], 'r--', label='GPS 속도', linewidth=1, alpha=0.7)
    ax.set_ylabel('속도 (km/h)', fontsize=11)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_title('속도 비교 (OBD vs GPS)', fontsize=12)

    ax = axes[1]
    ax.plot(time, df['Vehicle_Accel_Forward'], 'g-', label='전후 가속도', linewidth=0.8)
    ax.plot(time, df['Vehicle_Accel_Lateral'], 'orange', label='좌우 가속도', linewidth=0.8, alpha=0.7)
    ax.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
    ax.set_ylabel('가속도 (m/s²)', fontsize=11)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_title('차량 가속도', fontsize=12)

    ax = axes[2]
    ax.plot(time, df['Slope_Grade_IMU_pct'], 'b-', label='IMU 경사도', linewidth=0.8)
    ax.plot(time, df['Slope_Grade_GPS_pct'], 'r-', label='GPS 경사도', linewidth=1, alpha=0.7)
    ax.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
    ax.set_ylabel('경사도 (%)', fontsize=11)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_title('경사도 비교 (IMU vs GPS)', fontsize=12)
    ax.set_ylim(-10, 10)

    ax = axes[3]
    ax.plot(time, df['EMS11.N'], 'purple', label='엔진 RPM', linewidth=0.8)
    ax.set_ylabel('RPM', fontsize=11, color='purple')
    ax.tick_params(axis='y', labelcolor='purple')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    ax2 = ax.twinx()
    ax2.plot(time, df['EMS12.TPS'], 'brown', label='스로틀 위치', linewidth=0.8, alpha=0.7)
    ax2.set_ylabel('TPS (%)', fontsize=11, color='brown')
    ax2.tick_params(axis='y', labelcolor='brown')
    ax2.legend(loc='upper right')
    ax.set_title('엔진 상태', fontsize=12)

    ax = axes[4]
    mode_colors = {
        'Stopped': 'red',
        'Accelerating': 'green',
        'Cruising': 'blue',
        'Decelerating': 'orange',
    }
    for mode, color in mode_colors.items():
        mask = df['Driving_Mode'] == mode
        if mask.sum() > 0:
            ax.scatter(time[mask], df.loc[mask, 'EMS11.VS'], c=color, label=mode, s=1, alpha=0.5)

    ax.set_xlabel('시간 (초)', fontsize=11)
    ax.set_ylabel('속도 (km/h)', fontsize=11)
    ax.legend(loc='upper right', markerscale=5)
    ax.grid(True, alpha=0.3)
    ax.set_title('주행 모드 분류', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / f'{drive_name}_timeseries.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_correlation(df, drive_name, output_dir):
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(f'{drive_name} 센서 상관관계 분석', fontsize=16, fontweight='bold')

    ax = axes[0, 0]
    valid = df['GPS_Speed'].notna()
    if valid.sum() > 0:
        ax.scatter(df.loc[valid, 'GPS_Speed'], df.loc[valid, 'EMS11.VS'], alpha=0.3, s=2, c='blue')
        max_speed = max(df.loc[valid, 'GPS_Speed'].max(), df.loc[valid, 'EMS11.VS'].max())
        ax.plot([0, max_speed], [0, max_speed], 'r--', linewidth=2, label='이상적 1:1')
        corr = df.loc[valid, ['GPS_Speed', 'EMS11.VS']].corr().iloc[0, 1]
        ax.text(0.05, 0.95, f'상관계수: {corr:.3f}', transform=ax.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat'))
        ax.set_xlabel('GPS 속도 (km/h)', fontsize=11)
        ax.set_ylabel('OBD 속도 (km/h)', fontsize=11)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_title('속도 센서 일치도', fontsize=12)

    ax = axes[0, 1]
    valid = (df['Slope_Grade_GPS_pct'] != 0) & (df['EMS11.VS'] > 5)
    if valid.sum() > 0:
        ax.scatter(df.loc[valid, 'Slope_Grade_GPS_pct'], df.loc[valid, 'Slope_Grade_IMU_pct'],
                   alpha=0.3, s=2, c='green')
        ax.plot([-10, 10], [-10, 10], 'r--', linewidth=2, label='이상적 1:1')
        corr = df.loc[valid, ['Slope_Grade_GPS_pct', 'Slope_Grade_IMU_pct']].corr().iloc[0, 1]
        ax.text(0.05, 0.95, f'상관계수: {corr:.3f}', transform=ax.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat'))
        ax.set_xlabel('GPS 경사도 (%)', fontsize=11)
        ax.set_ylabel('IMU 경사도 (%)', fontsize=11)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10)
        ax.set_title('경사도 센서 일치도', fontsize=12)

    ax = axes[1, 0]
    ax.scatter(df['EMS11.VS'], df['Vehicle_Accel_Forward'], alpha=0.2, s=1, c='purple')
    ax.axhline(y=0, color='k', linestyle='--', linewidth=1)
    ax.set_xlabel('속도 (km/h)', fontsize=11)
    ax.set_ylabel('전후 가속도 (m/s²)', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_title('속도-가속도 관계', fontsize=12)

    ax = axes[1, 1]
    moving = df[df['EMS11.VS'] > 5].copy()
    ax.hist(moving['Slope_Grade_IMU_pct'], bins=50, alpha=0.5, label='IMU 경사도', color='blue', edgecolor='black')
    valid_gps = (moving['Slope_Grade_GPS_pct'] != 0)
    if valid_gps.sum() > 0:
        ax.hist(moving.loc[valid_gps, 'Slope_Grade_GPS_pct'], bins=50, alpha=0.5,
                label='GPS 경사도', color='red', edgecolor='black')
    ax.axvline(x=0, color='k', linestyle='--', linewidth=1)
    ax.set_xlabel('경사도 (%)', fontsize=11)
    ax.set_ylabel('빈도', fontsize=11)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title('경사도 분포', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / f'{drive_name}_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    parser = build_arg_parser('시계열 및 센서 상관관계 분석')
    args = parser.parse_args()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for drive_name in DRIVE_NAMES:
        df = load_drive_csv(drive_name, data_dir=args.data_dir,
                             export_as=f'{drive_name}_synced.csv', output_dir=args.output_dir)
        plot_timeseries(df, drive_name, output_dir)
        plot_correlation(df, drive_name, output_dir)
