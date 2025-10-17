@echo off
REM Script para configurar hostname local para acesso ao banco

echo 🔧 Configurando hostname local para o banco PostgreSQL...

REM Adicionar entrada no arquivo hosts do Windows
echo.
echo Adicionando entrada no arquivo hosts...
echo 127.0.0.1 bot-sisci-db >> C:\Windows\System32\drivers\etc\hosts
echo 127.0.0.1 postgres-db >> C:\Windows\System32\drivers\etc\hosts

echo.
echo ✅ Configuração concluída!
echo.
echo 📝 Agora você pode conectar usando:
echo    Host: bot-sisci-db
echo    Porta: 5432
echo    Banco: suporte_interno
echo    Usuário: postgres
echo    Senha: postgres123
echo.
echo 🔗 String de conexão:
echo    postgresql://postgres:postgres123@bot-sisci-db:5432/suporte_interno
echo.
pause
