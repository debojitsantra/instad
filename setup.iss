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
Source: "assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\Instad"; Filename: "{app}\instad.exe"
Name: "{autodesktop}\Instad"; Filename: "{app}\instad.exe"; Tasks: desktopicon

[Run]
; Universal Deno Installation for Windows via PowerShell 
Filename: "powershell.exe"; \
<<<<<<< HEAD
    Parameters: "-ExecutionPolicy Bypass -Command ""try {{ if (!(Get-Command deno -ErrorAction SilentlyContinue)) {{ iwr https://deno.land/install.ps1 -useb | iex } } catch {{ exit 1 }"""; \
=======
    Parameters: "-ExecutionPolicy Bypass -Command ""try {{ if (!(Get-Command deno -ErrorAction SilentlyContinue)) {{ iwr https://deno.land/install.ps1 -useb | iex } } catch {{ exit 1 } }"""; \
>>>>>>> d797404e99a4f3817cda32725d74d95c1d73c3d9
    StatusMsg: "Installing Deno runtime for signature solving..."; \
    Flags: runhidden runasoriginaluser

; Add Deno to Path for the current session/user if needed (runs as original user to modify user environment)
Filename: "powershell.exe"; \
    Parameters: "-ExecutionPolicy Bypass -Command ""[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $HOME + '\.deno\bin', 'User')"""; \
    Flags: runhidden runasoriginaluser

Filename: "{app}\instad.exe"; Description: "{cm:LaunchProgram,Instad}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;