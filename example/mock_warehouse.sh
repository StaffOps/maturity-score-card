#!/usr/bin/env bash
# mock_warehouse.sh — séries de valores variados para o time warehouse
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
AREA="data"
TEAM="warehouse"
ENV="prod"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

echo -e "${BOLD}Verificando API em $BASE_URL ...${NC}"
if ! curl -sf "$BASE_URL/healthz" > /dev/null; then
  echo -e "${RED}API não está respondendo. Suba com: docker compose up --build${NC}"
  exit 1
fi
echo -e "${GREEN}API ok${NC}\n"

post() {
  local app=$1 scorecard=$2 metric=$3 raw=$4
  local result score
  result=$(curl -sf -X POST "$BASE_URL/score" \
    -H "Content-Type: application/json" \
    -d "{\"area\":\"$AREA\",\"team\":\"$TEAM\",\"app\":\"$app\",\"env\":\"$ENV\",\"scorecard\":\"$scorecard\",\"metric\":\"$metric\",\"raw\":$raw}" 2>/dev/null || echo '{"score":0}')
  score=$(echo "$result" | grep -o '"score":[0-9.]*' | cut -d: -f2)
  printf "    ${GREEN}✓${NC} %-30s %-25s %-25s score=${CYAN}%s${NC}\n" "$app" "$scorecard" "$metric" "$score"
}

section() { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}"; }

# ─────────────────────────────────────────────────────────────
# warehouse-ingestor  (API full — evolução gradual C→B→A)
# ─────────────────────────────────────────────────────────────
section "warehouse-ingestor (evolução C → B → A)"

echo -e "\n  ${YELLOW}snapshot: qualidade C (baseline ruim)${NC}"
post warehouse-ingestor security    image_scan           '{"critical":1,"high":3,"medium":6}'
post warehouse-ingestor security    secret_scan          '{"found":false}'
post warehouse-ingestor security    sast                 '{"critical":1,"high":2,"medium":5}'
post warehouse-ingestor security    dast                 '{"high":2,"medium":4}'
post warehouse-ingestor application libs_secrets         '{"enabled":false}'
post warehouse-ingestor application libs_observability   '{"enabled":true}'
post warehouse-ingestor application unique_db_user       '{"enabled":false}'
post warehouse-ingestor application health_check         '{"enabled":true}'
post warehouse-ingestor application unit_coverage        '{"percentage":48}'
post warehouse-ingestor application integration_coverage '{"percentage":22}'
post warehouse-ingestor application stress_test          '{"error_rate":0.02,"p95_ms":1800,"checks_pct":68}'
post warehouse-ingestor reliability sla                  '{"availability_pct":98.9}'
post warehouse-ingestor reliability change_failure_rate  '{"rate_pct":14}'
post warehouse-ingestor reliability mttr                 '{"minutes":520}'
post warehouse-ingestor reliability mttd                 '{"minutes":90}'

echo -e "\n  ${YELLOW}snapshot: qualidade B (após sprint de melhoria)${NC}"
post warehouse-ingestor security    image_scan           '{"critical":0,"high":1,"medium":3}'
post warehouse-ingestor security    secret_scan          '{"found":false}'
post warehouse-ingestor security    sast                 '{"critical":0,"high":1,"medium":4}'
post warehouse-ingestor security    dast                 '{"high":1,"medium":2}'
post warehouse-ingestor application libs_secrets         '{"enabled":true}'
post warehouse-ingestor application libs_observability   '{"enabled":true}'
post warehouse-ingestor application unique_db_user       '{"enabled":false}'
post warehouse-ingestor application health_check         '{"enabled":true}'
post warehouse-ingestor application unit_coverage        '{"percentage":71}'
post warehouse-ingestor application integration_coverage '{"percentage":44}'
post warehouse-ingestor application stress_test          '{"error_rate":0.005,"p95_ms":820,"checks_pct":89}'
post warehouse-ingestor reliability sla                  '{"availability_pct":99.6}'
post warehouse-ingestor reliability change_failure_rate  '{"rate_pct":8}'
post warehouse-ingestor reliability mttr                 '{"minutes":180}'
post warehouse-ingestor reliability mttd                 '{"minutes":25}'

