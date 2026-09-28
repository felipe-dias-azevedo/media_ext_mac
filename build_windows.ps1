$ErrorActionPreference = 'Stop'

if ($env:GITHUB_REF_NAME) {
  $VERSION = $env:GITHUB_REF_NAME
} else {
    $VERSION = git tag --sort=-version:refname | Select-Object -First 1
}

$VERSION = $VERSION -replace '^v', ''
$V = $VERSION -split '\.'
$VERSION_INFO = "$($V[0]),$($V[1]),$($V[2]),0"

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
    --name MediaExt `
    --windowed `
    --icon icon.ico `
    --version-file version_info.txt `
    --add-data "icon/icon_borderless_1024.png;icon" `
    --hidden-import=yt_dlp `
    --hidden-import=imageio_ffmpeg `
    src/app.py