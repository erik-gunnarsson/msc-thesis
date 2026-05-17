#!/usr/bin/env bash
# Build PDF from LaTeX in this directory.
# Usage: ./build_pdf.sh [file.tex]   (default: wiod_regression_table.tex)
#
# Requires: MacTeX, TeX Live, or BasicTeX (pdflatex). Optional: latexmk.
# uv cannot install TeX — install from https://www.tug.org/mactex/ or `brew install --cask basictex`

set -euo pipefail

# Put TeX binaries on PATH (BasicTeX, MacTeX, or TeX Live year trees).
_prepend_tex_path() {
  local d
  shopt -s nullglob
  for d in \
    /Library/TeX/texbin \
    /usr/local/texlive/*/bin/universal-darwin \
    /usr/local/texlive/*/bin/arm64-darwin \
    /usr/local/texlive/*/bin/x86_64-darwinlegacy
  do
    [[ -x "${d}/pdflatex" ]] && PATH="${d}:${PATH}"
  done
  shopt -u nullglob
  export PATH
}
_prepend_tex_path

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

TEX="${1:-wiod_regression_table.tex}"
BASE="${TEX%.tex}"
PDF="${BASE}.pdf"

if ! [[ -f "$TEX" ]]; then
  echo "error: not found: $TEX" >&2
  exit 1
fi

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error "$TEX"
else
  echo "latexmk not found; using pdflatex twice (longtable often needs two passes)." >&2
  if ! command -v pdflatex >/dev/null 2>&1; then
    echo "error: pdflatex not found on PATH (checked /Library/TeX/texbin and common TeX Live paths)." >&2
    echo "" >&2
    echo "If 'brew install --cask basictex' says already installed but this fails, the .pkg installer" >&2
    echo "never completed — Homebrew records the cask without /Library/TeX/texbin/pdflatex." >&2
    echo "Fix: reinstall the cask and finish the installer (password prompt):" >&2
    echo "  brew reinstall --cask basictex" >&2
    echo "Or uninstall then install:" >&2
    echo "  brew uninstall --cask basictex && brew install --cask basictex" >&2
    echo "Then verify:  test -x /Library/TeX/texbin/pdflatex && echo OK" >&2
    echo "" >&2
    echo "Alternative — Docker (no local TeX):" >&2
    echo "  ./build_pdf_docker.sh" >&2
    exit 1
  fi
  pdflatex -interaction=nonstopmode -halt-on-error "$TEX"
  pdflatex -interaction=nonstopmode -halt-on-error "$TEX"
fi

echo "Wrote: $DIR/$PDF"
