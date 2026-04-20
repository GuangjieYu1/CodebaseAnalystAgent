@ECHO OFF
SETLOCAL EnableExtensions

SET "BASE_DIR=%~dp0"
SET "WRAPPER_DIR=%BASE_DIR%.mvn\wrapper"
SET "PROPS_FILE=%WRAPPER_DIR%\maven-wrapper.properties"

IF NOT EXIST "%PROPS_FILE%" (
  ECHO Missing %PROPS_FILE%
  EXIT /B 1
)

FOR /F "usebackq tokens=1,* delims==" %%A IN ("%PROPS_FILE%") DO (
  IF "%%A"=="distributionUrl" SET "DIST_URL=%%B"
)

FOR %%I IN ("%DIST_URL%") DO SET "DIST_FILE=%%~nxI"
SET "DIST_NAME=%DIST_FILE:-bin.zip=%"
SET "ARCHIVE_FILE=%WRAPPER_DIR%\%DIST_FILE%"
SET "INSTALL_DIR=%WRAPPER_DIR%\%DIST_NAME%"
SET "MVN_CMD=%INSTALL_DIR%\bin\mvn.cmd"

IF NOT EXIST "%MVN_CMD%" (
  IF NOT EXIST "%ARCHIVE_FILE%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%DIST_URL%' -OutFile '%ARCHIVE_FILE%'"
    IF ERRORLEVEL 1 (
      WHERE mvn >NUL 2>NUL
      IF NOT ERRORLEVEL 1 (
        CALL mvn %*
        EXIT /B %ERRORLEVEL%
      )
      ECHO Unable to download Maven distribution and local Maven was not found.
      EXIT /B 1
    )
  )

  IF EXIST "%INSTALL_DIR%" RMDIR /S /Q "%INSTALL_DIR%"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%ARCHIVE_FILE%' -DestinationPath '%WRAPPER_DIR%' -Force"
  IF ERRORLEVEL 1 EXIT /B 1
)

CALL "%MVN_CMD%" %*
EXIT /B %ERRORLEVEL%
