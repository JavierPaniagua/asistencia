# 🎓 SISTEMA DE ASISTENCIA ESCOLAR
## Guía final de instalación y puesta en funcionamiento

Sistema de control de asistencia mediante:

- ESP32-S3
- Lector RFID RC522
- Tarjetas RFID
- Registro por cédula
- Django
- Python
- SQLite
- Red local

---

# 1. REQUISITOS DE LA COMPUTADORA

Antes de instalar el sistema verificar que la computadora tenga:

- Windows 10 u 11
- Python
- Git
- Navegador Google Chrome o Microsoft Edge
- Conexión a la misma red que el ESP32

Para desarrollo también se recomienda:

- Visual Studio Code
- Extensión Python de VS Code

Arduino IDE solamente es necesario si se necesita volver a programar
el ESP32.

---

# 2. COMPROBAR PYTHON

Abrir PowerShell y ejecutar:

python --version

Debe mostrar una versión de Python instalada.

Ejemplo:

Python 3.14.6

También comprobar pip:

python -m pip --version

---

# 3. COMPROBAR GIT

Ejecutar:

git --version

Debe mostrar la versión instalada de Git.

---

# 4. CREAR CARPETA PARA EL SISTEMA

Abrir PowerShell:

mkdir C:\sistemas

cd C:\sistemas

---

# 5. CLONAR EL PROYECTO DESDE GITHUB

Ejecutar:

git clone https://github.com/JavierPaniagua/asistencia.git

Entrar al proyecto:

cd asistencia

---

# 6. VERIFICAR LA RAMA

Ejecutar:

git branch

Debe aparecer:

* main

La rama `main` contiene la versión estable del sistema.

---

# 7. CREAR ENTORNO VIRTUAL

Ejecutar:

python -m venv venv

---

# 8. ACTIVAR EL ENTORNO VIRTUAL

Si PowerShell bloquea la ejecución de scripts:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Luego:

.\venv\Scripts\Activate.ps1

Debe aparecer:

(venv) PS C:\sistemas\asistencia>

---

# 9. INSTALAR DEPENDENCIAS

Ejecutar:

python -m pip install --upgrade pip

Luego:

python -m pip install -r requirements.txt

Esto instalará Django y las demás librerías utilizadas por el sistema.

---

# 10. VERIFICAR EL SISTEMA

Ejecutar:

python manage.py check

El resultado esperado es:

System check identified no issues (0 silenced).

---

# 11. BASE DE DATOS

El sistema utiliza:

db.sqlite3

No necesita instalar MySQL, PostgreSQL ni otro servidor de base de datos.

Si `db.sqlite3` está incluido en el repositorio, al clonar el proyecto
también se obtiene la base de datos correspondiente a esa versión.

IMPORTANTE:

No ejecutar `makemigrations` ni `migrate` durante una instalación normal
si se está utilizando la base de datos ya preparada del proyecto.

---

# 12. INICIAR EL SERVIDOR

Con el entorno virtual activo ejecutar:

python manage.py runserver 0.0.0.0:8000

Mientras se utiliza el sistema esta ventana de PowerShell debe permanecer
abierta.

---

# 13. ABRIR EL SISTEMA

En la computadora servidor:

Pantalla de asistencia:

http://127.0.0.1:8000/pantalla/

Reportes:

http://127.0.0.1:8000/reportes/

Administración:

http://127.0.0.1:8000/admin/

---

# 14. ACCESO DESDE OTRO DISPOSITIVO

Si la computadora servidor utiliza:

192.168.0.10

otro dispositivo conectado a la misma red puede ingresar a:

http://192.168.0.10:8000/pantalla/

También puede acceder a:

http://192.168.0.10:8000/reportes/

---

# 15. CONFIGURACIÓN DE RED PARA EL ESP32

El ESP32 actualmente utiliza como dirección del servidor:

http://192.168.0.10:8000/

Por este motivo se recomienda que la computadora que funciona como
servidor tenga reservada la dirección:

192.168.0.10

La mejor opción es realizar una RESERVA DHCP en el router.

De esta manera la computadora siempre recibirá la misma dirección IP.

Si la nueva computadora utiliza correctamente 192.168.0.10, no será
necesario modificar el programa del ESP32.

---

# 16. FIREWALL DE WINDOWS

Si el ESP32 u otra computadora no puede conectarse al servidor:

1. Revisar Firewall de Windows.
2. Permitir Python en redes privadas.
3. Verificar que todos los dispositivos estén conectados a la misma red.
4. Verificar que el servidor esté ejecutándose con:

python manage.py runserver 0.0.0.0:8000

---

# 17. PROBAR EL SISTEMA

Realizar las siguientes pruebas:

1. Abrir la pantalla de asistencia.
2. Acercar una tarjeta RFID registrada.
3. Verificar el registro de entrada.
4. Verificar que aparezca el alumno en pantalla.
5. Probar registro mediante cédula.
6. Probar una tarjeta RFID desconocida.
7. Verificar el registro de salida.
8. Verificar el reporte diario.
9. Verificar el reporte mensual.
10. Verificar el reporte individual.
11. Exportar el reporte a Excel.
12. Exportar el reporte a PDF.

---

# 18. FUNCIONAMIENTO DE ENTRADA Y SALIDA

El sistema permite un registro diario por alumno.

PRIMER REGISTRO:

ENTRADA

