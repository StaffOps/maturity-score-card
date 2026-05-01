#!/usr/bin/env bash
# mock.sh — popula a API com dados de teste para todas as áreas/times/apps
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8080}"
ENV="${ENV:-dev}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ─── preflight ─────────────────────────────────────────────────────────────────

echo -e "${BOLD}Verificando API em $BASE_URL ...${NC}"
if ! curl -sf "$BASE_URL/healthz" > /dev/null; then
  echo -e "${RED}API não está respondendo. Suba com: docker compose up --build${NC}"
  exit 1
fi
echo -e "${GREEN}API ok${NC}\n"

# ─── helpers ───────────────────────────────────────────────────────────────────

post_score() {
  local area=$1 team=$2 app=$3 scorecard=$4 metric=$5 raw=$6
  local result score
  result=$(curl -sf -X POST "$BASE_URL/score" \
    -H "Content-Type: application/json" \
    -d "{\"area\":\"$area\",\"team\":\"$team\",\"app\":\"$app\",\"env\":\"$ENV\",\"scorecard\":\"$scorecard\",\"metric\":\"$metric\",\"raw\":$raw}" 2>/dev/null || echo '{"score":0}')
  score=$(echo "$result" | grep -o '"score":[0-9.]*' | cut -d: -f2)
  printf "    ${GREEN}✓${NC} %-15s %-25s score=${CYAN}%-6s${NC}\n" "$scorecard" "$metric" "$score"
}

post_problem() {
  local area=$1 team=$2 app=$3 type=$4 severity=$5 count=$6 channel=$7 details=$8
  curl -sf -X POST "$BASE_URL/problem/scan-result" \
    -H "Content-Type: application/json" \
    -d "{\"area\":\"$area\",\"team\":\"$team\",\"app\":\"$app\",\"env\":\"$ENV\",\"problem_type\":\"$type\",\"severity\":\"$severity\",\"count\":$count,\"details\":$details,\"slack_channel\":\"$channel\"}" > /dev/null 2>&1
  if [[ "$count" -gt 0 ]]; then
    printf "    ${RED}⚠${NC}  %-30s %-25s count=${RED}%-3s${NC} [%s]\n" "$area/$team/$app" "$type" "$count" "$severity"
  else
    printf "    ${GREEN}✓${NC} %-30s %-25s ${GREEN}clean${NC}\n" "$area/$team/$app" "$type"
  fi
}

section() { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}"; }
team_header() { echo -e "\n  ${BOLD}$1 / $2${NC}"; }
app_header() { echo -e "  → ${BOLD}$1${NC} ($2)"; }

# ─── perfis de qualidade (A=excelente B=bom C=médio D=ruim) ───────────────────

vuln_raw() {
  case $1 in
    A) echo '{"critical":0,"high":0,"medium":1}' ;;
    B) echo '{"critical":0,"high":1,"medium":3}' ;;
    C) echo '{"critical":1,"high":2,"medium":5}' ;;
    D) echo '{"critical":2,"high":4,"medium":9}' ;;
  esac
}
dast_raw() {
  case $1 in
    A) echo '{"high":0,"medium":1}' ;;
    B) echo '{"high":1,"medium":2}' ;;
    C) echo '{"high":2,"medium":4}' ;;
    D) echo '{"high":4,"medium":7}' ;;
  esac
}
bool_raw()   { [[ $1 =~ ^[AB]$ ]] && echo '{"enabled":true}'  || echo '{"enabled":false}'; }
secret_raw() { [[ $1 =~ ^[ABC]$ ]] && echo '{"found":false}' || echo '{"found":true}'; }
unit_cov_raw() {
  case $1 in A) echo '{"percentage":88}' ;; B) echo '{"percentage":73}' ;;
             C) echo '{"percentage":52}' ;; D) echo '{"percentage":31}' ;; esac
}
int_cov_raw() {
  case $1 in A) echo '{"percentage":68}' ;; B) echo '{"percentage":45}' ;;
             C) echo '{"percentage":27}' ;; D) echo '{"percentage":11}' ;; esac
}
stress_raw() {
  case $1 in
    A) echo '{"error_rate":0.0005,"p95_ms":310,"checks_pct":98}' ;;
    B) echo '{"error_rate":0.004,"p95_ms":670,"checks_pct":91}' ;;
    C) echo '{"error_rate":0.015,"p95_ms":1250,"checks_pct":74}' ;;
    D) echo '{"error_rate":0.04,"p95_ms":2600,"checks_pct":52}' ;;
  esac
}
sla_raw() {
  case $1 in A) echo '{"availability_pct":99.95}' ;; B) echo '{"availability_pct":99.7}' ;;
             C) echo '{"availability_pct":99.1}' ;;  D) echo '{"availability_pct":97.5}' ;; esac
}
cfr_raw() {
  case $1 in A) echo '{"rate_pct":2}' ;; B) echo '{"rate_pct":7}' ;;
             C) echo '{"rate_pct":12}';; D) echo '{"rate_pct":22}';; esac
}
mttr_raw() {
  case $1 in A) echo '{"minutes":35}';;  B) echo '{"minutes":150}';;
             C) echo '{"minutes":480}';; D) echo '{"minutes":2160}';; esac
}
mttd_raw() {
  case $1 in A) echo '{"minutes":3}';;  B) echo '{"minutes":18}';;
             C) echo '{"minutes":75}';; D) echo '{"minutes":180}';; esac
}

