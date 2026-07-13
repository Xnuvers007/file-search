[Setup]
; Informasi dasar aplikasi
AppName=File Content Search Pro
AppVersion=2.6.0
AppPublisher=Xnuvers007 | Indra Dwi A
AppPublisherURL=https://github.com/Xnuvers007/file-search

; Lokasi instalasi default (C:\Program Files\FileSearchPro)
DefaultDirName={autopf}\FileSearchPro
DefaultGroupName=File Content Search Pro

; Konfigurasi output file installer (.exe)
OutputDir=dist_installer
OutputBaseFilename=FileSearchPro_Setup_Windows_x64
SetupIconFile=assets\search_icon.ico

; Kompresi tinggi (membuat ukuran installer jadi lebih kecil)
Compression=lzma2/ultra
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
; Opsi membuat shortcut di desktop
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PERHATIAN: Menyalin SELURUH ISI folder hasil build PyInstaller
Source: "dist\FileSearchPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Membuat shortcut di Start Menu dan Desktop
Name: "{group}\File Content Search Pro"; Filename: "{app}\FileSearchPro.exe"; IconFilename: "{app}\FileSearchPro.exe"
Name: "{autodesktop}\File Content Search Pro"; Filename: "{app}\FileSearchPro.exe"; Tasks: desktopicon; IconFilename: "{app}\FileSearchPro.exe"

[Run]
; Opsi "Run / Jalankan aplikasi" setelah instalasi selesai
Filename: "{app}\FileSearchPro.exe"; Description: "{cm:LaunchProgram,File Content Search Pro}"; Flags: nowait postinstall skipifsilent
