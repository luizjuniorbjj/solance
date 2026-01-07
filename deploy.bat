@echo off
echo ========================================
echo   AiSyster - Deploy para Railway
echo ========================================
echo.

cd /d c:\aisyster

echo Adicionando arquivos...
git add .

echo.
set /p msg="Mensagem do commit (ou Enter para 'Update'): "
if "%msg%"=="" set msg=Update

echo.
echo Fazendo commit...
git commit -m "%msg%"

echo.
echo Enviando para GitHub...
git push

echo.
echo ========================================
echo   Deploy iniciado!
echo   Aguarde 2-3 min para ficar online.
echo   URL: https://www.aisyster.com/app
echo ========================================
pause