# ─── submitters por tipo de app ────────────────────────────────────────────────
# sl=security-level  al=application-level  rl=reliability-level

# API completa: todos os steps
api_full() {
  local area=$1 team=$2 app=$3 sl=$4 al=$5 rl=$6
  app_header "$app" "api-full sec=$sl app=$al rel=$rl"
  post_score $area $team $app security    image_scan           "$(vuln_raw $sl)"
  post_score $area $team $app security    secret_scan          "$(secret_raw $sl)"
  post_score $area $team $app security    sast                 "$(vuln_raw $sl)"
  post_score $area $team $app security    dast                 "$(dast_raw $sl)"
  post_score $area $team $app application libs_secrets         "$(bool_raw $al)"
  post_score $area $team $app application libs_observability   "$(bool_raw $al)"
  post_score $area $team $app application unique_db_user       "$(bool_raw $al)"
  post_score $area $team $app application health_check         "$(bool_raw $al)"
  post_score $area $team $app application unit_coverage        "$(unit_cov_raw $al)"
  post_score $area $team $app application integration_coverage "$(int_cov_raw $al)"
  post_score $area $team $app application stress_test          "$(stress_raw $al)"
  post_score $area $team $app reliability sla                  "$(sla_raw $rl)"
  post_score $area $team $app reliability change_failure_rate  "$(cfr_raw $rl)"
  post_score $area $team $app reliability mttr                 "$(mttr_raw $rl)"
  post_score $area $team $app reliability mttd                 "$(mttd_raw $rl)"
}

# API sem DAST e sem stress test (ex: API interna sem exposição externa)
api_partial() {
  local area=$1 team=$2 app=$3 sl=$4 al=$5 rl=$6
  app_header "$app" "api-partial sec=$sl app=$al rel=$rl"
  post_score $area $team $app security    image_scan           "$(vuln_raw $sl)"
  post_score $area $team $app security    secret_scan          "$(secret_raw $sl)"
  post_score $area $team $app security    sast                 "$(vuln_raw $sl)"
  post_score $area $team $app application libs_secrets         "$(bool_raw $al)"
  post_score $area $team $app application libs_observability   "$(bool_raw $al)"
  post_score $area $team $app application unique_db_user       "$(bool_raw $al)"
  post_score $area $team $app application health_check         "$(bool_raw $al)"
  post_score $area $team $app application unit_coverage        "$(unit_cov_raw $al)"
  post_score $area $team $app application integration_coverage "$(int_cov_raw $al)"
  post_score $area $team $app reliability sla                  "$(sla_raw $rl)"
  post_score $area $team $app reliability change_failure_rate  "$(cfr_raw $rl)"
  post_score $area $team $app reliability mttr                 "$(mttr_raw $rl)"
  post_score $area $team $app reliability mttd                 "$(mttd_raw $rl)"
}

