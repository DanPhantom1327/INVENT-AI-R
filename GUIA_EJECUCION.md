# INVENT-AI-R
## Sistema inteligente de gestión de inventarios

### 1. Descripción

INVENT-AI-R es una aplicación web académica para
gestionar inventarios de materia prima y pulpas
de fruta empacadas en presentaciones de 230 gramos.

Permite registrar ventas, compras, movimientos
de inventario y analizar la demanda futura mediante
modelos predictivos.

### 2. Tecnologías utilizadas

- Backend: Python, Django y Django REST Framework.
- Frontend: React y Vite.
- Base de datos: PostgreSQL 16.
- Contenedores: Docker y Docker Compose.
- Análisis predictivo: NumPy y Scikit-learn.
- Control de versiones: Git y GitHub.

### 3. Arquitectura

El sistema utiliza cinco microservicios Django:

| Servicio | Puerto | Función |
|---|---|---|
| auth-service | 8001 | Autenticación y usuarios |
| inventario-service | 8002 | Inventario y movimientos |
| ventas-service | 8003 | Registro de ventas |
| compras-service | 8004 | Registro de compras |
| analisis-service | 8005 | Proyecciones y alertas |

El frontend React utiliza el puerto 5173 cuando
está disponible.

### 4. Modelo de negocio

Los productos terminados son pulpas de fruta
en empaques de 230 gramos.

Precio de venta por empaque: $2.800 COP.

Las ventas utilizan cantidades enteras de empaques.

La materia prima se almacena en kilogramos.
El formulario de compras admite kg y libras
comerciales de 500 gramos, convirtiendo las
cantidades a kg antes de registrarlas.

### 5. Base de datos

Base de datos utilizada: invent_air.

PostgreSQL 16 se ejecuta localmente en el equipo
de desarrollo, fuera de Docker.

Los microservicios se conectan mediante
host.docker.internal.

IMPORTANTE:
El repositorio no contiene un respaldo de la base
de datos ni las credenciales privadas.

Para ejecutar el proyecto en otro equipo se
requiere configurar PostgreSQL, restaurar o crear
la estructura de la base de datos y proporcionar
las variables de entorno y claves necesarias.

No ejecutar scripts de regeneración de datos
sobre bases con información que se deba conservar.

### 6. Ejecución en el entorno configurado

Requisitos:
- Docker Desktop
- PostgreSQL 16 configurado
- Node.js y npm
- Variables de entorno y claves ya configuradas

Abrir Docker Desktop y verificar que PostgreSQL
esté disponible.

Desde la raíz del proyecto, ejecutar:

docker compose -f docker-compose.yml -f docker-compose.230g-test.yml up -d

Verificar los contenedores:

docker compose -f docker-compose.yml -f docker-compose.230g-test.yml ps

Iniciar el frontend:

npm --prefix frontend run dev

Abrir la dirección indicada por Vite,
normalmente http://localhost:5173/

### 7. Inteligencia artificial

El sistema utiliza tres modelos candidatos:

1. Promedio estacional de cuatro semanas.
2. Regresión lineal con tendencia semanal.
3. Regresión logarítmica con tendencia semanal.

Los modelos se comparan mediante backtesting
y se selecciona el de menor MAE para cada ítem.

El sistema proyecta el consumo futuro y calcula
la cobertura del inventario en días.

Los umbrales permiten clasificar las alertas
como ALTO, MEDIO o BAJO.

El módulo utiliza datos sintéticos académicos;
sus predicciones no equivalen a resultados
validados en una operación comercial real.

### 8. Pruebas

Se verificaron 47 pruebas unitarias del módulo
de análisis predictivo.

Para ejecutarlas:

docker compose -f docker-compose.yml -f docker-compose.230g-test.yml exec analisis-service python -m unittest discover -s analisis/tests -v

Para comprobar la configuración de un servicio:

docker compose -f docker-compose.yml -f docker-compose.230g-test.yml exec analisis-service python manage.py check

### 9. Detener el proyecto

Detener Vite con Ctrl + C.

Después ejecutar:

docker compose -f docker-compose.yml -f docker-compose.230g-test.yml down

No utilizar down -v si se desean conservar
los volúmenes de Docker.

### 10. Repositorio

https://github.com/DanPhantom1327/INVENT-AI-R