echo -e "\n  ${YELLOW}snapshot: qualidade A (estado atual)${NC}"
post warehouse-ingestor security    image_scan           '{"critical":0,"high":0,"medium":1}'
post warehouse-ingestor security    secret_scan          '{"found":false}'
post warehouse-ingestor security    sast                 '{"critical":0,"high":0,"medium":2}'
post warehouse-ingestor security    dast                 '{"high":0,"medium":1}'
post warehouse-ingestor application libs_secrets         '{"enabled":true}'
post warehouse-ingestor application libs_observability   '{"enabled":true}'
post warehouse-ingestor application unique_db_user       '{"enabled":true}'
post warehouse-ingestor application health_check         '{"enabled":true}'
post warehouse-ingestor application unit_coverage        '{"percentage":87}'
post warehouse-ingestor application integration_coverage '{"percentage":65}'
post warehouse-ingestor application stress_test          '{"error_rate":0.001,"p95_ms":380,"checks_pct":97}'
post warehouse-ingestor reliability sla                  '{"availability_pct":99.95}'
post warehouse-ingestor reliability change_failure_rate  '{"rate_pct":2}'
post warehouse-ingestor reliability mttr                 '{"minutes":40}'
post warehouse-ingestor reliability mttd                 '{"minutes":4}'

# ─────────────────────────────────────────────────────────────
# warehouse-transformer  (processo — estável mas médio)
# ─────────────────────────────────────────────────────────────
section "warehouse-transformer (processo estável, qualidade média)"

post warehouse-transformer security    image_scan           '{"critical":0,"high":2,"medium":4}'
post warehouse-transformer security    secret_scan          '{"found":false}'
post warehouse-transformer security    sast                 '{"critical":0,"high":1,"medium":3}'
post warehouse-transformer application libs_secrets         '{"enabled":true}'
post warehouse-transformer application libs_observability   '{"enabled":false}'
post warehouse-transformer application unique_db_user       '{"enabled":true}'
post warehouse-transformer application unit_coverage        '{"percentage":63}'
post warehouse-transformer application integration_coverage '{"percentage":38}'
post warehouse-transformer reliability sla                  '{"availability_pct":99.3}'
post warehouse-transformer reliability change_failure_rate  '{"rate_pct":9}'
post warehouse-transformer reliability mttr                 '{"minutes":210}'
post warehouse-transformer reliability mttd                 '{"minutes":45}'

# ─────────────────────────────────────────────────────────────
# warehouse-catalog-api  (API com problema de secret_scan)
# ─────────────────────────────────────────────────────────────
section "warehouse-catalog-api (API com falha crítica de segurança)"

post warehouse-catalog-api security    image_scan           '{"critical":0,"high":0,"medium":2}'
post warehouse-catalog-api security    secret_scan          '{"found":true}'   # <-- segredo exposto
post warehouse-catalog-api security    sast                 '{"critical":2,"high":3,"medium":8}'
post warehouse-catalog-api security    dast                 '{"high":3,"medium":6}'
post warehouse-catalog-api application libs_secrets         '{"enabled":false}'
post warehouse-catalog-api application libs_observability   '{"enabled":true}'
post warehouse-catalog-api application unique_db_user       '{"enabled":true}'
post warehouse-catalog-api application health_check         '{"enabled":true}'
post warehouse-catalog-api application unit_coverage        '{"percentage":80}'
post warehouse-catalog-api application integration_coverage '{"percentage":55}'
post warehouse-catalog-api application stress_test          '{"error_rate":0.003,"p95_ms":590,"checks_pct":94}'
post warehouse-catalog-api reliability sla                  '{"availability_pct":99.8}'
post warehouse-catalog-api reliability change_failure_rate  '{"rate_pct":4}'
post warehouse-catalog-api reliability mttr                 '{"minutes":60}'
post warehouse-catalog-api reliability mttd                 '{"minutes":8}'

# ─────────────────────────────────────────────────────────────
# warehouse-exporter  (API sem stress test — interna)
# ─────────────────────────────────────────────────────────────
section "warehouse-exporter (API interna — sem DAST/stress)"

