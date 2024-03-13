import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import toml
import yaml

pixi_root = pathlib.Path(os.environ["PIXI_PROJECT_ROOT"])


def read_recipes(verbose=None):
    for recipe_file in (pixi_root / "recipes").glob("*/recipe.yaml"):
        with open(recipe_file) as f:
            recipe = yaml.safe_load(f)
            recipe["recipe_dir"] = str(recipe_file.parent)
            yield recipe


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


def get_test_commands(config=None, log_lines=None):
    """
    Use ctest to extract command lines to execute to run tests.
    This function returns a dictionary whose keys are name of a test (i.e.
    'axon', 'soma', etc.) and values are a list of commands to run to perform
    the test.

    If casa-distro is used, three options must be given:
      casa_distro_cmd: the casa_distro executable
      config: a casa-distro environment dictionary.
      log_lines: a list that is extended with log lines for
                 the test extraction process.
    """
    cmd = ["ctest", "--print-labels"]
    # universal_newlines is the old name to request text-mode (text=True)
    o = subprocess.check_output(cmd, bufsize=-1, universal_newlines=True)
    labels = [i.strip() for i in o.split("\n")[2:] if i.strip()]
    if log_lines is not None:
        log_lines += ["$ " + " ".join(shlex.quote(arg) for arg in cmd), o, "\n"]
    tests = {}
    for label in labels:
        cmd = ["ctest", "-V", "-L", f"^{label}$"]
        env = os.environ.copy()
        env["BRAINVISA_TEST_REMOTE_COMMAND"] = "echo"
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=-1,
            universal_newlines=True,
            env=env,
        )
        o, stderr = p.communicate()
        if log_lines is not None:
            log_lines += ["$ " + " ".join(shlex_quote(arg) for arg in cmd), o, "\n"]
        if p.returncode != 0:
            # We want to hide stderr unless ctest returns a nonzero exit
            # code. In the case of test filtering where no tests are
            # matched (e.g. with ctest_options=['-R', 'dummyfilter']), the
            # annoying message 'No tests were found!!!' is printed to
            # stderr by ctest, but it exits with return code 0.
            sys.stderr.write(stderr)
            raise RuntimeError("ctest failed with the above error")
        o = o.split("\n")
        # Extract the third line that follows each line containing ': Test
        # command:'
        commands = []
        i = 0
        while i < len(o):
            line = o[i]
            m = re.match(r"(^[^:]*): Test command: .*$", line)
            if m:
                prefix = f"{m.group(1)}: "
                command = None
                i += 1
                while i < len(o) and o[i].startswith(prefix):
                    command = o[i][len(prefix) :]
                    i += 1
                if command:
                    commands.append(command)
            i += 1
        if commands:
            tests[label] = commands
    if log_lines is not None:
        log_lines += [
            "Final test dictionary:",
            json.dumps(tests, indent=4, separators=(",", ": ")),
        ]
    return tests