# Processo: sem DAST, sem stress, sem health_check
process() {
  local area=$1 team=$2 app=$3 sl=$4 al=$5 rl=$6
  app_header "$app" "process sec=$sl app=$al rel=$rl"
  post_score $area $team $app security    image_scan           "$(vuln_raw $sl)"
  post_score $area $team $app security    secret_scan          "$(secret_raw $sl)"
  post_score $area $team $app security    sast                 "$(vuln_raw $sl)"
  post_score $area $team $app application libs_secrets         "$(bool_raw $al)"
  post_score $area $team $app application libs_observability   "$(bool_raw $al)"
  post_score $area $team $app application unique_db_user       "$(bool_raw $al)"
  post_score $area $team $app application unit_coverage        "$(unit_cov_raw $al)"
  post_score $area $team $app application integration_coverage "$(int_cov_raw $al)"
  post_score $area $team $app reliability sla                  "$(sla_raw $rl)"
  post_score $area $team $app reliability change_failure_rate  "$(cfr_raw $rl)"
  post_score $area $team $app reliability mttr                 "$(mttr_raw $rl)"
  post_score $area $team $app reliability mttd                 "$(mttd_raw $rl)"
}

# ══════════════════════════════════════════════════════════════════════════════
# SCORES
# ══════════════════════════════════════════════════════════════════════════════

# ─── FINANCIAL ────────────────────────────────────────────────────────────────
section "FINANCIAL"

team_header financial payments
api_full    financial payments payments-gateway         A A A
api_full    financial payments payments-processor       A B A
api_full    financial payments payments-reconciliation  B A B
api_partial financial payments payments-pix             B B B
api_partial financial payments payments-card            C B C
process     financial payments payments-scheduler       A A A
process     financial payments payments-notifier        B B B
process     financial payments payments-reporter        A B A

team_header financial billing
api_full    financial billing billing-api               B B B
api_full    financial billing billing-invoice           A A A
api_full    financial billing billing-subscription      B A B
api_partial financial billing billing-report            C C B
api_partial financial billing billing-credit            B B C
process     financial billing billing-job               B B B
process     financial billing billing-exporter          A A A
process     financial billing billing-archiver          C B B

team_header financial treasury
api_full    financial treasury treasury-api             A A A
api_full    financial treasury treasury-fx              B B B
api_partial financial treasury treasury-cashflow        C B C
api_partial financial treasury treasury-hedge           B C B
api_partial financial treasury treasury-report          D C D
process     financial treasury treasury-batch           B B B
process     financial treasury treasury-reconciler      C C C
process     financial treasury treasury-monitor         A B A

# ─── OPERATIONS ───────────────────────────────────────────────────────────────
section "OPERATIONS"

team_header operations logistics
api_full    operations logistics logistics-api          B B B
api_full    operations logistics logistics-tracking     A A A
api_full    operations logistics logistics-routing      B A B
api_partial operations logistics logistics-fleet        C B C
api_partial operations logistics logistics-hub          B B B
process     operations logistics logistics-sync         C C B
process     operations logistics logistics-notifier     B B B
process     operations logistics logistics-archiver     A A A

team_header operations warehouse
api_full    operations warehouse warehouse-api          C B C
api_full    operations warehouse warehouse-inventory    B B B
api_full    operations warehouse warehouse-picking      D C D
api_partial operations warehouse warehouse-receiving    C C C
api_partial operations warehouse warehouse-shipping     B C B
process     operations warehouse warehouse-sync         D D D
process     operations warehouse warehouse-reporter     C C C
process     operations warehouse warehouse-cleaner      B B B

team_header operations delivery
api_full    operations delivery delivery-api            A A A
api_full    operations delivery delivery-tracking       A B A
api_full    operations delivery delivery-dispatch       B A B
api_partial operations delivery delivery-sla            B B B
api_partial operations delivery delivery-proof          C B C
process     operations delivery delivery-sync           A A A
process     operations delivery delivery-notifier       B B A
process     operations delivery delivery-monitor        A A A

# ─── TECHNOLOGY ───────────────────────────────────────────────────────────────
section "TECHNOLOGY"

team_header technology platform
api_full    technology platform platform-api            A A A
api_full    technology platform platform-auth           A A A
api_full    technology platform platform-gateway        A A A
api_partial technology platform platform-config         B A B
api_partial technology platform platform-feature-flags B B B
process     technology platform platform-deployer       A A A
process     technology platform platform-monitor        A A A
process     technology platform platform-backup         B A B

team_header technology infra
api_full    technology infra infra-api                  A A A
api_full    technology infra infra-dns                  B A B
api_partial technology infra infra-lb                   B B A
api_partial technology infra infra-cert                 A A A
api_partial technology infra infra-secrets              A A A
process     technology infra infra-rotation             A A A
process     technology infra infra-scanner              A B A
process     technology infra infra-reporter             B B B

