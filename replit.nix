{pkgs}: {
  deps = [
    pkgs.bash
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.glibcLocales
    pkgs.xcbuild
    pkgs.swig
    pkgs.openjpeg
    pkgs.mupdf
    pkgs.libjpeg_turbo
    pkgs.jbig2dec
    pkgs.harfbuzz
    pkgs.gumbo
    pkgs.freetype
    pkgs.libxcrypt
    pkgs.libyaml
    pkgs.postgresql
  ];
}
{pkgs}: {
  deps = [
    pkgs.python311
    pkgs.postgresql
  ];
}
