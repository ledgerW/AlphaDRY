
{ pkgs }: {
  deps = [
    pkgs.postgresql
    pkgs.libxcrypt
    pkgs.bash
    pkgs.netcat
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
