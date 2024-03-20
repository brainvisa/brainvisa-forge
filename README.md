# soma-forge
Build projects from source and create Conda packages (experimental)

## Prerequisite
Whatever you want to do, you must first [install Pixi](https://pixi.sh). It is a binary without dependency to put somewhere in the PATH. The install script copy it in the `bin` subdirectory of a parent directory that can be specified (default is `$HOME/.pixi`) with `PIXI_HOME`:

```
# To install it in /somewhere/bin/pixi
curl -fsSL https://pixi.sh/install.sh | env PIXI_HOME=/somewhere bash
```

## Test latest packages

Very preliminary packages are sometime deployed on BrainVISA site. On can test these package without compilation with the following commands (it is also possible to use conda or mamba instead of pixi):
```
mkdir /tmp/test
cd /tmp/test
pixi init
pixi project channel add https://brainvisa.info/download/conda
pixi add morphologist
pixi run brainvisa
```

For an interactive session use:
```
cd /tmp/test
pixi shell
...
```
## Packages

The packages currently built have the following dependencies:
- green: package containing brainvisa-cmake components ;
- olive: empty package with dependencies ;
- bisque: external dependency not found in conda-forge ; 
- light blue: package from conda-forge.

![dependencies](https://github.com/brainvisa/soma-forge/assets/3062350/c34edacd-ec27-49b4-b68d-75505390d63b)

## Building from sources and packaging

A build and/or packaging environement is entirerly contained in a single directory. This directory is first initialized by cloning soma-forge GitHub project. Then a setup script is executed, it will create the packages for external software, install all required dependencies and download brainvisa-cmake sources to make `bv_maker` ready to use.

```
git clone https://github.com/brainvisa/soma-forge
cd soma-forge
pixi run setup
```

Now one can activate the environment with the following command:
```
# be sure to be in the soma-forge directory
pixi shell
```

`bv_maker` can be used directly and built programs are in the PATH and ready to be used.

Conda packages installed via pixi (as dependencies) are found in the `.pixi` sub-directory in the soma-forge directory.

If one needs to make packages, use the following command:

```
pixi run forge --no-test
```

If not already done, this runs `pixi run build` that executes `bv_maker` and creates a `build/success` file when all steps (except sources) are successful. Then it creates non existing packages for all internal or external software. By default, packages are only created when tests are successful but some packages (such as `soma` that contains Aims) need some reference data for testing therefore I recommend to skip tests with `--no-test` until a procedure is created to generate these data.
