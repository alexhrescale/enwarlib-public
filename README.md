# enwarlib: a tool to help manage env var specification

  this library is compatible with python2 and python3

  `python setup.py install`
  
## dev setup

   if you have [nix-shell](https://nixos.org/nix/) available, clone this
   repository and run `nix-shell`, and your dev setup should be ready to go
   (`pip-sync` will be run automatically). To use python2, modify default.nix
   
   if not, follow a standard virtualenv setup. This project's dependencies
   are managed using [pip-tools](https://github.com/jazzband/pip-tools)

## tests

    once inside the nix-shell, you should be able to run tests directly using
    `python -m unittest discover tests`

## CLI usage example

   `env | python -m enwarlib --json-array | python -m enwarlib --bash-exports`
   
   
