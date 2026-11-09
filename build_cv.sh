#!/usr/bin/env bash
# Compile the canonical CV without leaving LaTeX byproducts in the website.
set -euo pipefail
cd "$(dirname "$0")"
cv_build_dir=$(mktemp -d "${TMPDIR:-/tmp}/soumitra-cv.XXXXXX")
trap 'rm -rf "$cv_build_dir"' EXIT
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -output-directory="$cv_build_dir" Soumitra_Shukla_CV.tex
if grep -Eq 'Overfull|LaTeX Error|undefined references|undefined citations' "$cv_build_dir/Soumitra_Shukla_CV.log"; then
  echo 'CV build has layout or reference warnings; inspect the log before publishing.' >&2
  exit 1
fi
cp "$cv_build_dir/Soumitra_Shukla_CV.pdf" Soumitra_Shukla_CV.pdf
