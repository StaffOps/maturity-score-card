# Pipeline curl examples

All examples use environment variables for context. Set them at the pipeline level:

```bash
MATURITY_API="https://maturity-api.internal"
AREA="financial"
TEAM="payments"
APP="payments-api"
ENV="prod"
```

---

## Scorecard: security

### image_scan

Output from container image scanners (Trivy, Grype, Snyk).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"security\",
    \"metric\": \"image_scan\",
    \"raw\": {
      \"critical\": 0,
      \"high\": 1,
      \"medium\": 3
    }
  }"
```

Scoring: `100 - (critical × 25) - (high × 10) - (medium × 3)`, minimum 0.

---

### secret_scan

Output from secret scanners (Gitleaks, TruffleHog, detect-secrets).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"security\",
    \"metric\": \"secret_scan\",
    \"raw\": {
      \"found\": false
    }
  }"
```

Scoring: `100` if no secret found, `0` otherwise.

---

### sast

Output from static analysis tools (Semgrep, SonarQube, CodeQL).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"security\",
    \"metric\": \"sast\",
    \"raw\": {
      \"critical\": 0,
      \"high\": 2,
      \"medium\": 5
    }
  }"
```

Scoring: same formula as `image_scan`.

---

### dast

Output from dynamic analysis tools (OWASP ZAP, Burp Suite).  
Skip this metric for internal services with no external exposure — the weight redistributes automatically.

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"security\",
    \"metric\": \"dast\",
    \"raw\": {
      \"high\": 0,
      \"medium\": 1
    }
  }"
```

Scoring: `100 - (high × 20) - (medium × 5)`, minimum 0.

---

## Scorecard: application

### libs_secrets

Whether the app uses a secret manager (Vault, AWS Secrets Manager) instead of hardcoded env vars.

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"application\",
    \"metric\": \"libs_secrets\",
    \"raw\": {
      \"enabled\": true
    }
  }"
```

Scoring: `100` if enabled, `0` otherwise.

---

### libs_observability

Whether the app has observability instrumentation (OpenTelemetry, structured logging, metrics).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"application\",
    \"metric\": \"libs_observability\",
    \"raw\": {
      \"enabled\": true
    }
  }"
```

Scoring: `100` if enabled, `0` otherwise.

---

### unique_db_user

Whether the app uses a dedicated database user (not shared with other services).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"application\",
    \"metric\": \"unique_db_user\",
    \"raw\": {
      \"enabled\": true
    }
  }"
```

Scoring: `100` if enabled, `0` otherwise.

---

### health_check

Whether the app exposes a health check endpoint.  
Skip for background processes with no HTTP interface.

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"application\",
    \"metric\": \"health_check\",
    \"raw\": {
      \"enabled\": true
    }
  }"
```

Scoring: `100` if enabled, `0` otherwise.

---

### unit_coverage

Unit test coverage percentage.

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"application\",
    \"metric\": \"unit_coverage\",
    \"raw\": {
      \"percentage\": 82
    }
  }"
```

Scoring: `100` if ≥ 80%, `50–100` if 60–80%, `10–50` if 40–60%, `0` below 40%.

---

### integration_coverage

Integration test coverage percentage.

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"application\",
    \"metric\": \"integration_coverage\",
    \"raw\": {
      \"percentage\": 65
    }
  }"
```

Scoring: `100` if ≥ 60%, `50–100` if 40–60%, `10–50` if 20–40%, `0` below 20%.

---

### stress_test

Output from load testing tools (k6, Gatling, Locust).  
Skip for processes that are not request-serving.

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"application\",
    \"metric\": \"stress_test\",
    \"raw\": {
      \"error_rate\": 0.002,
      \"p95_ms\": 420,
      \"checks_pct\": 97
    }
  }"
```

Scoring: up to 40 pts for error rate, 35 pts for p95 latency, 25 pts for checks passing.

---

## Scorecard: reliability

### sla

Observed availability over the period (from your monitoring tool).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"reliability\",
    \"metric\": \"sla\",
    \"raw\": {
      \"availability_pct\": 99.85
    }
  }"
```

Scoring: `100` if ≥ 99.5%, `75` if ≥ 99%, `50` if ≥ 98%, linear below 98%.

---

### change_failure_rate

Percentage of deployments that caused an incident or required a rollback.

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"reliability\",
    \"metric\": \"change_failure_rate\",
    \"raw\": {
      \"rate_pct\": 3
    }
  }"
