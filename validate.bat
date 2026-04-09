@echo off
echo ============================================
echo BPLS CSV Validator App
echo ============================================
python "%~dp0bpls_validator.py" %*
if errorlevel 1 (
    echo.
    echo Validation FAILED. Please check the errors above.
    pause
    exit /b 1
)
echo.
echo Validation completed successfully!
pause