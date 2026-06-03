param([string]$studyDir = "C:\Users\Renjith\Desktop\icode (2)\study")

$workflowsDir = "C:\Users\Renjith\Desktop\icode (2)\coursevi\.github\workflows"

Remove-Item -LiteralPath "$workflowsDir\generate-lecture.yml" -Force -ErrorAction SilentlyContinue

function New-WorkflowYaml($exam, $chapters, $displayName) {
  $opts = $chapters | ForEach-Object { "          - `"$($_.Num) - $($_.Name)`"" }
  $optsStr = $opts -join "`n"
  $d = $displayName

@"
name: "$d"
on:
  workflow_dispatch:
    inputs:
      chapter:
        description: 'Chapter'
        required: true
        type: choice
        options:
$optsStr

jobs:
  generate-lecture:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout coursevi
        uses: actions/checkout@v4

      - name: Checkout study content
        uses: actions/checkout@v4
        with:
          repository: renj-arch/dimsred
          path: study
          token: `${{ secrets.GH_PAT }}

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install edge-tts

      - name: Generate animated lecture
        env:
          LLM_PROVIDER: openrouter
          LLM_MODEL: openrouter/free
          LLM_API_KEY: `${{ secrets.OPENROUTER_API_KEY }}
          STUDY_PROJECT: `${{ github.workspace }}/study
        run: |
          CH="`${{ inputs.chapter }}"
          CH_NUM=`$(echo "`$CH" | cut -d' ' -f1)
          echo "CH_NUM=`$CH_NUM" >> `$GITHUB_ENV
          python course_video.py $exam "`$CH_NUM"

      - name: Upload video artifact
        uses: actions/upload-artifact@v4
        with:
          name: animated-lecture-$exam-`${{ inputs.chapter }}
          path: output/*.mp4
          retention-days: 7
"@
}

function Get-ChaptersFromDir($dir) {
  $i = 0
  Get-ChildItem -LiteralPath $dir -Filter "*.html" | Sort-Object Name | ForEach-Object {
    $i++
    $stem = $_.BaseName
    $name = ($stem -replace 'chapter-\d+-', '') -replace '-', ' '
    $name = (Get-Culture).TextInfo.ToTitleCase($name)
    [PSCustomObject]@{ Num = $i; Name = $name }
  }
}

$neetNames = @{
  1="The Living World"; 2="Biological Classification"; 3="Plant Kingdom"
  4="Animal Kingdom"; 5="Morphology of Flowering Plants"; 6="Anatomy of Flowering Plants"
  7="Structural Organization in Animals"; 8="Cell The Unit of Life"; 9="Biomolecules"
  10="Cell Cycle and Cell Division"; 11="Transport in Plants"; 12="Mineral Nutrition"
  13="Photosynthesis in Higher Plants"; 14="Respiration in Plants"; 15="Plant Growth and Development"
  16="Digestion and Absorption"; 17="Breathing and Exchange of Gases"; 18="Body Fluids and Circulation"
  19="Excretory Products and Their Elimination"; 20="Locomotion and Movement"
  21="Neural Control and Coordination"; 22="Chemical Coordination and Integration"
}
$neet = 1..22 | ForEach-Object { [PSCustomObject]@{ Num = $_; Name = $neetNames[$_] } }
[System.IO.File]::WriteAllText("$workflowsDir\generate-neet-lecture.yml",
  (New-WorkflowYaml "neet" $neet "NEET Biology"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "neet done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-upsc-lecture.yml",
  (New-WorkflowYaml "upsc" (Get-ChaptersFromDir "$studyDir\upsc\chapters") "UPSC"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "upsc done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-jee-lecture.yml",
  (New-WorkflowYaml "jee" (Get-ChaptersFromDir "$studyDir\jee\chapters") "JEE"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "jee done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-gate-lecture.yml",
  (New-WorkflowYaml "gate" (Get-ChaptersFromDir "$studyDir\gate\chapters") "GATE"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "gate done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-ssc-gd-lecture.yml",
  (New-WorkflowYaml "ssc-gd" (Get-ChaptersFromDir "$studyDir\ssc-gd\chapters") "SSC-GD"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "ssc-gd done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-cgl-lecture.yml",
  (New-WorkflowYaml "cgl" (Get-ChaptersFromDir "$studyDir\cgl\chapters") "CGL"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "cgl done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-ibps-po-lecture.yml",
  (New-WorkflowYaml "ibps-po" (Get-ChaptersFromDir "$studyDir\ibps-po\chapters") "IBPS PO"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "ibps-po done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-sbi-clerk-lecture.yml",
  (New-WorkflowYaml "sbi-clerk" (Get-ChaptersFromDir "$studyDir\sbi-clerk\chapters") "SBI Clerk"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "sbi-clerk done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-rbi-lecture.yml",
  (New-WorkflowYaml "rbi" (Get-ChaptersFromDir "$studyDir\rbi\chapters") "RBI"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "rbi done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-ctet-lecture.yml",
  (New-WorkflowYaml "ctet" (Get-ChaptersFromDir "$studyDir\ctet\chapters") "CTET"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "ctet done"

[System.IO.File]::WriteAllText("$workflowsDir\generate-agniveer-lecture.yml",
  (New-WorkflowYaml "agniveer" (Get-ChaptersFromDir "$studyDir\agniveer\chapters") "Agniveer"),
  [System.Text.UTF8Encoding]::new($false))
Write-Output "agniveer done"
