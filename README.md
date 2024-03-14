# soma-forge
Build projects from source and create Conda packages (experimental)

First install pixi it is a binary without dependency to put somewhere in the PATH. The install script copy it in the `bin` subdirectory of a parent directory that can be given with `PIXI_HOME`:

```
# To install it in /somewhere/bin/pixi
curl -fsSL https://pixi.sh/install.sh | env PIXI_HOME=/somewhere bash
```

Then setup the build environment. This will build and create the packages for external software that are not already in conda-forge and then download sources of brainvisa-cmake:
```
git clone https://github.com/brainvisa/casa-forge
cd casa-forge
pixi run setup
```

Now one can activate the environment with the following command:
```
# be sure to be in the casa-forge directory
pixi shell
```

`bv_maker` cand be used directly and built programs are in the PATH and ready to be used.

If one needs to make packages, use the following command:

```
pixi run forge --no-test
```

If not already done, this runs `pixi run build` that executes `bv_maker` and create a `build/success` file when all steps (except sources) are successful. Then it creates non existing packages for all internal or external software. By default, packages are only created when tests are successful but some packages (such as `soma` that contains Aims) needs some reference data for testing therefor I recommend to skip tests until a procedure is created to generate these data.
