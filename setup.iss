[Setup]
AppName=Instad
AppVersion=v1.2.0.0
DefaultDirName={autopf}\Instad
DefaultGroupName=Instad
UninstallDisplayIcon={app}\instad.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=Instad-Setup-x64
SetupIconFile=assets\icon.ico
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\instad.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\Instad"; Filename: "{app}\instad.exe"
Name: "{autodesktop}\Instad"; Filename: "{app}\instad.exe"; Tasks: desktopicon

[Run]
; Universal Deno Installation for Windows via PowerShell
Filename: "powershell.exe"; \
    Parameters: "-ExecutionPolicy Bypass -Command ""try { if (!(Get-Command deno -ErrorAction SilentlyContinue)) { iwr https://deno.land/install.ps1 -useb | iex } } catch { exit 1 }"""; \
    StatusMsg: "Installing Deno runtime for signature solving..."; \
    Flags: runhidden

; Add Deno to Path for the current session/user if needed
Filename: "powershell.exe"; \
    Parameters: "-ExecutionPolicy Bypass -Command ""[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $HOME + '\.deno\bin', 'User')"""; \
    Flags: runhidden

Filename: "{app}\instad.exe"; Description: "{cm:LaunchProgram,Instad}"; Flags: nowait postinstall skipfsreq

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;