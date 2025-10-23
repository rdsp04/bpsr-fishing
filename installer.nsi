!include "MUI2.nsh"
!include "nsDialogs.nsh"

;----------------
; App Settings
;----------------
!define AppName "bpsr-fishing"
!define AppExecutable "bpsr-fishing.exe"
!define InstallerFile "${AppName}_x64-Setup.exe"
!define LicenseFile "LICENSE"

Name "${AppName}"
OutFile "${InstallerFile}"
InstallDir "$LOCALAPPDATA\${AppName}"
RequestExecutionLevel admin

;----------------
; Pages
;----------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LicenseFile}"
Page custom PageSelectShortcuts PageLeaveShortcuts
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstall pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;----------------
; Languages
;----------------
!insertmacro MUI_LANGUAGE "English"

;----------------
; Variables
;----------------
Var StartMenuCheckbox
Var DesktopCheckbox
Var CreateStartMenu
Var CreateDesktop

;----------------
; Shortcut Selection Page
;----------------
Function PageSelectShortcuts
  nsDialogs::Create 1018
  Pop $0

  ${NSD_CreateCheckBox} 20u 20u 100% 12u "Create Start Menu Shortcut"
  Pop $StartMenuCheckbox
  ${NSD_SetState} $StartMenuCheckbox ${BST_CHECKED}

  ${NSD_CreateCheckBox} 20u 40u 100% 12u "Create Desktop Shortcut"
  Pop $DesktopCheckbox
  ${NSD_SetState} $DesktopCheckbox ${BST_CHECKED}

  nsDialogs::Show
FunctionEnd

Function PageLeaveShortcuts
  ${NSD_GetState} $StartMenuCheckbox $CreateStartMenu
  ${NSD_GetState} $DesktopCheckbox $CreateDesktop
FunctionEnd

;----------------
; Installation Section
;----------------
Section "Install"

  SetOutPath "$INSTDIR"

  File "dist\${AppExecutable}"
  File /r "images"
  CreateDirectory "$INSTDIR\logs"

  ${If} $CreateStartMenu = ${BST_CHECKED}
    CreateDirectory "$SMPROGRAMS\${AppName}"
    CreateShortCut "$SMPROGRAMS\${AppName}\${AppName}.lnk" "$INSTDIR\${AppExecutable}"
  ${EndIf}

  ${If} $CreateDesktop = ${BST_CHECKED}
    CreateShortCut "$DESKTOP\${AppName}.lnk" "$INSTDIR\${AppExecutable}"
  ${EndIf}

  WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd

;----------------
; Uninstall Section
;----------------
Section "Uninstall"

  Delete "$INSTDIR\${AppExecutable}"
  RMDir /r "$INSTDIR\images"
  RMDir /r "$INSTDIR\logs"

  Delete "$SMPROGRAMS\${AppName}\${AppName}.lnk"
  RMDir "$SMPROGRAMS\${AppName}"

  Delete "$DESKTOP\${AppName}.lnk"

  Delete "$INSTDIR\uninstall.exe"
  RMDir /r /REBOOTOK "$INSTDIR"

SectionEnd
