export CASA_DISTRO="brainvisa"
export CASA_BRANCH="master"
export CASA="$PIXI_PROJECT_ROOT"
export CASA_CONF="$CASA/conf"
export CASA_SRC="$CASA/src"
export CASA_BUILD="$CASA/build"
export CASA_TEST="$CASA/test"
export PATH="$CASA/src/brainvisa-cmake/bin:$CASA/build/bin:$CONDA_PREFIX/x86_64-conda-linux-gnu/sysroot/usr/bin:$PATH"
export CMAKE_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/x86_64-conda-linux-gnu/sysroot/usr/lib64"
export BRAINVISA_BVMAKER_CFG="$CASA/conf/bv_maker.cfg"
export LD_LIBRARY_PATH="$CASA/build/lib:$LD_LIBRARY_PATH"
python_short=$(python -c 'import sys; print(".".join(str(i) for i in sys.version_info[0:2]))')
export PYTHONPATH="$CASA/src/brainvisa-cmake/python:$CASA/build/lib/python${python_short}/site-packages"

if [ ! -e "$CASA_SRC" ]; then
    mkdir "$CASA_SRC"
fi
if [ ! -e "$CASA_SRC/brainvisa-cmake" ]; then
    git -C "$CASA_SRC" clone https://github.com/brainvisa/brainvisa-cmake
fi
