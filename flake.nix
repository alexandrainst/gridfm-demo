{
  description = "Nix flake for a development shell with Prettier and markdownlint-cli2";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs = inputs: {
    devShells = builtins.mapAttrs (system: pkgs: {
      default = pkgs.mkShell {
        packages = [
          pkgs.prettier
          pkgs.markdownlint-cli2
          pkgs.uv
          pkgs.git
          pkgs.tree
        ];
        shellHook = ''
          if [ -f .venv/bin/activate ]; then
            source .venv/bin/activate
          fi
        '';
      };
    }) inputs.nixpkgs.legacyPackages;
  };
}