team_header technology security-team
api_full    technology security-team sec-api            A A A
api_full    technology security-team sec-vault          A A A
api_full    technology security-team sec-sso            A A A
api_partial technology security-team sec-audit          A A A
api_partial technology security-team sec-compliance     B A B
process     technology security-team sec-scanner        A A A
process     technology security-team sec-reporter       A A A
process     technology security-team sec-archiver       A B A

# ─── COMMERCE ─────────────────────────────────────────────────────────────────
section "COMMERCE"

team_header commerce catalog
api_full    commerce catalog catalog-api                B B B
api_full    commerce catalog catalog-search             A B A
api_full    commerce catalog catalog-pricing            C B C
api_partial commerce catalog catalog-inventory          B C B
api_partial commerce catalog catalog-media              D C D
process     commerce catalog catalog-indexer            C C B
process     commerce catalog catalog-exporter           B B B
process     commerce catalog catalog-cleaner            C D C

team_header commerce orders
api_full    commerce orders orders-api                  B A B
api_full    commerce orders orders-checkout             A A A
api_full    commerce orders orders-fulfillment          B B B
api_partial commerce orders orders-returns              C B C
api_partial commerce orders orders-notifications        B B B
process     commerce orders orders-processor            B B B
process     commerce orders orders-reporter             C B C
process     commerce orders orders-archiver             B C B

team_header commerce checkout
api_full    commerce checkout checkout-api              A A A
api_full    commerce checkout checkout-cart             B A B
api_full    commerce checkout checkout-payment          A A A
api_partial commerce checkout checkout-coupon           B B B
api_partial commerce checkout checkout-shipping         C B B
process     commerce checkout checkout-validator        B B A
process     commerce checkout checkout-notifier         A A A
process     commerce checkout checkout-monitor          B A B

# ─── CUSTOMER ─────────────────────────────────────────────────────────────────
section "CUSTOMER"

team_header customer support
api_full    customer support support-api                C C B
api_full    customer support support-tickets            B C B
api_full    customer support support-chat               D D C
api_partial customer support support-kb                 C C C
api_partial customer support support-escalation         D C D
process     customer support support-reporter           C D C
process     customer support support-notifier           D D D
process     customer support support-archiver           C C C

team_header customer loyalty
api_full    customer loyalty loyalty-api                B B B
api_full    customer loyalty loyalty-points             A B A
api_full    customer loyalty loyalty-rewards            B A B
api_partial customer loyalty loyalty-tiers              B B B
api_partial customer loyalty loyalty-referral           C B C
process     customer loyalty loyalty-calculator         B B A
process     customer loyalty loyalty-notifier           A B A
process     customer loyalty loyalty-exporter           B C B

team_header customer onboarding
api_full    customer onboarding onboarding-api          B B B
api_full    customer onboarding onboarding-kyc          A A A
api_full    customer onboarding onboarding-docs         B B B
api_partial customer onboarding onboarding-verification C B B
api_partial customer onboarding onboarding-welcome      B C B
process     customer onboarding onboarding-processor    B B B
process     customer onboarding onboarding-notifier     B A B
process     customer onboarding onboarding-archiver     C B C

# ══════════════════════════════════════════════════════════════════════════════
# PROBLEMS — secrets em terraform e helmcharts
# ══════════════════════════════════════════════════════════════════════════════
section "PROBLEMS — Scans de IaC"

echo -e "\n  ${BOLD}Terraform${NC}"
# Críticos — precisam de ação imediata
post_problem financial   treasury    treasury-batch       secret_in_terraform critical 3 "#treasury-security"  '[{"file":"infra/rds.tf","line":18,"description":"DB_PASSWORD em texto plano"},{"file":"infra/s3.tf","line":42,"description":"AWS_SECRET_KEY hardcoded"},{"file":"infra/lambda.tf","line":7,"description":"API_TOKEN exposto"}]'
post_problem operations  warehouse   warehouse-sync       secret_in_terraform critical 2 "#warehouse-alerts"   '[{"file":"terraform/main.tf","line":31,"description":"REDIS_PASSWORD hardcoded"},{"file":"terraform/rds.tf","line":55,"description":"SECRET_KEY exposto"}]'
post_problem customer    support     support-notifier     secret_in_terraform critical 1 "#support-security"   '[{"file":"infra/sns.tf","line":12,"description":"AWS_SECRET_ACCESS_KEY exposto"}]'
post_problem commerce    catalog     catalog-media        secret_in_terraform high     2 "#catalog-alerts"     '[{"file":"tf/cdn.tf","line":9,"description":"CDN_API_KEY hardcoded"},{"file":"tf/storage.tf","line":23,"description":"GCS_KEY_JSON exposto"}]'

