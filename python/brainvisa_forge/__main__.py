import argparse
import fnmatch
import re
import shutil
import subprocess
import sys

from . import (
    read_recipes,
    sorted_recipes_packages,
    pixi_root,
    forged_packages,
    read_pixi_config,
)


def setup():
    (pixi_root / "src").mkdir(exist_ok=True)
    if not (pixi_root / "src" / "brainvisa-cmake").exists():
        subprocess.check_call(
            [
                "git",
                "-C",
                str(pixi_root / "src"),
                "clone",
                "https://github.com/brainvisa/brainvisa-cmake",
            ]
        )


def build():
    (pixi_root / "build" / "success").unlink(missing_ok=True)
    subprocess.check_call("bv_maker")
    with open(pixi_root / "build" / "success", "w"):
        pass


def forge(packages, force, show, verbose=None):
    if show and verbose is None:
        verbose = True
    if verbose is True:
        verbose = sys.stdout
    if not packages:
        packages = ["*"]
    selector = re.compile("|".join(f"(?:{fnmatch.translate(i)})" for i in packages))
    if not (pixi_root / "build" / "success").exists():
        build()
    channels = read_pixi_config()["project"]["channels"]
    recipes = read_recipes(verbose=True)
    for package in sorted_recipes_packages(recipes):
        if selector.match(package):
            if not force:
                # Check for the package exsitence
                if any(forged_packages(re.escape(package))):
                    if verbose:
                        print(
                            f"Skip existing package {package}",
                            file=verbose,
                            flush=True,
                        )
                    continue
            if verbose:
                print(
                    f'Build {package} from {recipes[package]["recipe_dir"]}',
                    file=verbose,
                    flush=True,
                )
            if not show:
                build_dir = pixi_root / "forge" / "bld" / f"rattler-build_{package}"
                if build_dir.exists():
                    shutil.rmtree(build_dir)
                forge = pixi_root / "forge"
                command = [
                    "rattler-build",
                    "build",
                    "--experimental",
                    "--no-build-id",
                    "-r",
                    recipes[package]["recipe_dir"],
                    "--output-dir",
                    str(forge),
                ]
                for i in channels + [f"file://{str(forge)}"]:
                    command.extend(["-c", i])
                try:
                    subprocess.check_call(command)
                except subprocess.CalledProcessError:
                    print(
                        "ERROR command failed:",
                        " ".join(f"'{i}'" for i in command),
                        file=sys.stdout,
                        flush=True,
                    )
                    return 1


parser = argparse.ArgumentParser(
    prog="python -m brainvisa_forge",
)

subparsers = parser.add_subparsers(
    required=True,
    title="subcommands",
)

parser_setup = subparsers.add_parser("setup", help="setup environment")
parser_setup.set_defaults(func=setup)
parser_build = subparsers.add_parser(
    "build", help="get sources, compile and build brainvisa-cmake components"
)
parser_build.set_defaults(func=build)

parser_forge = subparsers.add_parser("forge", help="create conda packages")
parser_forge.set_defaults(func=forge)
parser_forge.add_argument(
    "-f",
    "--force",
    action="store_true",
    help="build selected packages even it they exists",
)
parser_forge.add_argument(
    "-s",
    "--show",
    action="store_true",
    help="do not build packages, only show the ones that are selected",
)
parser_forge.add_argument(
    "packages",
    type=str,
    nargs="*",
    help="select packages using their names or Unix shell-like patterns",
)

args = parser.parse_args(sys.argv[1:])
kwargs = vars(args).copy()
del kwargs["func"]
args.func(**kwargs)
