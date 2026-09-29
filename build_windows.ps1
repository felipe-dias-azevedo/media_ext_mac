$ErrorActionPreference = 'Stop'

if ($env:GITHUB_REF_NAME) {
  $VERSION = $env:GITHUB_REF_NAME
} else {
    $VERSION = git tag --sort=-version:refname | Select-Object -First 1
}

$VERSION = $VERSION -replace '^v', ''
if ($VERSION -match '^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$') {
  $VERSION_INFO = "$($Matches[1]),$($Matches[2]),$($Matches[3]),0"
} else {
  Write-Warning "Ref '$VERSION' is not a release version; using 0.0.0 for this build."
  $VERSION = '0.0.0'
  $VERSION_INFO = '0,0,0,0'
}

@"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($VERSION_INFO),
    prodvers=($VERSION_INFO),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [
          StringStruct(u'FileVersion', u'$VERSION'),
          StringStruct(u'ProductVersion', u'$VERSION'),
          StringStruct(u'ProductName', u'MediaExt')
        ]
      )
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"@ | Set-Content version_info.txt

python -m PyInstaller `
    --onefile `
    --name MediaExt `
    --windowed `
    --icon icon.ico `
    --version-file version_info.txt `
    --add-data "icon/icon_borderless_1024.png;icon" `
    --hidden-import=yt_dlp `
    --hidden-import=imageio_ffmpeg `
    src/app.py