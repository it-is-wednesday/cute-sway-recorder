{
  description = "Cute Sway Recorder packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    # Last working commit from nixos-small-unstable
    nixpkgs.url =
      "github:NixOS/nixpkgs?rev=75e28c029ef2605f9841e0baa335d70065fe7ae2";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        cute-sway-recorder = { poetry2nix, lib, makeDesktopItem }:
          let
            package = poetry2nix.mkPoetryApplication { projectDir = ./.; };
            desktopItem = makeDesktopItem {
              name = "cute-sway-recorder";
              desktopName = "Cute Sway Recorder";
              icon = "cute-sway-recorder";
              exec = "${package}/bin/cute-sway-recorder";
              categories = [ "Utility" ];
              type = "Application";
            };
          in package.overrideAttrs (old: {
            buildInputs = (old.buildInputs or [ ]) ++ [ desktopItem ];
            postInstall = ''
              mkdir -p $out/share/applications
              mkdir -p $out/share/icons/hicolor/256x256/apps

              cp ${
                ./assets/icon.png
              } $out/share/icons/hicolor/256x256/apps/cute-sway-recorder.png
              cp ${desktopItem}/share/applications/* $out/share/applications/
            '';
          });
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            poetry2nix.overlays.default
            (final: _: {
              cute-sway-recorder = final.callPackage cute-sway-recorder { };
            })
          ];
        };
      in {
        packages.default = pkgs.cute-sway-recorder;
        devShells = {
          # Shell for app dependencies.
          #
          #     nix develop
          #
          # Use this shell for developing your app.
          default = pkgs.mkShell { inputsFrom = [ pkgs.cute-sway-recorder ]; };

          # Shell for poetry.
          #
          #     nix develop .#poetry
          #
          # Use this shell for changes to pyproject.toml and poetry.lock.
          poetry = pkgs.mkShell { packages = [ pkgs.poetry ]; };
        };
        legacyPackages = pkgs;
      });
}
