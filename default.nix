with import <nixpkgs> {};

stdenv.mkDerivation rec {
    name = "envvarwar";
    env = pkgs.buildEnv {
        name = name;
        paths = buildInputs;
    };
    buildInputs = [
        git
        python27Packages.virtualenv
    ];
    shellHook = ''
        export SOURCE_DATE_EPOCH=$(date +%s);
        export PYTHONPATH=.:$PYTHONPATH

        if [ ! -e venv ]; then
            virtualenv venv
        fi
        source venv/bin/activate
        if ! [ -x "$(command -v pip-sync)" ]; then
            echo 'pip-sync not found; installing pip-tools...'
            pip install pip-tools
        fi
        pip-sync
    '';
}

