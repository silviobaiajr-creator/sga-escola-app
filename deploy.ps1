# ============================================================
# SGA-H — Deploy automático no Google Cloud Run
# Como usar: abra o PowerShell na pasta do projeto e rode:
#   .\deploy.ps1
# ============================================================

$PROJECT_ID = "escola-sga"
$SERVICE_NAME = "sga-h-api"
$REGION = "us-central1"
# DATABASE_URL do Supabase (já preenchida)
$DB_URL = "postgresql://postgres.zjsiznfbswlziuffyosi:3ZreY%2Fq6%40V%3Fi%40a9@aws-1-sa-east-1.pooler.supabase.com:5432/postgres"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   SGA-H — Deploy para o Cloud Run" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Verificar autenticação ───────────────────────────────
Write-Host "1/5  Verificando login no Google Cloud..." -ForegroundColor Yellow
$account = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if (-not $account) {
    Write-Host "     Abrindo login..." -ForegroundColor Red
    gcloud auth login
}
Write-Host "     Conta: $account" -ForegroundColor Green

# ── 2. Definir projeto ─────────────────────────────────────
Write-Host ""
Write-Host "2/5  Selecionando projeto: $PROJECT_ID" -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
Write-Host "     OK!" -ForegroundColor Green

# ── 3. Ativar APIs necessárias ─────────────────────────────
Write-Host ""
Write-Host "3/5  Ativando APIs (Cloud Run + Artifact Registry)..." -ForegroundColor Yellow
gcloud services enable `
    run.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com `
    --quiet
Write-Host "     OK!" -ForegroundColor Green

# ── 4. Deploy do backend ────────────────────────────────────
Write-Host ""
Write-Host "4/5  Fazendo deploy no Cloud Run..." -ForegroundColor Yellow
Write-Host "     (Isso pode levar 3-5 minutos na primeira vez)" -ForegroundColor Gray

gcloud run deploy $SERVICE_NAME `
    --source . `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --min-instances 0 `
    --max-instances 3 `
    --set-env-vars "DATABASE_URL=$DB_URL" `
    --quiet

# ── 5. Permissão Vertex AI ─────────────────────────────────
Write-Host ""
Write-Host "5/5  Configurando permissão do Vertex AI..." -ForegroundColor Yellow

# Pega o número do projeto
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
$SA = "$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SA" `
    --role="roles/aiplatform.user" `
    --quiet | Out-Null

Write-Host "     Service Account: $SA" -ForegroundColor Green
Write-Host "     Permissao: roles/aiplatform.user" -ForegroundColor Green

# ── Resultado final ────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   DEPLOY CONCLUIDO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
    --region $REGION `
    --format="value(status.url)"

Write-Host ""
Write-Host "   URL do Backend:" -ForegroundColor Cyan
Write-Host "   $SERVICE_URL" -ForegroundColor White
Write-Host ""
Write-Host "   Teste rapido:" -ForegroundColor Cyan
Write-Host "   $SERVICE_URL/health" -ForegroundColor White
Write-Host "   $SERVICE_URL/docs   (Swagger UI)" -ForegroundColor White
Write-Host ""
Write-Host "   Proximos passos:" -ForegroundColor Yellow
Write-Host "   Copie a URL acima e configure no Vercel como:" -ForegroundColor White
Write-Host "   NEXT_PUBLIC_API_URL = $SERVICE_URL" -ForegroundColor White
Write-Host ""
