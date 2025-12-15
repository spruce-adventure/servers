{
  inputs = {
    nixpkgs.url = "https://channels.nixos.org/nixos-25.11/nixexprs.tar.xz";
    nixpkgs-unstable.url = "https://channels.nixos.org/nixpkgs-unstable/nixexprs.tar.xz";
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs-unstable";
    };
  };
  outputs =
    inputs@{ self, nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      modules = import ./modules/top-level/all-modules.nix { inherit lib; };
      eachSystem =
        f:
        lib.genAttrs lib.systems.flakeExposed (
          system:
          f {
            pkgs = import nixpkgs { inherit system; };
            inherit system;
          }
        );
      mkHost =
        hostname:
        lib.nixosSystem {
          modules = [
            ./hosts/${hostname}
          ] ++ modules.nixos;

          specialArgs = {
            inherit inputs self;
          };
        };
    in
    {
      nixosConfigurations = lib.flip lib.genAttrs mkHost [
        "pine"
        "sequoia"
      ];
      packages = eachSystem (
        { pkgs, ... }: import ./packages/top-level/all-packages.nix { inherit pkgs inputs self; }
      );
      devShell = eachSystem (
        { pkgs, ... }:
        pkgs.mkShellNoCC {
          packages = lib.attrValues {
            inherit (pkgs)
              nixd
              sops
              age
              ssh-to-age
              wireguard-tools
              ;
          };
        }
      );
      formatter = eachSystem (system: inputs.nixpkgs-unstable.legacyPackages.${system}.nixfmt-tree);
    };
}
