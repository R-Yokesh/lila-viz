"""
LILA BLACK - Data Processing Script
Converts raw parquet files → JSON files for the frontend.
Run this once before deploying or after getting new data.

Usage:
    python process_data.py --input ./player_data --output ./public/data
"""

import pyarrow.parquet as pq
import pandas as pd
import os, json, argparse

MAP_CONFIG = {
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290},
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

DAYS = ["February_10", "February_11", "February_12", "February_13", "February_14"]


def world_to_pixel(x, z, map_id):
    """Convert game world coords (x, z) → 1024x1024 minimap pixel coords."""
    cfg = MAP_CONFIG[map_id]
    u = (x - cfg['origin_x']) / cfg['scale']
    v = (z - cfg['origin_z']) / cfg['scale']
    px = round(u * 1024, 1)
    py = round((1 - v) * 1024, 1)
    return px, py


def load_all(input_dir):
    frames = []
    for day in DAYS:
        folder = os.path.join(input_dir, day)
        if not os.path.exists(folder):
            continue
        for f in os.listdir(folder):
            if f.startswith('.'):
                continue
            try:
                df = pq.read_table(os.path.join(folder, f)).to_pandas()
                df['event'] = df['event'].apply(
                    lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
                )
                df['day'] = day
                uid = f.split('_')[0]
                df['is_bot'] = uid.isnumeric()
                frames.append(df)
            except Exception as e:
                print(f"  Skipping {f}: {e}")
    return pd.concat(frames, ignore_index=True)


def process(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print("Loading all parquet files...")
    full = load_all(input_dir)
    print(f"  Loaded {len(full):,} rows, {full['match_id'].nunique()} matches")

    # Add pixel coordinates
    full[['px', 'py']] = full.apply(
        lambda r: pd.Series(world_to_pixel(r['x'], r['z'], r['map_id'])), axis=1
    )

    # Relative timestamps per match
    full['ts_ms'] = full['ts'].astype('int64') // 1_000_000
    ts_mins = full.groupby('match_id')['ts_ms'].transform('min')
    full['t'] = full['ts_ms'] - ts_mins

    output = {}
    for map_id in full['map_id'].unique():
        mdf = full[full['map_id'] == map_id].copy()
        matches = []
        for match_id, grp in mdf.groupby('match_id'):
            grp = grp.sort_values('t')
            day = grp['day'].iloc[0]
            records = grp[['user_id', 'px', 'py', 'event', 'is_bot', 't', 'day']].rename(
                columns={'px': 'x', 'py': 'y'}
            ).to_dict(orient='records')
            matches.append({"match_id": match_id, "day": day, "events": records})
        output[map_id] = matches
        path = os.path.join(output_dir, f"{map_id}.json")
        with open(path, 'w') as f:
            json.dump(matches, f)
        size_kb = os.path.getsize(path) / 1024
        print(f"  {map_id}: {len(matches)} matches → {size_kb:.0f} KB")

    print("Done!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',  default='./player_data', help='Path to player_data folder')
    parser.add_argument('--output', default='./public/data',  help='Output directory')
    args = parser.parse_args()
    process(args.input, args.output)
