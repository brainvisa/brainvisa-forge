# soma-forge
Build projects from source and create Conda packages (experimental)

First install pixi it is a binary without dependency to put somewhere in the PATH. The install script copy it in the `bin` subdirectory of a parent directory that can be given with `PIXI_HOME`:

```
# To install it in /somewhere/bin/pixi
curl -fsSL https://pixi.sh/install.sh | env PIXI_HOME=/somewhere bash
```

Then setup the build environment. This will build and create packages for software not in conda-forge and download sources of brainvisa-cmake:
```
git clone https://github.com/brainvisa/casa-forge
cd casa-forge
pixi run setup
```

Now one can activate the environment with the following command:
```
cd casa-forge
pixi shell
```

`bv_maker` cand be used but all compilation and packages creation can be done with the following command:

```
pixi run forge
```
