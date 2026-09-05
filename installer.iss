; ──────────────────────────────────────────────────────────────────────
; TechnobizTrader — Windows installer
; Run:  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; Output:  dist\installer\TechnobizTrader-Setup-1.0.0.exe
; ──────────────────────────────────────────────────────────────────────
#define MyAppName "TechnobizTrader"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TechnobizTrader"
#define MyAppURL "https://github.com/pitchiluxe/technobiz-trader-agent"
#define MyAppExeName "TechnobizTrader.exe"

[Setup]
AppId={{A4B7E2D8-3F1C-4A2B-9E8D-7C6F5A4B3C2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=RELEASE_NOTES.md
InfoBeforeFile=
OutputDir=dist\installer
OutputBaseFilename=TechnobizTrader-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
Uninstallable=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} {#MyAppVersion} — AI Trading Agency
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Bundle the entire COLLECT build (TechnobizTrader.exe + _internal\ subfolder)
; into the install directory. The Inno Setup "Flags: recursesubdirs createallsubdirs"
; preserves the directory structure exactly so Python can still find its libs.
Source: "dist\TechnobizTrader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; NOTE: A ".gitkeep" line below so the section stays valid even if Source is missing
Source: "Erick.jpg"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}";                       Filename: "{app}\{#MyAppExeName}"; Parameters: "--headless"
Name: "{group}\Open Dashboard";                     Filename: "{app}\{#MyAppExeName}"; Parameters: "--open"
Name: "{group}\Uninstall {#MyAppName}";             Filename: "{uninstallexe}"

; Desktop shortcut (optional, default off)
Name: "{commondesktop}\{#MyAppName}";               Filename: "{app}\{#MyAppExeName}"; Parameters: "--headless"; Tasks: desktopicon

[Run]
; After install, optionally start the server (no browser popup) and show it in the notification area.
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} (server)"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; When uninstalling, also remove per-user data so the next install starts clean
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[Code]
// Custom message shown on the install wizard's "Installing" page so the user
// understands what is happening after they click Install.
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
