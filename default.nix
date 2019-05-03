with import <nixpkgs> {};

stdenv.mkDerivation rec {
    name = "envvarwar";
    env = pkgs.buildEnv {
        name = name;
        paths = buildInputs;
    };
    buildInputs = [
        git
        # python27Packages.virtualenv
        python37Packages.virtualenv
    ];
    shellHook = ''
        export SOURCE_DATE_EPOCH=$(date +%s);
        export PYTHONPATH=.:$PYTHONPATH;

        PYTHON_VERSION=$(python -c 'import sys;print(sys.version_info.major)');
        VIRTUAL_ENV=''${VIRTUAL_ENV-venv$PYTHON_VERSION};
        if [ ! $VIRTUAL_ENV ]; then
            echo "using existing virtualenv at $VIRTUAL_ENV..."
            source $VIRTUAL_ENV/bin/activate
        else
            echo "creating virtualenv at $VIRTUAL_ENV..."
            if [ $PYTHON_VERSION -eq 2 ]; then
                virtualenv $VIRTUAL_ENV
            else
                python -m venv $VIRTUAL_ENV
            fi
            source $VIRTUAL_ENV/bin/activate
            python setup.py install
        fi
        if ! [ -x "$(command -v pip-sync)" ]; then
            echo 'pip-sync not found; installing pip-tools...'
            pip install pip-tools
        fi
        pip-sync
    '';
}

