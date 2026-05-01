#!/usr/bin/env bash
# mock_problems.sh — simula rodada geral de scans: resolve ativos, abre novos
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

echo -e "${BOLD}Verificando API em $BASE_URL ...${NC}"
if ! curl -sf "$BASE_URL/healthz" > /dev/null; then
  echo -e "${RED}API não está respondendo.${NC}"; exit 1
fi
echo -e "${GREEN}API ok${NC}\n"

problem() {
  local area=$1 team=$2 app=$3 env=$4 type=$5 severity=$6 count=$7 details=$8 channel=$9
  curl -sf -X POST "$BASE_URL/problem/scan-result" \
    -H "Content-Type: application/json" \
    -d "{\"area\":\"$area\",\"team\":\"$team\",\"app\":\"$app\",\"env\":\"$env\",\"problem_type\":\"$type\",\"severity\":\"$severity\",\"count\":$count,\"details\":$details,\"slack_channel\":\"$channel\"}" > /dev/null 2>&1
  if [[ "$count" -gt 0 ]]; then
    printf "  ${RED}⚠${NC}  %-12s %-15s %-30s %-25s count=${RED}%s${NC} [%s]\n" "$area" "$team" "$app" "$type" "$count" "$severity"
  else
    printf "  ${GREEN}✓${NC}  %-12s %-15s %-30s %-25s ${GREEN}resolvido${NC}\n" "$area" "$team" "$app" "$type"
  fi
}

section() { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}"; }

# ─────────────────────────────────────────────────────────────
# RESOLVIDOS — warehouse corrigiu os secrets
# ─────────────────────────────────────────────────────────────
section "Resolvidos — warehouse corrigiu após alerta"

problem data warehouse warehouse-catalog-api prod terraform_secret critical 0 '[]' '#warehouse-alerts'
problem data warehouse warehouse-catalog-api prod helm_secret      high     0 '[]' '#warehouse-alerts'
problem data warehouse warehouse-scheduler   prod terraform_secret high     0 '[]' '#warehouse-alerts'

# ─────────────────────────────────────────────────────────────
# NOVOS — financial/payments: secret em helmchart pós-deploy
# ─────────────────────────────────────────────────────────────
section "Novos — financial/payments (secret introduzido em deploy)"

problem financial payments payments-gateway prod helm_secret      critical 1 \
  '[{"file":"helm/values.yaml","line":31,"match":"stripe_secret_key"}]' \
  '#payments-security'

problem financial payments payments-api      prod terraform_secret high     2 \
  '[{"file":"infra/rds.tf","line":14,"match":"db_password"},{"file":"infra/rds.tf","line":22,"match":"db_username"}]' \
  '#payments-security'

problem financial billing  billing-api       prod helm_secret      high     1 \
  '[{"file":"helm/secrets.yaml","line":8,"match":"api_token"}]' \
  '#billing-alerts'

# ─────────────────────────────────────────────────────────────
# NOVOS — technology/platform: secret em terraform de infra
# ─────────────────────────────────────────────────────────────
section "Novos — technology/platform (secret em módulo compartilhado)"

problem technology platform platform-deployer prod terraform_secret critical 3 \
  '[{"file":"modules/iam/main.tf","line":5,"match":"aws_access_key_id"},{"file":"modules/iam/main.tf","line":6,"match":"aws_secret_access_key"},{"file":"modules/s3/vars.tf","line":19,"match":"bucket_key"}]' \
  '#platform-security'

problem technology infra    infra-rotation    prod terraform_secret high     1 \
  '[{"file":"infra/rotation.tf","line":42,"match":"rotation_token"}]' \
  '#infra-alerts'

# ─────────────────────────────────────────────────────────────
# LIMPOS — commerce já está ok nessa rodada
# ─────────────────────────────────────────────────────────────
section "Limpos — commerce/checkout sem achados"

problem commerce checkout checkout-api  prod terraform_secret critical 0 '[]' '#checkout-security'
problem commerce checkout checkout-api  prod helm_secret      high     0 '[]' '#checkout-security'
problem commerce orders   orders-api    prod terraform_secret critical 0 '[]' '#orders-alerts'

# ─────────────────────────────────────────────────────────────
# NOVOS — customer/loyalty: helm com credencial de parceiro
# ─────────────────────────────────────────────────────────────
section "Novos — customer/loyalty (credencial de parceiro exposta)"

problem customer loyalty loyalty-api prod helm_secret high 1 \
  '[{"file":"helm/partner-config.yaml","line":17,"match":"partner_api_key"}]' \
  '#loyalty-alerts'

echo -e "\n${GREEN}${BOLD}mock_problems concluído!${NC}\n"
echo -e "${BOLD}Resumo esperado no banco:${NC}"
echo -e "  ${GREEN}Resolvidos${NC}: warehouse-catalog-api (2x), warehouse-scheduler"
echo -e "  ${RED}Abertos${NC}:    payments-gateway, payments-api, billing-api, platform-deployer, infra-rotation, loyalty-api"
