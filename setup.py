import os
import subprocess
import toml

p = os.environ["PIXI_PROJECT_ROOT"]
tf = os.path.join(p, "pixi.toml")
f = f"file://{os.path.join(p, 'forge')}"
t = toml.load(tf, decoder=toml.TomlPreserveCommentDecoder())
if f not in t["project"]["channels"]:
    t["project"]["channels"].append(f)
    toml.dump(t, open(tf, "w"), encoder=toml.TomlPreserveCommentEncoder())

if not os.path.exists(os.environ["CASA_SRC"]):
    os.mkdir(os.environ["CASA_SRC"])

if not os.path.exists(os.path.join(os.environ["CASA_SRC"], "brainvisa-cmake")):
    subprocess.check_call(
        [
            "git",
            "-C",
            os.environ["CASA_SRC"],
            "clone",
            "https://github.com/brainvisa/brainvisa-cmake",
        ]
    )
