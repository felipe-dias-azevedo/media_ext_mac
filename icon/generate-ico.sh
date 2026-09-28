/Applications/Inkscape.app/Contents/MacOS/inkscape -w 16 -h 16 icon.svg -o icon_16.png
/Applications/Inkscape.app/Contents/MacOS/inkscape -w 32 -h 32 icon.svg -o icon_32.png
/Applications/Inkscape.app/Contents/MacOS/inkscape -w 48 -h 48 icon.svg -o icon_48.png
/Applications/Inkscape.app/Contents/MacOS/inkscape -w 256 -h 256 icon.svg -o icon_256.png

magick icon_16.png icon_32.png icon_48.png icon_256.png icon.ico

