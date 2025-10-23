!include "MUI2.nsh"
!include "nsDialogs.nsh"

;----------------
; App Settings
;----------------
!define AppName "bpsr-fishing"
!define AppExecutable "main.exe"
!define InstallerFile "${AppName}Installer.exe"
!define LicenseFile "LICENSE.txt" ; optional

Name "${AppName}"
OutFile "${InstallerFile}"
InstallDir "$PROGRAMFILES\${AppName}"
RequestExecutionLevel admin

;----------------
; Pages
;----------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LicenseFile}"  ; remove if no license
Page custom PageSelectShortcuts PageLeaveShortcuts
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

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

  ; Copy main executable
  File "dist\${AppExecutable}"

  ; Copy images folder
  File /r "images\*"

  ; Create empty logs folder
  CreateDirectory "$INSTDIR\logs"

  ; Create Start Menu shortcut if checked
  ${If} $CreateStartMenu = ${BST_CHECKED}
    CreateDirectory "$SMPROGRAMS\${AppName}"
    CreateShortCut "$SMPROGRAMS\${AppName}\${AppName}.lnk" "$INSTDIR\${AppExecutable}"
  ${EndIf}

  ; Create Desktop shortcut if checked
  ${If} $CreateDesktop = ${BST_CHECKED}
    CreateShortCut "$DESKTOP\${AppName}.lnk" "$INSTDIR\${AppExecutable}"
  ${EndIf}

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

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

  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

SectionEnd
