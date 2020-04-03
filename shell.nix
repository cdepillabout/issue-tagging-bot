
let
  nixpkgs-src = builtins.fetchTarball {
    # Recent version of nixpkgs master as of 2020-03-30.
    url = "https://github.com/NixOS/nixpkgs/archive/570e3edc8519c666b74a5ca469e1dd286902691d.tar.gz";
    sha256 = "sha256:0aw6rw4r13jij8hn27z2pbilvwzcpvaicc59agqznmr2bd2742xl";
  };

  nixpkgs = import nixpkgs-src {};
in

with nixpkgs;

let
  pythonEnv = python37.withPackages (ps: with ps; [
    PyGithub

    # dev tools
    black
    mypy
  ]);
in
pythonEnv.env

