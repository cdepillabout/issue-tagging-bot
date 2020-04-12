
let
  nixpkgs-src = builtins.fetchTarball {
    # Recent version of nixpkgs master as of 2020-03-30.
    url = "https://github.com/NixOS/nixpkgs/archive/570e3edc8519c666b74a5ca469e1dd286902691d.tar.gz";
    sha256 = "sha256:0aw6rw4r13jij8hn27z2pbilvwzcpvaicc59agqznmr2bd2742xl";
  };

  nixpkgs = import nixpkgs-src { config = { allowUnfree = true; }; };
in

with nixpkgs;

let
  pythonEnv = python37.buildEnv.override {
    extraLibs = with python37Packages; [
      numpy
      pandas
      PyGithub
      scikitlearn
      tensorflow-bin

      # dev tools
      black
      ipython
      mypy
    ];

    # There is a collision in tensorboard and tensorflow, because they both try
    # to install the tensorboard binary.
    ignoreCollisions = true;
  };
in
pythonEnv.env

