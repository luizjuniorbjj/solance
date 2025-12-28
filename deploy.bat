@echo off
echo ========================================
echo   SoulHaven - Deploy para Railway
echo ========================================
echo.

cd /d c:\soulhaven

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
echo   URL: https://solance-production-959e.up.railway.app/app
echo ========================================
pause
