import argparse
import subprocess
import sys
import toml

from . import read_recipes, sorted_packages, pixi_root


def setup():
    pixi_config_file = pixi_root / "pixi.toml"
    channel = f"file://{pixi_root / 'forge'}"
    with open(pixi_config_file) as f:
        pixi_config = toml.load(f, decoder=toml.TomlPreserveCommentDecoder())
    if channel not in pixi_config["project"]["channels"]:
        pixi_config["project"]["channels"].append(channel)
        with open(pixi_config_file, "w") as f:
            toml.dump(pixi_config, f, encoder=toml.TomlPreserveCommentEncoder())

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


def forge():
    if not (pixi_root / "build" / "success").exists():
        build()
    recipes = read_recipes(verbose=True)
    for package in sorted_packages(recipes):
        print(package, ":", recipes[package]["recipe_dir"])


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

args = parser.parse_args(sys.argv[1:])
kwargs = vars(args).copy()
del kwargs["func"]
args.func(**kwargs)
