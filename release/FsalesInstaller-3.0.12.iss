; FSales Inno Setup Installer
#define MyAppName "FSales"
#define MyAppVersion "3.0.12"
#define MyAppPublisher "FireSmart"
#define MyAppExeName "Fsales.exe"
#define MySourceDir "D:\Fsales_PCCC\dist\Fsales"

[Setup]
AppId={{B210A5E9-4E37-4D65-A91F-56F3B05B7E09}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=C:\Fsales
DisableDirPage=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=D:\Fsales_update\updates\3.0.12
OutputBaseFilename=Fsales-Setup-EXE-3.0.12
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
WizardImageFile=D:\Fsales_PCCC\assets\logo_pccc.bmp
WizardSmallImageFile=D:\Fsales_PCCC\assets\logo_pccc_small.bmp
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình"; GroupDescription: "Tùy chọn bổ sung:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