post warehouse-exporter security    image_scan           '{"critical":0,"high":1,"medium":2}'
post warehouse-exporter security    secret_scan          '{"found":false}'
post warehouse-exporter security    sast                 '{"critical":0,"high":1,"medium":3}'
post warehouse-exporter application libs_secrets         '{"enabled":true}'
post warehouse-exporter application libs_observability   '{"enabled":true}'
post warehouse-exporter application unique_db_user       '{"enabled":true}'
post warehouse-exporter application health_check         '{"enabled":true}'
post warehouse-exporter application unit_coverage        '{"percentage":76}'
post warehouse-exporter application integration_coverage '{"percentage":50}'
post warehouse-exporter reliability sla                  '{"availability_pct":99.7}'
post warehouse-exporter reliability change_failure_rate  '{"rate_pct":6}'
post warehouse-exporter reliability mttr                 '{"minutes":120}'
post warehouse-exporter reliability mttd                 '{"minutes":15}'

# ─────────────────────────────────────────────────────────────
# warehouse-scheduler  (processo crítico, confiabilidade ruim)
# ─────────────────────────────────────────────────────────────
section "warehouse-scheduler (processo crítico, SLA ruim)"

post warehouse-scheduler security    image_scan           '{"critical":0,"high":0,"medium":1}'
post warehouse-scheduler security    secret_scan          '{"found":false}'
post warehouse-scheduler security    sast                 '{"critical":0,"high":0,"medium":1}'
post warehouse-scheduler application libs_secrets         '{"enabled":true}'
post warehouse-scheduler application libs_observability   '{"enabled":false}'
post warehouse-scheduler application unique_db_user       '{"enabled":false}'
post warehouse-scheduler application unit_coverage        '{"percentage":55}'
post warehouse-scheduler application integration_coverage '{"percentage":30}'
post warehouse-scheduler reliability sla                  '{"availability_pct":97.2}'  # crítico
post warehouse-scheduler reliability change_failure_rate  '{"rate_pct":18}'            # alto
post warehouse-scheduler reliability mttr                 '{"minutes":1440}'           # 24h
post warehouse-scheduler reliability mttd                 '{"minutes":240}'            # 4h

# ─────────────────────────────────────────────────────────────
# Problemas detectados
# ─────────────────────────────────────────────────────────────
section "Problemas (secrets em infra)"

post_problem() {
  local app=$1 type=$2 severity=$3 count=$4 details=$5
  curl -sf -X POST "$BASE_URL/problem/scan-result" \
    -H "Content-Type: application/json" \
    -d "{\"area\":\"$AREA\",\"team\":\"$TEAM\",\"app\":\"$app\",\"env\":\"$ENV\",\"problem_type\":\"$type\",\"severity\":\"$severity\",\"count\":$count,\"details\":$details,\"slack_channel\":\"#warehouse-alerts\"}" > /dev/null 2>&1
  if [[ "$count" -gt 0 ]]; then
    printf "    ${RED}⚠${NC}  %-30s %-30s count=${RED}%s${NC} [%s]\n" "$app" "$type" "$count" "$severity"
  else
    printf "    ${GREEN}✓${NC} %-30s %-30s ${GREEN}clean${NC}\n" "$app" "$type"
  fi
}

post_problem warehouse-catalog-api   terraform_secret  critical 2 '[{"file":"infra/main.tf","line":42,"match":"aws_secret_access_key"},{"file":"infra/vars.tf","line":18,"match":"db_password"}]'
post_problem warehouse-catalog-api   helm_secret       high     1 '[{"file":"helm/values.yaml","line":77,"match":"token"}]'
post_problem warehouse-scheduler     terraform_secret  high     1 '[{"file":"infra/scheduler.tf","line":31,"match":"api_key"}]'
post_problem warehouse-transformer   helm_secret       low      0 '[]'
post_problem warehouse-ingestor      terraform_secret  critical 0 '[]'
post_problem warehouse-exporter      helm_secret       low      0 '[]'

echo -e "\n${GREEN}${BOLD}warehouse mock concluído!${NC}\n"
