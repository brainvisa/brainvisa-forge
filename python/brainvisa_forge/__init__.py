import json
import os
import pathlib
import re

# import subprocess
# import sys
# import tempfile
import toml
import yaml

pixi_root = pathlib.Path(os.environ["PIXI_PROJECT_ROOT"])


def read_recipes(verbose=None):
    for recipe_file in (pixi_root / "recipes").glob("*/recipe.yaml"):
        with open(recipe_file) as f:
            recipe = yaml.safe_load(f)
            recipe["recipe_dir"] = str(recipe_file.parent)
            yield recipe


# def read_recipes(verbose=None):
#     """
#     Read all recipe.yaml files via rattler-build to let it resolve
#     the content of the file that may contain jinja-like expressions.
#     This is only package name.

#     Return a dict whos keys are package names and values are recipe
#     dicts. In each recipe dict, a "recipe_dir" item is added containing
#     the directory of the recipe file.
#     """
#     if verbose is True:
#         verbose = sys.stdout
#     recipes = None
#     recipe_files = list((pixi_root / "recipes").glob("*/recipe.yaml"))
#     recipes_file = pixi_root / "recipes" / "recipes.yaml"
#     if recipes_file.exists():
#         if max(f.stat().st_mtime for f in recipe_files) <= recipes_file.stat().st_mtime:
#             with open(recipes_file) as f:
#                 recipes = yaml.safe_load(f)
#     if not recipes:
#         recipes = {}
#         for recipe_file in recipe_files:
#             recipe_dir = recipe_file.parent
#             with tempfile.TemporaryDirectory() as tmp:
#                 command = [
#                     "rattler-build",
#                     "build",
#                     "--experimental",
#                     "--render-only",
#                     "-r",
#                     str(recipe_dir),
#                     "-q",
#                     "--output-dir",
#                     tmp,
#                 ]
#                 if verbose:
#                     print("Reading", recipe_file, file=verbose, flush=True)
#                 try:
#                     recipe_str = subprocess.check_output(
#                         command, stderr=subprocess.DEVNULL
#                     )
#                 except subprocess.CalledProcessError:
#                     print(
#                         "ERROR: command failed:",
#                         " ".join(command),
#                         file=sys.stderr,
#                         flush=True,
#                     )
#                     continue

#             recipe = yaml.safe_load(recipe_str)["recipe"]
#             recipe["recipe_dir"] = str(recipe_dir)
#             if verbose:
#                 print(
#                     "  ->",
#                     recipe["package"]["name"],
#                     recipe["package"]["version"],
#                     file=verbose,
#                     flush=True,
#                 )
#             recipes[recipe["package"]["name"]] = recipe
#         with open(recipes_file, "w") as f:
#             yaml.safe_dump(recipes, f)
#     return recipes


def sorted_recipes_packages():
    # Put recipes in dict
    recipes = {i["package"]["name"]: i for i in read_recipes()}
    # Parse recipes dependencies
    ready = set(recipes)
    waiting = set()
    dependent = {}
    depends = {}
    for package_name, recipe in recipes.items():
        for _, requirements in recipe.get("requirements").items():
            for requirement in requirements:
                if not isinstance(requirement, str):
                    continue
                dependency = requirement.split(None, 1)[0]
                if dependency in recipes:
                    ready.discard(package_name)
                    waiting.add(package_name)
                    depends.setdefault(package_name, set()).add(dependency)
                    dependent.setdefault(dependency, set()).add(package_name)

    done = set()
    while ready:
        package = ready.pop()
        yield package, recipes[package]["recipe_dir"]
        done.add(package)
        for r in dependent.get(package, ()):
            if all(i in done for i in depends.get(r, ())):
                waiting.discard(r)
                ready.add(r)


def forged_packages(name_re):
    if isinstance(name_re, str):
        name_re = re.compile(name_re)
    for repodata_file in (pixi_root / "forge").glob("*/repodata.json"):
        with open(repodata_file) as f:
            repodata = json.load(f)
        for file, package_info in repodata.get("packages.conda", {}).items():
            name = package_info["name"]
            if name_re.match(name):
                package_info["path"] = str(pathlib.Path(repodata_file).parent / file)
                yield package_info


def read_pixi_config():
    with open(pixi_root / "pixi.toml") as f:
        return toml.load(f)


def write_pixi_config(pixi_config):
    with open(pixi_root / "pixi.toml", "w") as f:
        toml.dump(pixi_config, f, encoder=toml.TomlPreserveCommentEncoder())
