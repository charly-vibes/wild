# devenv.sh — single source of truth for wild's toolchain (spike for DDL-irv).
# Verify: devenv shell -- just ci
{ pkgs, ... }: {
  packages = with pkgs; [
    just # task runner (`just ci` is the single QA entry point)
    lefthook # git hooks (lefthook.yml)
    git
  ];

  # pytest + jsonschema pins come from requirements-dev.txt (installed into the venv).
  languages.python = {
    enable = true;
    venv = {
      enable = true;
      requirements = ./requirements-dev.txt;
    };
  };
}
