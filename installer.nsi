!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"


;----------------
; App Settings
;----------------
Icon "icons/icon.ico"
UninstallIcon "icons/icon.ico"

!define AppName "bpsr-fishing"
!define AppId "bpsr-fishing"
!define AppVersion "1.2.0"
!define AppExecutable "bpsr-fishing.exe"
!define InstallerFile "${AppName}_${AppVersion}_x64-Setup.exe"
!define LicenseFile "LICENSE"
!define UninstallRegKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\${AppId}"

Name "${AppName}"
OutFile "${InstallerFile}"
InstallDir "$LOCALAPPDATA\${AppName}"
RequestExecutionLevel user

;----------------
; Variables
;----------------
Var isUpdate
Var StartMenuCheckbox
Var DesktopCheckbox
Var CreateStartMenu
Var CreateDesktop
Var SkipWelcome
Var SkipLicense
Var SkipDir
Var IS_UPDATER

!insertmacro GetParameters
;----------------
; Initialization
;----------------
Function CreateSelectedShortcuts
  SetShellVarContext current

  StrCmp $CreateStartMenu ${BST_CHECKED} 0 +3
    CreateDirectory "$SMPROGRAMS\${AppName}"
    CreateShortcut "$SMPROGRAMS\${AppName}\${AppName}.lnk" "$INSTDIR\${AppExecutable}" "" "$INSTDIR\icons\icon.ico"

  StrCmp $CreateDesktop ${BST_CHECKED} 0 +3
    CreateShortcut "$DESKTOP\${AppName}.lnk" "$INSTDIR\${AppExecutable}" "" "$INSTDIR\icons\icon.ico"
FunctionEnd


Function PageFinishShortcuts
  nsDialogs::Create 1018
  Pop $0

  ${NSD_CreateLabel} 12u 10u 100% 12u "Create shortcuts"
  Pop $R0

  ${NSD_CreateCheckBox} 20u 30u 100% 12u "Create Start Menu shortcut"
  Pop $StartMenuCheckbox
  ${NSD_SetState} $StartMenuCheckbox ${BST_CHECKED}

  ${NSD_CreateCheckBox} 20u 50u 100% 12u "Create Desktop shortcut"
  Pop $DesktopCheckbox
  ${NSD_SetState} $DesktopCheckbox ${BST_CHECKED}

  nsDialogs::Show
FunctionEnd

Function PageLeaveFinishShortcuts
  ${NSD_GetState} $StartMenuCheckbox $CreateStartMenu
  ${NSD_GetState} $DesktopCheckbox $CreateDesktop
  Call CreateSelectedShortcuts
FunctionEnd

Function HasSubstring
  ; $0 = haystack, $1 = needle
  ; $2 = "1" if found, empty if not
  Push $3
  Push $4
  StrCpy $2 ""
  StrLen $3 $1
  loop_hs:
    StrCpy $4 $0 $3
    StrCmp $4 $1 found_hs
    StrLen $5 $0
    IntCmp $5 0 done_hs
    StrCpy $0 $0 "" 1
    Goto loop_hs
  found_hs:
    StrCpy $2 1
  done_hs:
  Pop $4
  Pop $3
FunctionEnd

Function .onInit


  ; Default flags
  StrCpy $IS_UPDATER "0"
  StrCpy $isUpdate "0"

  ; Get command-line arguments
  ${GetParameters} $R0

  ; Check for /UPDATER argument
  StrCpy $1 "/UPDATER"
  StrCpy $0 $R0
  Call HasSubstring
  StrCmp $2 "1" +2 0
    StrCpy $IS_UPDATER "1"

  ; Detect existing installation
  ReadRegStr $R3 HKCU "${UninstallRegKey}" "InstallLocation"
  StrCmp $R3 "" not_installed 0
    StrCpy $INSTDIR $R3
    StrCpy $isUpdate "1"
    Goto done_init
not_installed:
    StrCpy $isUpdate "0"
done_init:

  ; Skip UI pages if running silent
  ${If} ${Silent}
    StrCpy $SkipWelcome "1"
    StrCpy $SkipLicense "1"
    StrCpy $SkipDir "1"
  ${EndIf}

  ; Control shell context (admin only for full install)
  ${If} $IS_UPDATER == "0"
    SetShellVarContext current
  ${Else}
    SetShellVarContext all
  ${EndIf}
FunctionEnd


Function SkipDirPage
  ${If} $isUpdate == "1"
    Abort
  ${EndIf}
FunctionEnd

;----------------
; Page Sequence
;----------------
!define MUI_ICON "icons/icon.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LicenseFile}"
PageEx directory
  PageCallbacks SkipDirPage
PageExEnd
!insertmacro MUI_PAGE_INSTFILES
Page custom PageFinishShortcuts PageLeaveFinishShortcuts
!define MUI_FINISHPAGE_RUN "$INSTDIR\${AppExecutable}"
!define MUI_FINISHPAGE_RUN_TEXT "Run ${AppName}"
!define MUI_FINISHPAGE_RUN_CHECKED
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateSelectedShortcuts
!insertmacro MUI_PAGE_FINISH


!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"


;----------------
; Installation Section
;----------------
Section "Install"
    nsExec::ExecToStack 'taskkill /F /IM "${AppExecutable}"'

  SetOutPath "$INSTDIR"

  ${If} $isUpdate == "1"
    DetailPrint "Updating ${AppName}..."
    ; Delete only files that need replacement
    RMDir /r "$INSTDIR\images"
    RMDir /r "$INSTDIR\html"
    RMDir /r "$INSTDIR\icons"
    RMDir /r "$INSTDIR\.git"
    RMDir /r "$INSTDIR\.venv"

    RMDir /r "$INSTDIR\config"
    Delete "$INSTDIR\${AppExecutable}"

    ; Keep logs/screenshots
  ${Else}
    DetailPrint "Installing ${AppName}..."
    CreateDirectory "$INSTDIR\logs"
  ${EndIf}

  ; Copy files
  File "dist\${AppExecutable}"
  File /r "images"
  File /r "config"
  File /r "html"
  File /r "icons"


  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Registry info
  WriteRegStr HKCU "${UninstallRegKey}" "DisplayName" "${AppName}"
  WriteRegStr HKCU "${UninstallRegKey}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UninstallRegKey}" "UninstallString" "$INSTDIR\uninstall.exe"

  ${If} $IS_UPDATER == "0"


    nsExec::ExecToLog 'cmd /C start "" "$INSTDIR\${AppExecutable}"'
  ${EndIf}
SectionEnd

;----------------
; Uninstall Section
;----------------
Section "Uninstall"
    nsExec::ExecToStack 'taskkill /F /IM "${AppExecutable}"'

    ; Delete main executable and folders
    Delete "$INSTDIR\${AppExecutable}"
    RMDir /r "$INSTDIR\images"
    RMDir /r "$INSTDIR\config"
    RMDir /r "$INSTDIR\html"
    RMDir /r "$INSTDIR\logs"
    RMDir /r "$INSTDIR\screenshots"

    ; Remove Start Menu shortcut and folder
    Delete "$SMPROGRAMS\${AppName}\${AppName}.lnk"
    RMDir "$SMPROGRAMS\${AppName}"

    ; Remove Desktop shortcut
    Delete "$DESKTOP\${AppName}.lnk"

    ; Remove uninstaller
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r /REBOOTOK "$INSTDIR"

    ; Remove registry key
    DeleteRegKey HKCU "${UninstallRegKey}"
SectionEnd
