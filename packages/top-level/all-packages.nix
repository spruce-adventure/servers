{
  pkgs,
  inputs,
  self,
}@args:

let
  pkgs = args.pkgs.extend (
    _: _: {
      inherit inputs self;
    }
  );
  inherit (builtins) readDir;
  inherit (pkgs) lib;

  inherit (lib)
    attrNames
    filter
    filterAttrs
    pathExists
    listToAttrs
    ;
  inherit (lib.trivial) pipe;

  childPaths = path: attrNames (filterAttrs (_: type: type == "directory") (readDir path));
  basePath = ../by-name;
  mkPath = dir: {
    name = dir;
    path = "${basePath}/${dir}/package.nix";
  };
  callRaw = raw: {
    inherit (raw) name;
    value = pkgs.callPackage raw.path { };
  };
in
pipe basePath [
  childPaths
  (map mkPath)
  (filter (raw: pathExists raw.path))
  (map callRaw)
  listToAttrs
]
