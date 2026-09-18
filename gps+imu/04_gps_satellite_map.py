import matplotlib.pyplot as plt
import contextily as ctx
from pyproj import Transformer
from data_utils import DRIVE_NAMES, build_arg_parser, load_drive_csv, resolve_path, setup_korean_font

setup_korean_font()

transformer = Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)


def clean_gps_track(df, movement_threshold=0.0001):
    valid_gps = df['GPS_Lat'].notna() & df['GPS_Lon'].notna()
    gps_data = df[valid_gps].copy()
    gps_data = gps_data[gps_data['EMS11.VS'] > 2].copy()

    gps_data['lat_diff'] = gps_data['GPS_Lat'].diff().abs()
    gps_data['lon_diff'] = gps_data['GPS_Lon'].diff().abs()
    valid_movement = (gps_data['lat_diff'] < movement_threshold) & (gps_data['lon_diff'] < movement_threshold)
    valid_movement.iloc[0] = True

    gps_data = gps_data[valid_movement].copy()
    gps_data = gps_data.drop(['lat_diff', 'lon_diff'], axis=1)
    return gps_data


def plot_satellite_track(df, drive_name, output_dir):
    gps_data = clean_gps_track(df)
    if len(gps_data) < 10:
        return

    x, y = transformer.transform(gps_data['GPS_Lon'].values, gps_data['GPS_Lat'].values)
    gps_data['x'] = x
    gps_data['y'] = y

    fig, ax = plt.subplots(figsize=(16, 12))
    speeds = gps_data['EMS11.VS'].values

    scatter = ax.scatter(gps_data['x'], gps_data['y'], c=speeds, cmap='RdYlGn',
                          s=180, alpha=0.8, edgecolors='black', linewidths=0.8, zorder=5)

    start_idx = gps_data.index[0]
    end_idx = gps_data.index[-1]

    ax.scatter(gps_data.loc[start_idx, 'x'], gps_data.loc[start_idx, 'y'], c='lime', s=400,
               marker='o', edgecolors='black', linewidths=3, label='출발', zorder=10)
    ax.scatter(gps_data.loc[end_idx, 'x'], gps_data.loc[end_idx, 'y'], c='red', s=400,
               marker='s', edgecolors='black', linewidths=3, label='도착', zorder=10)

    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom='auto', attribution=False)

    cbar = plt.colorbar(scatter, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label('속도 (km/h)', fontsize=35, fontweight='bold')
    cbar.ax.tick_params(labelsize=38)

    ax.legend(loc='upper right', fontsize=40, framealpha=0.9, markerscale=1.5, labelspacing=0.2)
    ax.set_title(f'{drive_name} 주행 궤적 위성 지도', fontsize=32, fontweight='bold', pad=10)
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.tick_params(labelsize=0)

    plt.tight_layout()
    plt.savefig(output_dir / f'{drive_name}_contextily.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()


if __name__ == '__main__':
    parser = build_arg_parser('GPS 궤적 위성 지도 시각화')
    args = parser.parse_args()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for drive_name in DRIVE_NAMES:
        df = load_drive_csv(drive_name, data_dir=args.data_dir,
                             export_as=f'{drive_name}_gps.csv', output_dir=args.output_dir)
        plot_satellite_track(df, drive_name, output_dir)
