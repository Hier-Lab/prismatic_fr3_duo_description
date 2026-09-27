#!/usr/bin/env python3
"""Compile a Xacro robot description into a URDF file."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


PACKAGE_NAME = "prismatic_fr3_duo_description"


def find_package_root() -> Path:
    """Return the installed share directory, or the source tree during development."""
    source_root = Path(__file__).resolve().parents[1]
    if (source_root / "package.xml").is_file():
        return source_root

    try:
        from ament_index_python.packages import get_package_share_directory

        return Path(get_package_share_directory(PACKAGE_NAME))
    except (ImportError, LookupError):
        return source_root


PACKAGE_ROOT = find_package_root()
DEFAULT_INPUT = PACKAGE_ROOT / "urdf" / "prismatic_fr3_duo.urdf.xacro"
DEFAULT_OUTPUT = PACKAGE_ROOT / "urdf" / "prismatic_fr3_duo.urdf"
DEFAULT_CONFIG = PACKAGE_ROOT / "config" / "prismatic_fr3_duo.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a Xacro file to URDF using the package parameter YAML."
    )
    parser.add_argument(
        "-i", "--input", type=Path, default=DEFAULT_INPUT, help="input Xacro file"
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT, help="output URDF file"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="parameter YAML passed to the Xacro as config_file",
    )
    parser.add_argument(
        "--xacro-executable",
        default="xacro",
        help="xacro executable name or path (default: xacro)",
    )
    parser.add_argument(
        "--keep-all-collisions",
        action="store_false",
        help="do not reduce collision elements in the generated URDF",
    )
    return parser.parse_args()


def resolve_existing(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    return resolved


def collision_shape(collision: ET.Element) -> str | None:
    """Return the primitive or mesh tag used by a collision element."""
    geometry = collision.find("geometry")
    if geometry is None or len(geometry) == 0:
        return None
    return geometry[0].tag


def simplify_collisions(path: Path) -> tuple[int, int]:
    """
    Keep at most one cylinder and one sphere collision on every link.

    A link with no cylinder or sphere keeps its first collision geometry. This
    preserves collision coverage for the base, hand mesh, and finger boxes.
    """
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(path, parser=parser)
    links_changed = 0
    collisions_removed = 0

    for link in tree.getroot().findall("link"):
        collisions = link.findall("collision")
        if len(collisions) <= 1:
            continue

        cylinder = next(
            (item for item in collisions if collision_shape(item) == "cylinder"),
            None,
        )
        sphere1 = next(
            (item for item in collisions if collision_shape(item) == "sphere"),
            None,
        )
        sphere2 = next(
            (item for item in collisions if collision_shape(item) == "sphere"),
            None,
        )
        keep = {item for item in (cylinder, sphere1, sphere2) if item is not None}
        if not keep:
            keep = {collisions[0]}

        removed_here = 0
        for collision in collisions:
            if collision not in keep:
                link.remove(collision)
                removed_here += 1

        if removed_here:
            links_changed += 1
            collisions_removed += removed_here

    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return links_changed, collisions_removed


def main() -> int:
    args = parse_args()

    try:
        input_path = resolve_existing(args.input, "input Xacro")
        config_path = resolve_existing(args.config, "config YAML")
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    xacro_executable = shutil.which(args.xacro_executable)
    if xacro_executable is None:
        print(
            f"error: xacro executable not found: {args.xacro_executable!r}; "
            "source your ROS environment first",
            file=sys.stderr,
        )
        return 2

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            result = subprocess.run(
                [
                    xacro_executable,
                    input_path.name,
                    f"config_file:={config_path}",
                ],
                cwd=input_path.parent,
                stdout=temporary_file,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

        if result.returncode != 0:
            print(result.stderr.rstrip(), file=sys.stderr)
            return result.returncode

        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)

        if not args.keep_all_collisions:
            links_changed, collisions_removed = simplify_collisions(temporary_path)
            print(
                f"Simplified collisions on {links_changed} links "
                f"({collisions_removed} collision elements removed)"
            )

        temporary_path.replace(output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(f"Generated {output_path} from {input_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
