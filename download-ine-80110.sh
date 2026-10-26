#!/usr/bin/env bash
# Download INE table 80110: PIB per cápita at current prices, by autonomous
# community, autonomous city, and province.
#
# The table page only renders a filtered view:
#   https://www.ine.es/jaxiT3/Tabla.htm?t=80110&L=0
# The complete series (every territory, magnitude, and year) is the file
# linked from "Formatos de descarga":
#   https://www.ine.es/jaxiT3/dlgExport.htm?t=80110
#
# Default CSV columns (semicolon-separated, UTF-8 with a BOM):
#   Comunidades y Ciudades Autónomas y Provincias;Magnitud;Periodo;Total
# Magnitudes: Valor (euros, "." thousands separator), Índice España = 100,
# and Tasa de Variación Interanual ("," decimal separator). Empty cells are "".

set -euo pipefail

TABLE_ID="80110"
LANG="es"
FORMAT="csv"
OUT_DIR="data"

usage() {
  cat <<'EOF'
Usage: download-ine-80110.sh [options]

Download the full INE table 80110 (GDP per capita, current prices,
autonomous communities, cities, and provinces).

Options:
  -f FORMAT   csv (default), tsv, xlsx, px, json, all
  -o DIR      output directory (default: data)
  -t ID       INE table id (default: 80110)
  -l LANG     file language: es or en (default: es)
  -h          show this help

csv is semicolon-separated. tsv is tab-separated. Both contain the full
series, not the single year selected on the web page.
EOF
}

while getopts ":f:o:t:l:h" opt; do
  case "$opt" in
    f) FORMAT="$OPTARG" ;;
    o) OUT_DIR="$OPTARG" ;;
    t) TABLE_ID="$OPTARG" ;;
    l) LANG="$OPTARG" ;;
    h)
      usage
      exit 0
      ;;
    :)
      echo "Option -$OPTARG needs a value." >&2
      usage >&2
      exit 1
      ;;
    \?)
      echo "Unknown option: -$OPTARG" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$LANG" in
  es|en) ;;
  *)
    echo "Language must be es or en, got: $LANG" >&2
    exit 1
    ;;
esac

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required." >&2
  exit 1
fi

declare -a FORMATS
case "$FORMAT" in
  all) FORMATS=(csv tsv xlsx px json) ;;
  csv|tsv|xlsx|px|json) FORMATS=("$FORMAT") ;;
  *)
    echo "Unknown format: $FORMAT" >&2
    echo "Use csv, tsv, xlsx, px, json, or all." >&2
    exit 1
    ;;
esac

url_for() {
  local fmt="$1"
  case "$fmt" in
    csv) echo "https://www.ine.es/jaxiT3/files/t/${LANG}/csv_bdsc/${TABLE_ID}.csv" ;;
    tsv) echo "https://www.ine.es/jaxiT3/files/t/${LANG}/csv_bd/${TABLE_ID}.csv" ;;
    xlsx) echo "https://www.ine.es/jaxiT3/files/t/${LANG}/xlsx/${TABLE_ID}.xlsx" ;;
    px) echo "https://www.ine.es/jaxiT3/files/t/${LANG}/px/${TABLE_ID}.px" ;;
    json) echo "https://servicios.ine.es/wstempus/jsCache/${LANG}/DATOS_TABLA/${TABLE_ID}?tip=AM" ;;
  esac
}

extension_for() {
  case "$1" in
    tsv) echo "tsv" ;;
    *) echo "$1" ;;
  esac
}

mkdir -p "$OUT_DIR"

download_one() {
  local fmt="$1"
  local url dest tmp header
  url="$(url_for "$fmt")"
  dest="${OUT_DIR}/${TABLE_ID}.$(extension_for "$fmt")"
  tmp="$(mktemp)"
  header="$(mktemp)"

  echo "Downloading ${fmt} -> ${dest}"
  if ! curl --fail --location --retry 3 --retry-delay 2 \
      --silent --show-error \
      --user-agent "plan-mery/ine-downloader" \
      --dump-header "$header" \
      --output "$tmp" \
      "$url"; then
    rm -f "$tmp" "$header"
    echo "Download failed: $url" >&2
    exit 1
  fi

  if [[ ! -s "$tmp" ]]; then
    rm -f "$tmp" "$header"
    echo "Downloaded file is empty: $url" >&2
    exit 1
  fi

  if [[ "$fmt" == "csv" || "$fmt" == "tsv" ]]; then
    local sep first
    if [[ "$fmt" == "csv" ]]; then
      sep=";"
    else
      sep=$'\t'
    fi
    first="$(head -n 1 "$tmp" | tr -d '\r')"
    case "$first" in
      *"Periodo"*"${sep}"*) ;;
      *)
        rm -f "$tmp" "$header"
        echo "Unexpected header in $url:" >&2
        echo "$first" >&2
        exit 1
        ;;
    esac
  fi

  mv "$tmp" "$dest"
  local modified bytes rows
  modified="$(awk 'BEGIN{IGNORECASE=1} /^Last-Modified:/ {sub(/\r$/,""); print substr($0, index($0,$2)); exit}' "$header")"
  rm -f "$header"
  bytes="$(wc -c < "$dest" | tr -d ' ')"
  echo "  ${bytes} bytes${modified:+, INE last modified ${modified}}"
  if [[ "$fmt" == "csv" || "$fmt" == "tsv" ]]; then
    rows="$(($(wc -l < "$dest" | tr -d ' ') - 1))"
    echo "  ${rows} data rows"
  fi
}

for fmt in "${FORMATS[@]}"; do
  download_one "$fmt"
done
