#!/usr/bin/env bash

set -e

OUTDIR="../games"
mkdir -p "$OUTDIR"

N=50
MIN_SIZE=10
MAX_SIZE=500

for i in $(seq 0 $((N - 1))); do
    # linear interpolation
    size=$(awk -v i="$i" -v n="$((N-1))" -v min="$MIN_SIZE" -v max="$MAX_SIZE" \
        'BEGIN { printf "%d", min + (i * (max - min) / n) }')

    maxe=$((size * 4))
    seed=12345

    file=$(printf "%s/%d.pg" "$OUTDIR" "$size")

    ../../oink/build/test_solvers --size "$size" --maxe "$maxe" --gameseed "$seed" > "$file"

    echo "Generated $file (size=$size, maxe=$maxe)"
done