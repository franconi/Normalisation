#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "desktop_launcher.py"


def pyinstaller_available() -> bool:
    return importlib.util.find_spec("PyInstaller") is not None


def default_mode() -> str:
    return "onedir" if platform.system() == "Darwin" else "onefile"


def build_args(args: argparse.Namespace) -> list[str]:
    dist_dir = ROOT / args.dist_dir
    work_dir = ROOT / args.work_dir
    spec_dir = ROOT / args.spec_dir

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        args.name,
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
    ]

    mode = args.mode or default_mode()
    command.append("--onefile" if mode == "onefile" else "--onedir")

    if not args.console and platform.system() in {"Darwin", "Windows"}:
        command.append("--windowed")

    readme = ROOT / "readme.md"
    if readme.exists():
        command.extend(["--add-data", f"{readme}{os.pathsep}."])

    for module in [
        "combined_null_4nf_frontend",
        "combined_null_4nf_decomposer",
        "fd_mvd_normalizer",
        "sql_null_decomposer",
        "six_nf",
    ]:
        command.extend(["--hidden-import", module])

    command.append(str(ENTRYPOINT))
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a self-contained Normaliser desktop app with PyInstaller."
    )
    parser.add_argument("--name", default="Normaliser")
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--work-dir", default="build/pyinstaller")
    parser.add_argument("--spec-dir", default="build/spec")
    parser.add_argument(
        "--mode",
        choices=("onefile", "onedir"),
        default=None,
        help="Default is onedir on macOS, onefile on Windows/Linux.",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Keep a console window for debugging.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not ENTRYPOINT.exists():
        print(f"Missing entrypoint: {ENTRYPOINT}", file=sys.stderr)
        return 1

    if not pyinstaller_available():
        print(
            "PyInstaller is not installed. Install it with:\n"
            "  python -m pip install pyinstaller",
            file=sys.stderr,
        )
        return 2

    dist_dir = ROOT / args.dist_dir
    spec_dir = ROOT / args.spec_dir
    dist_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)

    command = build_args(args)
    print("Running:")
    print(" ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)

    print("\nBuild output:")
    for path in sorted(dist_dir.iterdir()):
        print(f"  {path.relative_to(ROOT)}")

    if shutil.which("codesign") and platform.system() == "Darwin":
        print("\nmacOS note: sign/notarize the .app before distributing outside your machine.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