```

Scoring: `100` if < 5%, `75` if < 10%, `50` if < 15%, `25` otherwise.

---

### mttr

Mean time to recovery in minutes (from incident open to resolution).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"reliability\",
    \"metric\": \"mttr\",
    \"raw\": {
      \"minutes\": 45
    }
  }"
```

Scoring: `100` if < 60 min, `75` if < 4 h, `50` if < 24 h, `25` otherwise.

---

### mttd

Mean time to detection in minutes (from incident start to first alert).

```bash
curl -sf -X POST "$MATURITY_API/score" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"$APP\",
    \"env\": \"$ENV\",
    \"scorecard\": \"reliability\",
    \"metric\": \"mttd\",
    \"raw\": {
      \"minutes\": 4
    }
  }"
```

Scoring: `100` if < 5 min, `75` if < 30 min, `50` if < 2 h, `25` otherwise.

---

## Problems: infrastructure secrets

### terraform_secret

Report secrets found in Terraform files. Set `count: 0` to mark as resolved.

```bash
curl -sf -X POST "$MATURITY_API/problem/scan-result" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"${APP}-infra\",
    \"env\": \"$ENV\",
    \"problem_type\": \"terraform_secret\",
    \"severity\": \"critical\",
    \"count\": 1,
    \"details\": [
      {
        \"file\": \"infra/main.tf\",
        \"line\": 42,
        \"description\": \"AWS_SECRET_ACCESS_KEY\"
      }
    ],
    \"slack_channel\": \"#$TEAM-security\"
  }"
```

### helm_secret

Report secrets found in Helm chart files.

```bash
curl -sf -X POST "$MATURITY_API/problem/scan-result" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"${APP}-infra\",
    \"env\": \"$ENV\",
    \"problem_type\": \"helm_secret\",
    \"severity\": \"high\",
    \"count\": 1,
    \"details\": [
      {
        \"file\": \"helm/values.yaml\",
        \"line\": 17,
        \"description\": \"DB_PASSWORD\"
      }
    ],
    \"slack_channel\": \"#$TEAM-security\"
  }"
```

### Resolving a problem

When the scanner finds no issues, send `count: 0`. The problem is cleared from the dashboard immediately.

```bash
curl -sf -X POST "$MATURITY_API/problem/scan-result" \
  -H "Content-Type: application/json" \
  -d "{
    \"area\": \"$AREA\",
    \"team\": \"$TEAM\",
    \"app\": \"${APP}-infra\",
    \"env\": \"$ENV\",
    \"problem_type\": \"terraform_secret\",
    \"severity\": \"critical\",
    \"count\": 0,
    \"details\": [],
    \"slack_channel\": \"#$TEAM-security\"
  }"
```

---

## Partial evaluation

Not all apps run all metrics. Simply omit the metrics that don't apply — the scorecard weight redistributes automatically among the metrics that did run.

**Example:** an internal background process (no HTTP, no DAST, no stress test, no health check):

```bash
for metric in image_scan secret_scan sast; do
  curl -sf -X POST "$MATURITY_API/score" \
    -H "Content-Type: application/json" \
    -d "{\"area\":\"$AREA\",\"team\":\"$TEAM\",\"app\":\"$APP\",\"env\":\"$ENV\",\"scorecard\":\"security\",\"metric\":\"$metric\",\"raw\":{\"critical\":0,\"high\":0,\"medium\":1}}"
done
```

---

## GitHub Actions snippet

```yaml
- name: Submit image scan score
  env:
    MATURITY_API: ${{ secrets.MATURITY_API_URL }}
  run: |
    curl -sf -X POST "$MATURITY_API/score" \
      -H "Content-Type: application/json" \
      -d "{
        \"area\": \"financial\",
        \"team\": \"payments\",
        \"app\": \"${{ github.event.repository.name }}\",
        \"env\": \"prod\",
        \"scorecard\": \"security\",
        \"metric\": \"image_scan\",
        \"raw\": {\"critical\": 0, \"high\": 0, \"medium\": 2},
        \"pipeline_id\": \"${{ github.run_id }}\"
      }"
```

## GitLab CI snippet

```yaml
submit-maturity-score:
  stage: report
  script:
    - |
      curl -sf -X POST "$MATURITY_API_URL/score" \
        -H "Content-Type: application/json" \
        -d "{
          \"area\": \"financial\",
          \"team\": \"payments\",
          \"app\": \"$CI_PROJECT_NAME\",
          \"env\": \"prod\",
          \"scorecard\": \"security\",
          \"metric\": \"image_scan\",
          \"raw\": {\"critical\": 0, \"high\": 0, \"medium\": 2},
          \"pipeline_id\": \"$CI_PIPELINE_ID\"
        }"
```
