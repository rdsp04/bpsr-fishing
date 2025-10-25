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
!define AppVersion "1.1.0"
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
Var ProgressBar
Var ProgressLabel
Var SkipWelcome
Var SkipLicense
Var SkipDir
Var CMD_ARGS
Var IS_UPDATER


!insertmacro GetParameters
;----------------
; Initialization
;----------------
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
  ${If} $IS_UPDATER == "1"
    SetShellVarContext current
  ${Else}
    SetShellVarContext all
  ${EndIf}
FunctionEnd





;----------------
; Custom Pages
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

Function SkipDirPage
  ${If} $isUpdate == "1"
    Abort
  ${EndIf}
FunctionEnd

;----------------
; Updating Page
;----------------
Function PageUpdate
  nsDialogs::Create 1018
  Pop $0

  ${NSD_CreateLabel} 0u 10u 100% 12u "Updating ${AppName}..."
  Pop $ProgressLabel

  ${NSD_CreateProgressBar} 0u 30u 100% 12u
  Pop $ProgressBar
  SendMessage $ProgressBar ${PBM_SETRANGE} 0 100
  SendMessage $ProgressBar ${PBM_SETPOS} 0 0

  nsDialogs::Show
FunctionEnd

Function SkipUpdatePage
  ${If} $isUpdate == "0"
    Abort
  ${EndIf}
FunctionEnd
Function PreShowUpdate
  ${If} $isUpdate == "0"
    Abort
  ${EndIf}
FunctionEnd
;----------------
; Page Sequence
;----------------
!define MUI_ICON "icons/icon.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LicenseFile}"
Page custom PageSelectShortcuts PageLeaveShortcuts
PageEx custom
  PageCallbacks PreShowUpdate
PageExEnd
PageEx directory
  PageCallbacks SkipDirPage
PageExEnd
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH


!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"


;----------------
; Installation Section
;----------------
Section "Install"

  SetOutPath "$INSTDIR"

  ${If} $isUpdate == "1"
    DetailPrint "Updating ${AppName}..."
    ; Delete only files that need replacement
    Delete "$INSTDIR\${AppExecutable}"
    Delete "$INSTDIR\config\*.*"
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


  ; Shortcuts (only on fresh install)
  ${If} $isUpdate == "0"
    ${If} $CreateStartMenu = ${BST_CHECKED}
      CreateDirectory "$SMPROGRAMS\${AppName}"
      CreateShortCut "$SMPROGRAMS\${AppName}\${AppName}.lnk" "$INSTDIR\${AppExecutable}" "" "$INSTDIR\icons\icon.ico"
    ${EndIf}

    ${If} $CreateDesktop = ${BST_CHECKED}
      CreateShortCut "$DESKTOP\${AppName}.lnk" "$INSTDIR\${AppExecutable}" "" "$INSTDIR\icons\icon.ico"
    ${EndIf}
  ${EndIf}

  ; Show progress bar incrementally (example)
  SendMessage $ProgressBar ${PBM_SETPOS} 50 0
  Sleep 500
  SendMessage $ProgressBar ${PBM_SETPOS} 100 0

  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Registry info
  WriteRegStr HKCU "${UninstallRegKey}" "DisplayName" "${AppName}"
  WriteRegStr HKCU "${UninstallRegKey}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UninstallRegKey}" "UninstallString" "$INSTDIR\uninstall.exe"

  ${If} $CMDLINE == "/UPDATER"
    Exec "$INSTDIR\${AppExecutable}"
  ${EndIf}

SectionEnd

;----------------
; Uninstall Section
;----------------
Section "Uninstall"

  Delete "$INSTDIR\${AppExecutable}"
  RMDir /r "$INSTDIR\images"
  RMDir /r "$INSTDIR\config"
  RMDir /r "$INSTDIR\html"
  RMDir /r "$INSTDIR\logs"
  RMDir /r "$INSTDIR\screenshots"

  Delete "$SMPROGRAMS\${AppName}\${AppName}.lnk"
  RMDir "$SMPROGRAMS\${AppName}"

  Delete "$DESKTOP\${AppName}.lnk"

  Delete "$INSTDIR\uninstall.exe"
  RMDir /r /REBOOTOK "$INSTDIR"

  DeleteRegKey HKCU "${UninstallRegKey}"

SectionEnd
