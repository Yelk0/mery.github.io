#!/usr/bin/env bash
# Download everything the comparison needs:
#   data/80109.csv       total GDP by region (INE table 80109)
#   data/80110.csv       GDP per capita by region (INE table 80110)
#   data/cre-volume.csv  real GDP growth, unrounded (CRE workbook)
#   data/65321.csv       public and private jobs (INE EPA table 65321)
#   data/be1306.csv      community debt stock (Bank of Spain 13.6)
#   data/health.csv      December surgical waiting time (Ministry of Health)
#   data/schools.csv     early school leaving (Eurostat)
#   data/care.csv        dependency care still waiting (IMSERSO)
#   data/balance.csv     national-accounts surplus or deficit (IGAE)
#   data/budget.csv      settled budget by spending policy (Hacienda)
#   data/people.json     presidents and cabinet members
set -euo pipefail
cd "$(dirname "$0")"
./download-ine-80110.sh -t 80109
./download-ine-80110.sh
python3 download-cre-volume.py
./download-ine-80110.sh -t 65321
curl --fail --location --retry 3 --retry-delay 2 --silent --show-error \
  --user-agent "plan-mery/bde-downloader" \
  --output data/be1306.csv \
  "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1306.csv"
python3 download-health.py
python3 download-schools.py
python3 download-care.py
python3 download-balance.py
python3 download-budget.py
python3 download-office-holders.py