Se guarda:

hora_entrada

SEGUNDO REGISTRO:

SALIDA

Se guarda:

hora_salida

El sistema utiliza un tiempo mínimo de permanencia antes de permitir
el registro de salida.

Actualmente:

240 minutos = 4 horas

---

# 19. ESTADOS DE ASISTENCIA

El sistema puede identificar:

JORNADA COMPLETA

El alumno tiene entrada y salida.

EN EL COLEGIO

El alumno tiene entrada pero todavía no tiene salida.

AUSENTE

El alumno no tiene registro de entrada.

PENDIENTE

Corresponde a una fecha que todavía no debe computarse.

---

# 20. REPORTES DISPONIBLES

El sistema dispone de:

## Reporte diario

Muestra:

- Alumno
- Cédula
- Curso
- Entrada
- Salida
- Estado

## Reporte mensual

Muestra la asistencia de todos los alumnos durante el mes.

Estados resumidos:

C = Jornada completa

E = Solo entrada

A = Ausente

- = Fecha pendiente

Totales:

JC = Jornadas completas

SE = Solo entrada

A = Ausencias

% = Porcentaje de asistencia

## Reporte individual

Permite seleccionar un alumno y un periodo.

Muestra:

- Fecha
- Día
- Hora de entrada
- Hora de salida
- Estado
- Días computados
- Presentes
- Ausentes
- Jornadas completas
- Porcentaje de asistencia

---

# 21. EXPORTACIONES

El sistema permite:

- Imprimir reportes
- Exportar a Excel
- Exportar a PDF

El reporte mensual PDF está preparado para hoja Oficio horizontal.

Medida:

13 x 8,5 pulgadas

---

# 22. INICIAR EL SISTEMA CADA DÍA

Cada vez que se encienda la computadora:

Abrir PowerShell.

Ejecutar:

cd C:\sistemas\asistencia

Activar el entorno:

.\venv\Scripts\Activate.ps1

Si PowerShell bloquea la activación:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Luego ejecutar:

python manage.py runserver 0.0.0.0:8000

Finalmente abrir:

http://127.0.0.1:8000/pantalla/

---

# 23. ACTUALIZAR DESDE GITHUB

Antes de actualizar se recomienda verificar que no existan cambios locales.

Ejecutar:

cd C:\sistemas\asistencia

git status

Luego:

git pull origin main

Después activar el entorno virtual:

.\venv\Scripts\Activate.ps1

Si requirements.txt fue actualizado:

python -m pip install -r requirements.txt

Finalmente:

python manage.py check

---

# 24. GUARDAR CAMBIOS EN GITHUB

Para guardar una nueva versión:

git status

git add .

git commit -m "Descripcion de los cambios"

git push origin main

Verificar:

git status

El resultado esperado es:

nothing to commit, working tree clean

---

# 25. RESPALDO DE LA BASE DE DATOS

El archivo más importante con los datos es:

db.sqlite3

Se recomienda realizar copias periódicas de este archivo.

Ejemplo:

db.sqlite3
db_respaldo_2026-08-31.sqlite3

IMPORTANTE:

No reemplazar ni eliminar la base de datos original mientras el servidor
Django está funcionando.

---

# 26. ESTRUCTURA PRINCIPAL

Proyecto:

C:\sistemas\asistencia

Elementos principales:

manage.py

db.sqlite3

requirements.txt

asistencia/

config/

venv/

El entorno `venv` no debe subirse a GitHub.

---

# 27. HARDWARE RFID

Hardware utilizado:

ESP32-S3 N16R8

Lector:

RC522

Conexiones:

RC522        ESP32-S3

3.3V   ->    3V3
GND    ->    GND
RST    ->    GPIO 4
SDA    ->    GPIO 5
SCK    ->    GPIO 12
MOSI   ->    GPIO 11
MISO   ->    GPIO 13
IRQ    ->    Sin conectar

El sistema utiliza:

SPI.begin(12, 13, 11, 5);

No modificar estas conexiones si el lector está funcionando correctamente.

---

# 28. COMPROBACIÓN RÁPIDA

Si el sistema deja de funcionar comprobar en este orden:

1. ¿La computadora está encendida?
2. ¿Está conectada a la red?
3. ¿Tiene la IP correcta?
4. ¿El entorno virtual está activo?
5. ¿Django está ejecutándose?
6. ¿El ESP32 está conectado al Wi-Fi?
7. ¿El ESP32 y la PC están en la misma red?
8. ¿El Firewall permite Python?
9. ¿La base de datos db.sqlite3 existe?
10. ¿La tarjeta RFID está registrada?

---

# 29. COMANDOS RÁPIDOS

INICIAR:

cd C:\sistemas\asistencia

.\venv\Scripts\Activate.ps1

python manage.py runserver 0.0.0.0:8000


VERIFICAR:

python manage.py check


ACTUALIZAR:

git pull origin main


VER ESTADO DE GIT:

git status


GUARDAR:

git add .

git commit -m "Actualizacion del sistema"

git push origin main


DETENER SERVIDOR:

CTRL + C

---

# 30. VERSIÓN

Sistema de Asistencia Escolar

Versión estable:

Entrada y Salida

Tecnologías:

- Python
- Django
- SQLite
- ESP32-S3
- RFID RC522
- HTML
- CSS
- JavaScript
- Excel
- PDF

Desarrollado para uso educativo.