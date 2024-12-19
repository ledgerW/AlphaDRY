
{ pkgs }: {
  deps = [
    pkgs.postgresql
    pkgs.libxcrypt
    pkgs.bash
    pkgs.glibcLocales
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.libyaml
    pkgs.python311
    pkgs.postgresql_16
    pkgs.nodejs
  ];
}
