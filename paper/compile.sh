#!/usr/bin/env bash
# Compile the English and/or Russian manuscripts to paper/releases/.
# Usage: bash paper/compile.sh [en|ru|all|anonymous]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
KIND="${1:-all}"
BUILD="${ROOT}/build"
RELEASES="${ROOT}/releases"

mkdir -p "${BUILD}" "${RELEASES}"

compile_one() {
  local src="$1"
  local job="$2"
  local out="$3"
  echo "=== pdflatex ${src} ==="
  # Do not set BSTINPUTS: a value that is only paper/ hides plainnat.bst in
  # the TeX tree. BIBINPUTS must include paper/ so \bibliography{refs} resolves.
  unset BSTINPUTS || true
  export BIBINPUTS="${ROOT}:"
  (
    cd "${ROOT}"
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD}" -jobname="${job}" "${src}"
    # Relative path only: Debian TeX sets openout_any=p, so bibtex refuses
    # an absolute aux path. Do not cd into build/ (that hides paper/refs.bib
    # unless BIBINPUTS is set) and do not set BSTINPUTS (that hides plainnat.bst).
    bibtex "build/${job}"
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD}" -jobname="${job}" "${src}"
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD}" -jobname="${job}" "${src}"
  )
  if [[ ! -s "${BUILD}/${job}.bbl" ]]; then
    echo "empty bibliography: ${BUILD}/${job}.bbl" >&2
    cat "${BUILD}/${job}.blg" >&2 || true
    exit 1
  fi
  cp "${BUILD}/${job}.pdf" "${RELEASES}/${out}"
  echo "wrote ${RELEASES}/${out}"
}

case "${KIND}" in
  en) compile_one main.tex main semantic-afterlife-en.pdf ;;
  ru) compile_one main.ru.tex main.ru semantic-afterlife-ru.pdf ;;
  all)
    compile_one main.tex main semantic-afterlife-en.pdf
    compile_one main.ru.tex main.ru semantic-afterlife-ru.pdf
    ;;
  anonymous)
    # TMLR-anonymous English PDF. Identified EN/RU releases are unchanged.
    echo "=== pdflatex anonymous main.tex ==="
    unset BSTINPUTS || true
    export BIBINPUTS="${ROOT}:"
    (
      cd "${ROOT}"
      pdflatex -interaction=nonstopmode -halt-on-error \
        -output-directory="${BUILD}" -jobname="anonymous" \
        "\def\TMLRANON{1}\input{main.tex}"
      bibtex "build/anonymous"
      pdflatex -interaction=nonstopmode -halt-on-error \
        -output-directory="${BUILD}" -jobname="anonymous" \
        "\def\TMLRANON{1}\input{main.tex}"
      pdflatex -interaction=nonstopmode -halt-on-error \
        -output-directory="${BUILD}" -jobname="anonymous" \
        "\def\TMLRANON{1}\input{main.tex}"
    )
    if [[ ! -s "${BUILD}/anonymous.bbl" ]]; then
      echo "empty bibliography: ${BUILD}/anonymous.bbl" >&2
      cat "${BUILD}/anonymous.blg" >&2 || true
      exit 1
    fi
    cp "${BUILD}/anonymous.pdf" "${RELEASES}/semantic-afterlife-anonymous.pdf"
    echo "wrote ${RELEASES}/semantic-afterlife-anonymous.pdf"
    ;;
  *)
    echo "usage: $0 [en|ru|all|anonymous]" >&2
    exit 2
    ;;
esac
