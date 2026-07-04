import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np

from part2.pg import read_parity_game
from part2.zielonka import solve_zielonka
from part2.fpi_freezing import solve_fpi

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

TESTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../games"))
results = []

# Natural numeric sort of files
test_files = sorted(
    os.listdir(TESTS_DIR),
    key=lambda f: int(os.path.splitext(f)[0])
)

print(f"{'File':<25} | {'FPI (ms)':<12} | {'Zielonka (ms)':<15}")
print("-" * 60)

for filename in test_files:
    file_path = os.path.join(TESTS_DIR, filename)

    G = read_parity_game(file_path)

    # Benchmark FPI
    start = time.perf_counter()
    solve_fpi(G)
    time_fpi = (time.perf_counter() - start) * 1000

    # Benchmark Zielonka
    start = time.perf_counter()
    solve_zielonka(G)
    time_zlk = (time.perf_counter() - start) * 1000

    print(f"{filename:<25} | {time_fpi:<12.2f} | {time_zlk:<15.2f}")

    results.append({
        "file": os.path.splitext(filename)[0],
        "fpi": time_fpi,
        "zlk": time_zlk
    })

# ---------------- PLOTTING ----------------
if results:
    files = [r["file"] for r in results]
    fpi_times = [r["fpi"] for r in results]
    zlk_times = [r["zlk"] for r in results]

    x = np.arange(len(files))

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(12, 7),
        sharex=True
    )

    # --- FPI subplot ---
    ax1.plot(x, fpi_times, marker='o', color="#1f77b4")
    ax1.set_title("FPI Freezing Performance")
    ax1.set_ylabel("Time (ms)")
    ax1.grid(True, alpha=0.3)

    # --- Zielonka subplot ---
    ax2.plot(x, zlk_times, marker='s', color="#ff7f0e")
    ax2.set_title("Zielonka Performance")
    ax2.set_ylabel("Time (ms)")
    ax2.set_xlabel("Game instance")
    ax2.grid(True, alpha=0.3)

    # Shared x-axis labels
    ax2.set_xticks(x)
    ax2.set_xticklabels(files, rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig("random_games_comparison.png", dpi=300)

    print("\n📊 Chart saved as 'random_games_comparison.png'")