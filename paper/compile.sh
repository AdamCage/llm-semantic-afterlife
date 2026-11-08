#!/usr/bin/env bash
# Compile the English and/or Russian manuscripts to paper/releases/.
# Usage: bash paper/compile.sh [en|ru|all|anonymous]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
KIND="${1:-all}"
BUILD="${ROOT}/build"
RELEASES="${ROOT}/releases"

mkdir -p "${BUILD}" "${RELEASES}"

# Use the published vector figure; relocate only its legend in the build
# copy. The original experimental bundle is never rewritten or re-estimated.
FIGURE_SOURCE="${ROOT}/../artifacts/stage-13/tau_escape_s12/tau_escape_s12.svg"
FIGURE_BUILD="${BUILD}/figures"
mkdir -p "${FIGURE_BUILD}"
if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "rsvg-convert is required (Ubuntu package: librsvg2-bin)" >&2
  exit 1
fi
if [[ "$(grep -c 'id="legend_1"' "${FIGURE_SOURCE}")" != "1" ]]; then
  echo "expected one legend group in ${FIGURE_SOURCE}" >&2
  exit 1
fi
sed -f "${ROOT}/figure-layout.sed" "${FIGURE_SOURCE}" \
  > "${FIGURE_BUILD}/tau_escape_s12.svg"
rsvg-convert --format=pdf \
  --output "${FIGURE_BUILD}/tau_escape_s12.pdf" \
  "${FIGURE_BUILD}/tau_escape_s12.svg"

compile_one() {
  local src="$1"
  local job="$2"
  local out="$3"
  echo "=== pdflatex ${src} ==="
  # The vendored tmlr.bst is in the working directory. Preserve the default
  # TeX search tree; BIBINPUTS must include paper/ so refs.bib resolves.
  unset BSTINPUTS || true
  export BIBINPUTS="${ROOT}:"
  (
    cd "${ROOT}"
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD}" -jobname="${job}" "${src}"
    # Relative path only: Debian TeX sets openout_any=p, so bibtex refuses
    # an absolute aux path. Do not cd into build/ (that hides paper/refs.bib
    # unless BIBINPUTS is set); keep the default BSTINPUTS search path.
    bibtex "build/${job}"
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD}" -jobname="${job}" "${src}"
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD}" -jobname="${job}" "${src}"
    # A complete translation can move floats again after the bibliography
    # settles. Resolve that last label change before copying the release.
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD}" -jobname="${job}" "${src}"
  )
  if [[ ! -s "${BUILD}/${job}.bbl" ]]; then
    echo "empty bibliography: ${BUILD}/${job}.bbl" >&2
    cat "${BUILD}/${job}.blg" >&2 || true
    exit 1
  fi
  if grep -Eq 'There were undefined references|There were undefined citations|Label\(s\) may have changed|multiply defined' "${BUILD}/${job}.log"; then
    echo "unresolved references in ${BUILD}/${job}.log" >&2
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
      pdflatex -interaction=nonstopmode -halt-on-error \
        -output-directory="${BUILD}" -jobname="anonymous" \
        "\def\TMLRANON{1}\input{main.tex}"
    )
    if [[ ! -s "${BUILD}/anonymous.bbl" ]]; then
      echo "empty bibliography: ${BUILD}/anonymous.bbl" >&2
      cat "${BUILD}/anonymous.blg" >&2 || true
      exit 1
    fi
    if grep -Eq 'There were undefined references|There were undefined citations|Label\(s\) may have changed|multiply defined' "${BUILD}/anonymous.log"; then
      echo "unresolved references in ${BUILD}/anonymous.log" >&2
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
