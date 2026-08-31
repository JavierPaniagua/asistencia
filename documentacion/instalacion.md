# INSTALACIÓN DEL SISTEMA DE ASISTENCIA EN OTRA PC

## 1. Crear carpeta de trabajo

```powershell
mkdir C:\sistemas
cd C:\sistemas

## 2. Clonar el proyecto desde GitHub
git clone -b asistencia-entrada https://github.com/JavierPaniagua/asistencia.git

python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass (si se bloquea)

.\venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

python manage.py runserver 0.0.0.0:8000

http://127.0.0.1:8000/pantalla/
http://127.0.0.1:8000/reportes/
http://127.0.0.1:8000/admin/