import subprocess
import re
import matplotlib.pyplot as plt

CMD = [
    "wsl",
    "../../oink/build/test_solvers",
    "--fpi", "--zlk", "--psi", "--sort",
    "../../part2/games"
]

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub('', text)


def parse_output(output):
    sizes, fpi_list, psi_list, zlk_list = [], [], [], []

    for line in output.splitlines():
        line = line.strip()
        if not line or ".pg:" not in line:
            continue

        size_match = re.match(r"(\d+)\.pg:", line)
        if not size_match:
            continue
        size = int(size_match.group(1))

        fpi = re.search(r"fpi\s*\((\d+)\)", line)
        psi = re.search(r"psi\s*\((\d+)\)", line)
        zlk = re.search(r"zlk\s*\((\d+)\)", line)

        if not (fpi and psi and zlk):
            continue

        sizes.append(size)
        fpi_list.append(int(fpi.group(1)))
        psi_list.append(int(psi.group(1)))
        zlk_list.append(int(zlk.group(1)))

    return sizes, fpi_list, psi_list, zlk_list


def main():
    print("Running benchmark in WSL...")

    result = subprocess.run(CMD, capture_output=True, text=True)

    output = strip_ansi(result.stdout + result.stderr)
    print(output)

    sizes, fpi, psi, zlk = parse_output(output)
    print(f"Parsed {len(sizes)} datapoints")

    # sort by size
    if sizes:
        sizes, fpi, psi, zlk = map(
            list,
            zip(*sorted(zip(sizes, fpi, psi, zlk)))
        )

    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    axes[0].plot(sizes, fpi, marker='o')
    axes[0].set_title("FPI solver")
    axes[0].set_ylabel("Time (ms)")
    axes[0].grid(True, linestyle="--", alpha=0.6)

    axes[1].plot(sizes, psi, marker='o', color='orange')
    axes[1].set_title("PSI solver")
    axes[1].set_ylabel("Time (ms)")
    axes[1].grid(True, linestyle="--", alpha=0.6)

    axes[2].plot(sizes, zlk, marker='o', color='green')
    axes[2].set_title("ZLK solver")
    axes[2].set_xlabel("Game Size")
    axes[2].set_ylabel("Time (ms)")
    axes[2].grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig("solver_comparison_subplots.png", dpi=300, bbox_inches="tight")

    print("Saved plot: solver_comparison_subplots.png")


if __name__ == "__main__":
    main()