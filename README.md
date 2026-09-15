# NovaGo - Sistema de Delivery & Despacho de Encomiendas

[![Django](https://img.shields.io/badge/Django-6.0-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![GitFlow](https://img.shields.io/badge/GitFlow-Standard-orange.svg)](https://nvie.com/posts/a-successful-git-branching-model/)
[![License](https://img.shields.io/badge/Academic-UTP_2026--II-red.svg)](https://www.utp.edu.pe)

> **Universidad Tecnológica del Perú (UTP)**  
> **Facultad de Ingeniería de Sistemas e Informática**  
> **Curso:** Herramientas de Desarrollo (`100000S66T`) - Ciclo 2026-II  
> **Estudiante:** Ruben Walter Vivas Jimenez (Código: `U18209770` | Correo: `u22224908@utp.edu.pe`)  
> **Repositorio Oficial:** [https://github.com/Ruben-DWC/NovaGo-Delivery-System](https://github.com/Ruben-DWC/NovaGo-Delivery-System)

---

## 1. Descripción del Proyecto

Sistema web integral de delivery y gestión de despachos con seguimiento telemático GPS en tiempo real, control riguroso de inventario, pasarela de pagos con conciliación y auditoría administrativa de pedidos. Desarrollado con Django y Python bajo una arquitectura MVT modular y un ciclo de vida gestionado rigurosamente mediante Git y GitHub.

---

## Propuesta de Valor de NovaGo

**NovaGo** no compite como marketplace multi-tienda (como DiDi o PedidosYa). NovaGo es un **minimarket digital con delivery propio**.

Eso significa que el sistema controla de extremo a extremo:

- Catálogo y stock de una tienda única.
- Flujo completo del pedido en una sola plataforma.
- Gestión directa de motorizados y seguimiento del recorrido.

### ¿Por qué NovaGo es diferente y único?

1. **Control total de inventario y despacho**: al ser tienda única, el stock y la preparación son más consistentes.
2. **Trazabilidad operativa interna**: pedido, pago, ruta y entrega se auditan dentro del mismo sistema.
3. **Experiencia más predecible para el cliente**: menos variabilidad por comercios externos.
4. **Modelo ideal para prototipo académico serio**: suficiente complejidad real sin convertirse en plataforma masiva.

### ¿Qué problema resuelve el sistema?

NovaGo resuelve la falta de coordinación entre inventario, pedidos, pagos y entrega en pequeños comercios con reparto propio. Evita:

- Sobreventa por falta de sincronización de stock.
- Pedidos sin trazabilidad clara para cliente y administrador.
- Gestión manual desordenada de pagos y estados de entrega.

### ¿Quiénes lo usan?

1. **Clientes**: compran productos del minimarket, pagan y rastrean su pedido.
2. **Motorizados**: revisan pedidos asignados, reportan ubicación y estado de entrega.
3. **Administradores**: gestionan productos, stock, pedidos, pagos y usuarios.

## Definición del Proyecto (Rubro)

**NovaGo** se define como una **tienda de conveniencia (minimarket) con delivery propio**.

No es un marketplace tipo "PedidosYa" o "DiDi Food" (multi-tienda), sino una plataforma de **una sola tienda** con 3 roles: cliente, motorizado y administrador.

### ¿Qué vende NovaGo?

- Alimentos envasados y snacks
- Bebidas (agua, gaseosas, jugos, energéticas)
- Productos de uso rápido del hogar (básicos)

### ¿Por qué este rubro?

Este enfoque cumple de forma directa con lo solicitado por el curso y la profesora, con una complejidad intermedia y realista para un prototipo:

- Stock por producto (inventario)
- Pagos (transferencia y otros métodos)
- Entrega por motorizado
- Mapa GPS con ruta de pedido
- Flujo web para cliente y motorizado

### Alcance MVP (versión académica intermedia)

1. Cliente: registro/login, catálogo, pedido, pago, seguimiento.
2. Motorizado: pedidos asignados, actualización de ubicación y estado.
3. Admin: gestión de productos/stock, pedidos, pagos y usuarios.

Con este alcance se prioriza demostrar buenas prácticas de desarrollo y Git (ramas, commits, merge, resolución de conflictos), sin intentar una complejidad de producción completa.

## Tabla de Contenidos

- [Propuesta de Valor de NovaGo](#-propuesta-de-valor-de-novago
- [Definición del Proyecto (Rubro)](#-definición-del-proyecto-rubro
- [Estado Actual del Desarrollo](#-estado-actual-del-desarrollo
- [Roadmap de Integración](#-roadmap-de-integración
- [Cómo Demostrar que NovaGo es Diferente](#-cómo-demostrar-que-novago-es-diferente)
- [Características](#-características
- [Tecnologías](#-tecnologías
- [Instalación](#-instalación
- [Conceptos de Git Aplicados](#-conceptos-de-git-aplicados
- [Estructura del Proyecto](#-estructura-del-proyecto
- [Comandos Útiles](#-comandos-útiles

## Estado Actual del Desarrollo

### Implementado

1. **Branding y UX base**: identidad NovaGo, landing moderna, testimonios, microinteracciones y tema claro/oscuro.
2. **Autenticación por rol**: login/registro con pantallas de éxito y redirección por rol.
3. **Catálogo funcional**: listado, búsqueda, filtro por categoría y detalle de producto.
4. **Carrito y checkout**: agregar/actualizar/eliminar productos, crear pedido y pago pendiente.
5. **Pedidos**: listado y detalle con control de permisos por rol.
6. **Tracking operativo**: panel de motorizado, registro de ubicación y vista de rastreo del pedido.
7. **Arquitectura modular**: separación de servicios de negocio (por ejemplo, servicios de carrito/orden).

### En progreso

1. Refuerzo de panel administrativo con métricas operativas.
2. Mayor profundidad en visualización de mapa (ruta interactiva en interfaz).
3. Cobertura de pruebas automatizadas por módulo.

## 🗺️ Roadmap de Integración

### Fase 1 (base funcional) ✅

- Branding + landing + autenticación + catálogo + carrito + checkout + pedidos + tracking básico.

### Fase 2 (consolidación operativa) 🚧

- Integración visual de mapa en vivo en tracking.
- Estados de pedido más guiados (workflow operativo).
- Mejoras de panel cliente y motorizado con indicadores.

### Fase 3 (calidad y demostración final) 📅

- Suite de tests (unitarios e integración).
- Hardening de validaciones de negocio.
- Evidencias de rendimiento y usabilidad para exposición.

## 🧪 Cómo Demostrar que NovaGo es Diferente

Para la sustentación, recomendamos mostrar evidencias concretas:

1. **Tiempo y trazabilidad**: desde creación de pedido hasta entrega con eventos visibles.
2. **Consistencia de stock**: prueba de reducción de inventario al confirmar pedido.
3. **Flujo por roles**: cliente, motorizado y admin con vistas y permisos distintos.
4. **UX coherente**: tema claro/oscuro, diseño responsive y rutas funcionales.
5. **Mantenibilidad**: separación de vistas, forms, urls y servicios para evolución sencilla.

## Características

### Para Clientes

- Catálogo de productos con stock en tiempo real
- Carrito de compras
- Sistema de pagos (transferencia/tarjeta)
- Seguimiento GPS del motorizado
- Historial de pedidos

### Para Motorizados

- Lista de pedidos asignados
- Compartir ubicación en tiempo real
- Actualizar estado de entregas

### Panel Administrativo

- Gestión de usuarios
- Control de stock
- Gestión de pagos
- Reportes básicos

## Tecnologías

- **Backend**: Python 3.13 + Django 6.x
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de Datos**: SQLite (desarrollo)
- **Control de Versiones**: Git + GitHub
- **Mapas**: tracking GPS propio + integración de mapa interactivo (Leaflet.js planificado para vista avanzada)

## Instalación

### Prerrequisitos

- Python 3.8 o superior
- Git instalado
- Navegador web moderno

### Pasos de Instalación

1. **Clonar el repositorio**

```bash
git clone <URL-del-repositorio>
cd delivery_system
```

1. **Crear y activar entorno virtual**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

1. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

1. **Ejecutar migraciones**

```bash
python manage.py makemigrations
python manage.py migrate
```

1. **Crear superusuario**

```bash
python manage.py createsuperuser
```

1. **Ejecutar servidor de desarrollo**

```bash
python manage.py runserver
```

1. **Acceder a la aplicación**

- Frontend: <http://localhost:8000>
- Admin: <http://localhost:8000/admin>

## Conceptos de Git Aplicados

Este proyecto está diseñado para demostrar los conceptos de la **Primera Unidad** del curso:

### 1. Introducción al Control de Versiones

- **Control de Versiones**: Sistema que registra cambios en archivos a lo largo del tiempo
- **Principios Básicos**: Trazabilidad, colaboración, respaldo, reversión
- **Git**: Sistema distribuido de control de versiones

### 2. Instalación y Configuración

```bash
# Configuración inicial de Git
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# Ver configuración
git config --list
```

### 3. Comandos Básicos

```bash
# Inicializar repositorio
git init

# Ver estado
git status

# Agregar archivos al staging area
git add archivo.py
git add .

# Hacer commit
git commit -m "Descripción del cambio"

# Ver historial
git log
git log --oneline
git log --graph --oneline --all

# Ver diferencias
git diff
```

### 4. Manejo de Repositorios y Ramas (Branching)

#### Concepto de Ramas

Las ramas permiten trabajar en diferentes funcionalidades sin afectar el código principal.

```bash
# Listar ramas
git branch

# Crear nueva rama
git branch nombre-rama

# Cambiar de rama
git checkout nombre-rama
# O en versiones modernas
git switch nombre-rama

# Crear y cambiar a nueva rama
git checkout -b feature/nueva-funcionalidad
```

#### Estrategia de Ramas en este Proyecto

``
main (producción)
  └── develop (desarrollo)
        ├── feature/usuarios
        ├── feature/productos
        ├── feature/pedidos
        ├── feature/pagos
        └── feature/gps-tracking
``

### 5. Estrategias de Ramificación y Fusión

#### Git Flow Simplificado

- **main**: Código en producción (estable)
- **develop**: Integración de desarrollo
- **feature/***: Nuevas funcionalidades
- **hotfix/***: Correcciones urgentes

#### Fusión de Ramas (Merge)

```bash
# Cambiar a la rama destino
git checkout develop

# Fusionar rama feature
git merge feature/usuarios

# Si todo está bien, eliminar rama feature
git branch -d feature/usuarios
```

### 6. Resolver Conflictos

#### ¿Qué es un conflicto?

Ocurre cuando dos ramas modifican las mismas líneas de código.

#### Ejemplo de Conflicto

```python
<<<<<<< HEAD
def calcular_total(items):
    return sum(item.precio for item in items)
=======
def calcular_total(items):
    return sum(item.precio * item.cantidad for item in items)
>>>>>>> feature/carrito
```

#### Resolver Conflictos

1. Abrir el archivo con conflicto
2. Editar manualmente y elegir qué código mantener
3. Eliminar los marcadores (`<<<<<<<`, `=======`, `>>>>>>>`)
4. Agregar y hacer commit:

```bash
git add archivo_resuelto.py
git commit -m "Resuelve conflicto en cálculo de total"
```

### 7. Colaboración con Repositorios Remotos

```bash
# Agregar repositorio remoto
git remote add origin <URL-repositorio>

# Ver remotos configurados
git remote -v

# Subir cambios (push)
git push origin main
git push origin develop

# Descargar cambios (pull)
git pull origin main

# Descargar sin fusionar (fetch)
git fetch origin
```

### 8. Sistema de Control de Versiones en la Nube

#### GitHub/GitLab/Bitbucket

- Hosting de repositorios
- Colaboración en equipo
- Issues y Project Management
- CI/CD Integration

```bash
# Clonar repositorio existente
git clone <URL-repositorio>

# Ver información del remoto
git remote show origin
```

### 9. Trabajo Colaborativo

#### Buenas Prácticas

- Commits pequeños y frecuentes
- Mensajes de commit descriptivos
- Pull antes de Push
- Crear rama para cada funcionalidad
- Code review antes de merge

#### Formato de Mensajes de Commit

``
tipo(alcance): descripción breve

Descripción detallada (opcional)

Ejemplos:
feat(productos): agregar filtro por categoría
fix(pagos): corregir validación de tarjeta
docs(readme): actualizar instrucciones de instalación
style(templates): mejorar diseño responsive
refactor(models): optimizar queries de productos
test(orders): agregar tests para carrito
``

### 10. Pull Requests (Solicitudes de Extracción)

#### ¿Qué es un Pull Request?

Solicitud para fusionar cambios de una rama a otra, con revisión de código.

#### Flujo de Pull Request

1. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Hacer commits: `git commit -m "Implementar funcionalidad"`
3. Push a remoto: `git push origin feature/nueva-funcionalidad`
4. Crear PR en GitHub/GitLab
5. Code Review por el equipo
6. Resolver comentarios y conflictos
7. Merge a develop/main

#### Plantilla de Pull Request

```markdown
## Descripción
Breve descripción de los cambios

## Tipo de cambio
- [ ] Nueva funcionalidad
- [ ] Corrección de bug
- [ ] Refactorización
- [ ] Documentación

## Checklist
- [ ] El código sigue las convenciones del proyecto
- [ ] Se agregaron/actualizaron tests
- [ ] Se actualizó la documentación
- [ ] Los cambios no rompen funcionalidad existente
```

### 11. Merge Conflicts y Release

#### Prevenir Conflictos

```bash
# Actualizar rama feature con cambios de develop
git checkout feature/mi-rama
git pull origin develop
# Resolver conflictos si existen
git push origin feature/mi-rama
```

#### Proceso de Release

```bash
# Crear tag para versión
git tag -a v1.0.0 -m "Primera versión estable"

# Subir tag
git push origin v1.0.0

# Ver tags
git tag
```

## Estructura del Proyecto

``
delivery_system/
├── config/                     # Configuración Django
│   ├── __init__.py
│   ├── settings.py            # Configuración principal
│   ├── urls.py                # URLs principales
│   └── wsgi.py
├── apps/                      # Aplicaciones del proyecto
│   ├── users/                 # Gestión de usuarios
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── forms.py
│   ├── products/              # Catálogo y stock
│   ├── orders/                # Pedidos
│   ├── payments/              # Pagos
│   └── tracking/              # GPS tracking
├── static/                    # Archivos estáticos
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                 # Templates HTML
│   ├── base.html
│   ├── navbar.html
│   └── footer.html
├── media/                     # Archivos subidos
├── manage.py                  # Script de gestión Django
├── requirements.txt           # Dependencias
├── .gitignore                # Archivos ignorados por Git
└── README.md                 # Este archivo
``

## Comandos Útiles

### Django

```bash
# Crear nueva app
python manage.py startapp nombre_app

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Colectar archivos estáticos
python manage.py collectstatic

# Shell interactivo
python manage.py shell
```

### Git - Comandos Comunes

```bash
# Ver estado
git status

# Ver ramas
git branch -a

# Ver historial gráfico
git log --graph --oneline --all --decorate

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer cambios en archivo
git checkout -- archivo.py

# Ver diferencias entre ramas
git diff develop..main
```

## Equipo de Desarrollo

- **Miembro 1**: Feature/Usuarios y Autenticación
- **Miembro 2**: Feature/Productos y Stock
- **Miembro 3**: Feature/Pedidos y Carrito
- **Miembro 4**: Feature/Pagos
- **Miembro 5**: Feature/GPS Tracking

## Convenciones del Proyecto

### Nombres de Ramas

- `main` - Producción
- `develop` - Desarrollo
- `feature/nombre-descriptivo` - Nueva funcionalidad
- `hotfix/nombre-bug` - Corrección urgente
- `release/v1.0.0` - Preparación de release

### Commits

- Usar mensajes en español
- Formato: `tipo(alcance): descripción`
- Commits atómicos (un cambio lógico por commit)

### Pull Requests

- Título descriptivo
- Descripción detallada de cambios
- Asignar reviewers
- Vincular issues relacionados

## Reportar Bugs

Usar el sistema de Issues de GitHub con la plantilla:

```markdown
**Descripción del bug**
Descripción clara del problema

**Pasos para reproducir**
1. Ir a '...'
2. Hacer clic en '...'
3. Ver error

**Comportamiento esperado**
Lo que debería pasar

**Capturas de pantalla**
Si aplica
```

## Licencia

Este proyecto es con fines educativos para el curso de Herramientas de Desarrollo.

## Conceptos Aprendidos

- Control de versiones con Git
- Branching y merging
- Resolución de conflictos
- Trabajo colaborativo con repositorios remotos
- Pull requests y code review
- Git Flow workflow
- Desarrollo web con Django
- Trabajo en equipo

---

**Nota**: Este README es un documento vivo que se actualiza conforme avanza el proyecto.
