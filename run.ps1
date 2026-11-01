[CmdletBinding()]
param(
    [switch]$SkipNotebook
)
$ErrorActionPreference = 'Stop'

# Configuration — adjust these paths or set matching environment variables.
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { 'py' }
$VenvDir = if ($env:VENV_DIR) { $env:VENV_DIR } else { Join-Path $ProjectDir '.venv' }
$NotebookPath = if ($env:NOTEBOOK_PATH) { $env:NOTEBOOK_PATH } else { Join-Path $ProjectDir 'notebook\AI_Related_State_Policy_Activity_Pipeline.ipynb' }
$ExecutedDir = if ($env:EXECUTED_DIR) { $env:EXECUTED_DIR } else { Join-Path $ProjectDir 'notebook\executed' }
$OutputDir = if ($env:STATE_NEWS_OUTPUT_DIR) { $env:STATE_NEWS_OUTPUT_DIR } else { Join-Path $ProjectDir 'state_news_output' }
$OutputCsv = if ($env:OUTPUT_CSV_PATH) { $env:OUTPUT_CSV_PATH } else { Join-Path $OutputDir 'ai_policy_activity_candidates.csv' }
$DashboardCsv = if ($env:DASHBOARD_CSV_PATH) { $env:DASHBOARD_CSV_PATH } else { Join-Path $ProjectDir 'data\ai_policy_activity_candidates.csv' }
$Port = if ($env:PORT) { $env:PORT } else { '8501' }

function Write-Log([string]$Message) {
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

try {
    if (-not (Get-Command $PythonBin -ErrorAction SilentlyContinue)) {
        throw "Python command '$PythonBin' was not found. Install Python 3.10+ or set PYTHON_BIN."
    }

    if (-not (Test-Path $VenvDir)) {
        Write-Log "Creating virtual environment: $VenvDir"
        if ($PythonBin -eq 'py'){ & py -3 -m venv $VenvDir }
        else { & $PythonBin -m venv $VenvDir }
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment.' }
}

    $VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
    if (-not (Test-Path $VenvPython)) { throw "Virtual environment Python not found: $VenvPython" }
    Write-Log 'Installing project and notebook dependencies'
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
    & $VenvPython -m pip install -r (Join-Path $ProjectDir 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }

    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectDir 'data'), $ExecutedDir, $OutputDir | Out-Null

    if (-not $SkipNotebook) {
        if (-not (Test-Path $NotebookPath)) { throw "Notebook not found: $NotebookPath" }
        $env:STATE_NEWS_OUTPUT_DIR = $OutputDir
        Write-Log "Executing notebook: $NotebookPath"
        & $VenvPython -m jupyter nbconvert --to notebook --execute $NotebookPath `
            --output 'executed_ai_policy_pipeline.ipynb' --output-dir $ExecutedDir `
            --ExecutePreprocessor.timeout=1800 --ExecutePreprocessor.kernel_name=python3
        if ($LASTEXITCODE -ne 0) { throw 'Notebook execution failed. Review the nbconvert error above.' }
        $NotebookCsv = Join-Path $OutputDir 'ai_policy_activity_candidates.csv'
        if (-not (Test-Path $NotebookCsv)) { throw "Expected notebook output was not created: $NotebookCsv" }
        if ($OutputCsv -ne $NotebookCsv) {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputCsv) | Out-Null
            Copy-Item -Force $NotebookCsv $OutputCsv
        }
        $SourceCsv = $OutputCsv
    }
    else {
        Write-Log 'Notebook execution skipped. Reusing an existing candidate CSV.'
        if (Test-Path $OutputCsv) { $SourceCsv = $OutputCsv }
        elseif (Test-Path $DashboardCsv) { $SourceCsv = $DashboardCsv }
        else { throw 'No CSV found. Set OUTPUT_CSV_PATH or add data\ai_policy_activity_candidates.csv.' }
    }

    & $VenvPython (Join-Path $ProjectDir 'scripts\validate_and_copy.py') --input $SourceCsv --output $DashboardCsv
    if ($LASTEXITCODE -ne 0) { throw 'Candidate CSV validation/copy failed.' }

    $env:DASHBOARD_CSV_PATH = $DashboardCsv
    Write-Log "Starting dashboard at http://localhost:$Port"
    & $VenvPython -m streamlit run (Join-Path $ProjectDir 'dashboard.py') --server.port $Port --server.address 127.0.0.1
    if ($LASTEXITCODE -ne 0) { throw 'Streamlit exited with an error.' }
}
catch {
    Write-Error $_
    exit 1
}
