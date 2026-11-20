@echo off
REM Copies the CHROMAS authors example data out of Chromas2025.zip into the folders this project uses.
REM The zip is not part of this repository. Download it yourself from https://doi.org/10.17617/3.MJI3HA
REM and check the licence on that page first. Then run:
REM
REM     build_demo.bat                          looks for Chromas2025.zip here, then in your Downloads folder
REM     build_demo.bat "D:\path\Chromas2025.zip"
REM
REM   model_weights\sepia_2classes_fcn_resnet50.pth   the trained network, for the neuralnet method
REM   data\                                           example.mp4, example_chunk_0/1/2.mp4, example.dataset
REM   training_data\sepia_binary and sepia_3class     painted training images and masks
REM
REM All three folders are ignored by git, so none of this is uploaded.
setlocal
cd /d "%~dp0"

call :main %*
set RC=%ERRORLEVEL%

echo.
if %RC% EQU 0 echo build_demo finished.
if not %RC% EQU 0 echo build_demo failed. See the messages above.
echo.
pause
exit /b %RC%


:main
set "ZIP=%~1"
if "%ZIP%"=="" if exist "Chromas2025.zip" set "ZIP=%CD%\Chromas2025.zip"
if "%ZIP%"=="" if exist "%USERPROFILE%\Downloads\Chromas2025.zip" set "ZIP=%USERPROFILE%\Downloads\Chromas2025.zip"
if "%ZIP%"=="" goto nozip
if not exist "%ZIP%" goto nozip

set "WORK=%TEMP%\chromas2025_unpack"
if exist "%WORK%" rmdir /s /q "%WORK%"

echo Using %ZIP%
echo Unpacking it, about 230 MB. This takes a minute...
powershell -NoProfile -Command "Expand-Archive -LiteralPath $env:ZIP -DestinationPath $env:WORK -Force"
if errorlevel 1 exit /b 1

set "SRC=%WORK%\Chromas2025"
if not exist "%SRC%\model_weights" goto badzip
if not exist "%SRC%\tutorial_data" goto badzip
if not exist "%SRC%\training_data" goto badzip

echo Copying the trained weights to model_weights\ ...
if not exist model_weights mkdir model_weights
copy /y "%SRC%\model_weights\sepia_2classes_fcn_resnet50.pth" model_weights\ >nul
if errorlevel 1 exit /b 1

echo Copying the example videos and dataset to data\ ...
if not exist data mkdir data
xcopy /e /i /y "%SRC%\tutorial_data" data >nul
if errorlevel 1 exit /b 1

echo Copying the training images and masks to training_data\ ...
if not exist training_data mkdir training_data
xcopy /e /i /y "%SRC%\training_data\sepia_binary" training_data\sepia_binary >nul
if errorlevel 1 exit /b 1
xcopy /e /i /y "%SRC%\training_data\sepia_3class" training_data\sepia_3class >nul
if errorlevel 1 exit /b 1

rmdir /s /q "%WORK%"
echo.
echo Copied:
echo   model_weights\sepia_2classes_fcn_resnet50.pth
echo   data\example.mp4, example_chunk_0.mp4, example_chunk_1.mp4, example_chunk_2.mp4, example.dataset
echo   training_data\sepia_binary and training_data\sepia_3class
exit /b 0

:nozip
echo.
echo Chromas2025.zip not found.
echo Download it from https://doi.org/10.17617/3.MJI3HA and either put it in this folder or run:
echo     build_demo.bat "C:\path\to\Chromas2025.zip"
exit /b 1

:badzip
echo.
echo The zip does not have the folders Chromas2025\model_weights, tutorial_data and training_data. Is it the right file?
exit /b 1
