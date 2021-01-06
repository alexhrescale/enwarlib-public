with import <nixpkgs> {};

stdenv.mkDerivation rec {
    name = "envvarwar";
    env = pkgs.buildEnv {
        name = name;
        paths = buildInputs;
    };
    buildInputs = [
        git
        python37Full
    ];
    shellHook = ''
        export SOURCE_DATE_EPOCH=$(date +%s)
        VIRTUAL_ENV=''${VIRTUAL_ENV-venv}
        if [ -e $VIRTUAL_ENV ]; then
            echo "using existing virtualenv at $VIRTUAL_ENV..."
            source $VIRTUAL_ENV/bin/activate
        else
            echo "creating virtualenv at $VIRTUAL_ENV..."
            python -m venv $VIRTUAL_ENV
            source $VIRTUAL_ENV/bin/activate
            pip install -e ".[dev]"
        fi
        pip-sync
    '';
}

