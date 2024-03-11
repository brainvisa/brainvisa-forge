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
    write_pixi_config,
)


def setup(verbose=None):
    # Find recipes for external projects and recipes build using bv_maker
    external_recipes = []
    bv_maker_recipes = []
    bv_maker_packages = set()
    for recipe in read_recipes():
        script = recipe.get("build", {}).get("script")
        if isinstance(script, str) and "BRAINVISA_INSTALL_PREFIX" in script:
            bv_maker_recipes.append(recipe)
            bv_maker_packages.add(recipe["package"]["name"])
        else:
            external_recipes.append(recipe)

    # Build external packages
    for recipe in external_recipes:
        package = recipe["package"]["name"]
        if not any(forged_packages(re.escape(package))):
            result = forge([package], force=False, show=False, check_build=False, verbose=verbose)
            if result:
                return result

    # Add internal forge to pixi project
    channel = f"file://{pixi_root / 'forge'}"
    pixi_config = read_pixi_config()
    if channel not in pixi_config["project"]["channels"]:
        pixi_config["project"]["channels"].append(channel)
        write_pixi_config(pixi_config)

    # Download brainvisa-cmake sources
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

    # Compute all packages build and run dependencies
    dependencies = {}
    for recipe in external_recipes + bv_maker_recipes:
        for requirement in recipe.get("requirements", {}).get("run", []) + recipe.get(
            "requirements", {}
        ).get("build", []):
            if not isinstance(requirement, str) or requirement.startswith("$"):
                continue
            package, constraint = (requirement.split(None, 1) + [None])[:2]
            if package not in bv_maker_packages:
                dependencies.setdefault(package, set())
                if constraint:
                    existing_constraint = dependencies[package]
                    if constraint not in existing_constraint:
                        existing_constraint.add(constraint)
                        dependencies[package] = existing_constraint

    # Add dependencies to pixi project
    remove = []
    add = []
    for package, constraint in dependencies.items():
        pixi_constraint = pixi_config.get("dependencies", {}).get(package)
        if pixi_constraint is not None:
            if pixi_constraint == "*":
                pixi_constraint = set()
            else:
                pixi_constraint = set(pixi_constraint.split(","))
            if constraint == "*":
                constraint = set()
            if pixi_constraint != constraint:
                remove.append(package)
            else:
                continue
        if constraint:
            add.append(f"{package} {','.join(constraint)}")
        else:
            add.append(f"{package} =*")
    try:
        if remove:
            command = ["pixi", "remove"] + remove
            subprocess.check_call(command)
        if add:
            command = ["pixi", "add"] + add
            subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print(
            "ERROR command failed:",
            " ".join(f"'{i}'" for i in command),
            file=sys.stdout,
            flush=True,
        )
        return 1
        

def build():
    (pixi_root / "build" / "success").unlink(missing_ok=True)
    subprocess.check_call("bv_maker")
    with open(pixi_root / "build" / "success", "w"):
        pass


def forge(packages, force, show, check_build=True,verbose=None):
    if show and verbose is None:
        verbose = True
    if verbose is True:
        verbose = sys.stdout
    if not packages:
        packages = ["*"]
    selector = re.compile("|".join(f"(?:{fnmatch.translate(i)})" for i in packages))
    if check_build and not (pixi_root / "build" / "success").exists():
        build()
    channels = read_pixi_config()["project"]["channels"]
    for package, recipe_dir in sorted_recipes_packages():
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
                    f"Build {package}",
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
                    recipe_dir,
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
