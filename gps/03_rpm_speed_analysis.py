import matplotlib.pyplot as plt
import seaborn as sns
from data_utils import DRIVE_NAMES, build_arg_parser, load_drive_csv, resolve_path, setup_korean_font

setup_korean_font()
sns.set_style('darkgrid')


def plot_rpm_speed_analysis(df, output_csv_name, output_dir):
    fig, axes = plt.subplots(3, 1, figsize=(16, 18))
    fig.suptitle(f'주행 데이터 시각화 분석: {output_csv_name}', fontsize=18)

    time = df['timestamps']
    rpm = df['EMS11.N']
    speed = df['EMS11.VS']

    ax1 = axes[0]
    ax1.plot(time, rpm, color='royalblue', linewidth=1)
    ax1.set_xlabel('Time (sec)', fontsize=12)
    ax1.set_ylabel('RPM', color='royalblue', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='royalblue')
    ax1.set_title('시간대별 RPM 및 속도 추이', fontsize=14)

    ax1b = ax1.twinx()
    ax1b.plot(time, speed, color='crimson', linewidth=1.2)
    ax1b.set_ylabel('Speed (km/h)', color='crimson', fontsize=12)
    ax1b.tick_params(axis='y', labelcolor='crimson')
    ax1b.grid(False)

    ax2 = axes[1]
    ax2.scatter(speed, rpm, s=12, alpha=0.4, color='teal', edgecolor='none')
    ax2.set_xlabel('Speed (km/h)', fontsize=12)
    ax2.set_ylabel('RPM', fontsize=12)
    ax2.set_title('속도 대비 RPM 분포 (기어비 확인 가능)', fontsize=14)

    ax3 = axes[2]
    sns.histplot(rpm[speed > 1], bins=30, kde=True, color='skyblue', ax=ax3)
    ax3.set_xlabel('RPM', fontsize=12)
    ax3.set_ylabel('Count', fontsize=12)
    ax3.set_title('주행 중 RPM 사용 구간 분포', fontsize=14)

    plt.tight_layout()
    output_name = output_csv_name.replace('.csv', '') + '_analysis.png'
    plt.savefig(output_dir / output_name, dpi=150, bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    parser = build_arg_parser('RPM 및 속도 기반 주행 데이터 분석')
    args = parser.parse_args()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for drive_name in DRIVE_NAMES:
        output_csv_name = f'output_{drive_name}.csv'
        df = load_drive_csv(drive_name, data_dir=args.data_dir,
                             export_as=output_csv_name, output_dir=args.output_dir)
        plot_rpm_speed_analysis(df, output_csv_name, output_dir)
