import os
import pathlib
import subprocess
import yaml
import sys

pixi_root = pathlib.Path(os.environ["PIXI_PROJECT_ROOT"])

def read_recipes(verbose=None):
    """
    Read all recipe.yaml files via rattler-build to let it resolve
    the content of the file that may contain jinja-like expressions.
    This is only package name.

    Return a dict whos keys are package names and values are recipe
    dicts. In each recipe dict, a "recipe_dir" item is added containing
    the directory of the recipe file.
    """
    if verbose is True:
        verbose = sys.stdout
    recipes = None
    recipe_files = list((pixi_root / "recipes").glob("*/recipe.yaml"))
    recipes_file = pixi_root / "recipes" / "recipes.yaml"
    if recipes_file.exists():
        if max(f.stat().st_mtime for f in recipe_files) <= recipes_file.stat().st_mtime:
            with open(recipes_file) as f:
                recipes = yaml.safe_load(f)
    if not recipes:
        recipes = {}
        for recipe_file in recipe_files:
            recipe_dir = recipe_file.parent
            command = [
                "rattler-build",
                "build",
                "--experimental",
                "--render-only",
                "-r",
                str(recipe_dir),
                "-q",
            ]
            if verbose:
                print("Reading", recipe_file, file=verbose, flush=True)
            try:
                recipe_str = subprocess.check_output(command, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print(
                    "ERROR: command failed:",
                    " ".join(command),
                    file=sys.stderr,
                    flush=True,
                )
                continue

            recipe = yaml.safe_load(recipe_str)["recipe"]
            recipe["recipe_dir"] = str(recipe_dir)
            if verbose:
                print(
                    "  ->",
                    recipe["package"]["name"],
                    recipe["package"]["version"],
                    file=verbose,
                    flush=True,
                )
            recipes[recipe["package"]["name"]] = recipe
        with open(recipes_file, "w") as f:
            yaml.safe_dump(recipes, f)
    return recipes


def parse_dependencies(recipes):
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
    return (ready, waiting, dependent, depends)


def sorted_packages(recipes):
    ready, waiting, dependent, depends = parse_dependencies(recipes)
    done = set()
    while ready:
        package = ready.pop()
        yield package
        done.add(package)
        for r in dependent.get(package, ()):
            if all(i in done for i in depends.get(r, ())):
                waiting.discard(r)
                ready.add(r)