# High
post_problem customer    support     support-chat         secret_in_terraform high     1 "#support-security"   '[{"file":"infra/eks.tf","line":77,"description":"DATADOG_API_KEY exposto"}]'
post_problem operations  warehouse   warehouse-cleaner    secret_in_terraform high     1 "#warehouse-alerts"   '[{"file":"terraform/sqs.tf","line":14,"description":"QUEUE_SECRET hardcoded"}]'

# Scans limpos
post_problem financial   payments    payments-scheduler   secret_in_terraform critical 0 "#payments-security"  '[]'
post_problem financial   billing     billing-job          secret_in_terraform critical 0 "#billing-security"   '[]'
post_problem technology  platform    platform-deployer    secret_in_terraform critical 0 "#platform-security"  '[]'
post_problem technology  infra       infra-rotation       secret_in_terraform critical 0 "#infra-security"     '[]'
post_problem commerce    orders      orders-processor     secret_in_terraform critical 0 "#orders-security"    '[]'
post_problem customer    loyalty     loyalty-calculator   secret_in_terraform critical 0 "#loyalty-security"   '[]'

echo -e "\n  ${BOLD}HelmCharts${NC}"
# Críticos
post_problem financial   treasury    treasury-api         secret_in_helmchart critical 2 "#treasury-security"  '[{"file":"helm/values.yaml","line":45,"description":"database.password em plaintext"},{"file":"helm/secrets.yaml","line":12,"description":"jwt.secret exposto"}]'
post_problem customer    support     support-tickets      secret_in_helmchart high     1 "#support-security"   '[{"file":"chart/values.yaml","line":89,"description":"smtp.password hardcoded"}]'
post_problem operations  warehouse   warehouse-inventory  secret_in_helmchart high     1 "#warehouse-alerts"   '[{"file":"helm/values-prod.yaml","line":33,"description":"mongodb.uri com credenciais"}]'
post_problem commerce    catalog     catalog-cleaner      secret_in_helmchart high     2 "#catalog-alerts"     '[{"file":"helm/values.yaml","line":21,"description":"elasticsearch.password exposto"},{"file":"helm/secrets.yaml","line":8,"description":"S3_SECRET_KEY hardcoded"}]'

# Medium
post_problem customer    onboarding  onboarding-processor secret_in_helmchart medium   1 "#onboarding-alerts"  '[{"file":"chart/values.yaml","line":67,"description":"redis.auth com valor default"}]'

# Scans limpos
post_problem financial   payments    payments-gateway     secret_in_helmchart critical 0 "#payments-security"  '[]'
post_problem financial   billing     billing-api          secret_in_helmchart critical 0 "#billing-security"   '[]'
post_problem technology  platform    platform-api         secret_in_helmchart critical 0 "#platform-security"  '[]'
post_problem technology  security-team sec-vault          secret_in_helmchart critical 0 "#security-alerts"    '[]'
post_problem commerce    checkout    checkout-api         secret_in_helmchart critical 0 "#checkout-security"  '[]'
post_problem customer    loyalty     loyalty-api          secret_in_helmchart critical 0 "#loyalty-security"   '[]'

# ─── resumo ───────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${GREEN}━━━ Concluído ━━━${NC}"
echo -e "  Áreas:    5 (financial, operations, technology, commerce, customer)"
echo -e "  Times:    15"
echo -e "  Apps:     120 (75 APIs + 45 processos)"
echo -e "  Métricas: ~1560 pontuações enviadas"
echo -e "  Problemas: 7 críticos / 5 high / 1 medium + 12 scans limpos\n"
echo -e "  ${BOLD}Grafana:${NC} http://localhost:3000/d/maturity-score-v1"
echo -e "  ${BOLD}Prometheus:${NC} http://localhost:9090"
