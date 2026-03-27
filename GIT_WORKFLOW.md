# 🔀 Guía de Flujo de Trabajo con Git

Este documento explica el flujo de trabajo con Git que usaremos en el proyecto.

## 📌 Conceptos Básicos de Git

### ¿Qué es Git?

Git es un **sistema de control de versiones distribuido** que permite:

- Rastrear cambios en el código
- Colaborar con múltiples desarrolladores
- Revertir cambios si algo sale mal
- Mantener un historial completo del proyecto

### ¿Por qué usar Git?

- ✅ **Trazabilidad**: Saber quién hizo qué y cuándo
- ✅ **Colaboración**: Trabajar en equipo sin pisarse los cambios
- ✅ **Respaldo**: Tu código está seguro
- ✅ **Experimentación**: Probar cosas nuevas sin miedo

## 🌳 Estrategia de Ramas (Branching Strategy)

### Estructura de Ramas

``
main (producción - código estable)
  │
  └── develop (integración - desarrollo activo)
        ├── feature/usuarios
        ├── feature/productos
        ├── feature/pedidos
        ├── feature/pagos
        └── feature/gps-tracking
``

### Tipos de Ramas

#### 1. `main` - Rama Principal

- Código en **producción**
- Siempre debe estar **funcional y estable**
- Solo se hace merge desde `develop` cuando una versión está lista
- **NUNCA** hacer commits directos en `main`

#### 2. `develop` - Rama de Desarrollo

- Rama de **integración**
- Aquí se fusionan todas las features
- Base para crear nuevas features
- Debe estar **mayormente funcional**

#### 3. `feature/*` - Ramas de Funcionalidad

- Una rama por cada nueva funcionalidad
- Se crean desde `develop`
- Nomenclatura: `feature/nombre-descriptivo`
- Ejemplos:
  - `feature/login-usuarios`
  - `feature/catalogo-productos`
  - `feature/carrito-compras`
  - `feature/sistema-pagos`
  - `feature/rastreo-gps`

#### 4. `hotfix/*` - Correcciones Urgentes

- Para bugs críticos en producción
- Se crean desde `main`
- Se fusionan a `main` Y `develop`
- Ejemplo: `hotfix/corregir-pago`

## 📋 Flujo de Trabajo Completo

### Paso 1: Actualizar tu repositorio local

```bash
# Asegúrate de estar en develop
git checkout develop

# Descarga los últimos cambios
git pull origin develop
```

### Paso 2: Crear una rama feature

```bash
# Crear y cambiar a nueva rama
git checkout -b feature/mi-funcionalidad

# Verificar en qué rama estás
git branch
```

### Paso 3: Hacer cambios y commits

```bash
# Ver archivos modificados
git status

# Ver diferencias específicas
git diff archivo.py

# Agregar archivos al staging area
git add archivo1.py archivo2.py
# O agregar todos
git add .

# Hacer commit con mensaje descriptivo
git commit -m "feat(usuarios): agregar formulario de registro"

# Commits adicionales según necesites
git commit -m "feat(usuarios): validar campos del formulario"
git commit -m "feat(usuarios): agregar mensajes de error"
```

### Paso 4: Subir tu rama al repositorio remoto

```bash
# Primera vez (crear rama remota)
git push -u origin feature/mi-funcionalidad

# Siguientes veces
git push
```

### Paso 5: Crear Pull Request en GitHub

1. Ir a GitHub → Tu repositorio
2. Verás un mensaje "Compare & pull request"
3. Click en el botón
4. Completar información:
   - **Título**: Descripción breve
   - **Descripción**: Detalle de cambios
   - **Reviewers**: Asignar compañeros para revisión
5. Click "Create pull request"

### Paso 6: Code Review

El equipo revisa tu código y puede:

- ✅ Aprobar el PR
- 💬 Dejar comentarios
- ❌ Solicitar cambios

Si solicitan cambios:

```bash
# Hacer las correcciones
git add .
git commit -m "fix: aplicar sugerencias del code review"
git push
# El PR se actualiza automáticamente
```

### Paso 7: Merge a Develop

Una vez aprobado:

1. Asegurarse que no hay conflictos
2. Click "Merge pull request" en GitHub
3. Click "Confirm merge"
4. Opcionalmente: Eliminar la rama feature

O desde línea de comandos:

```bash
# Cambiar a develop
git checkout develop

# Fusionar tu feature
git merge feature/mi-funcionalidad

# Subir a remoto
git push origin develop

# Eliminar rama local (opcional)
git branch -d feature/mi-funcionalidad

# Eliminar rama remota (opcional)
git push origin --delete feature/mi-funcionalidad
```

## 🔥 Resolver Conflictos

### ¿Cuándo ocurren conflictos?

Cuando dos personas modifican **las mismas líneas** del mismo archivo.

### Ejemplo de Conflicto

```python
<<<<<<< HEAD (tu código)
def calcular_total(items):
    return sum(item.precio * item.cantidad for item in items)
=======
def calcular_total(items, descuento=0):
    subtotal = sum(item.precio * item.cantidad for item in items)
    return subtotal - descuento
>>>>>>> develop (código de develop)
```

### Pasos para Resolver

```bash
# 1. Intentar merge
git merge develop
# Git te avisa de conflictos

# 2. Ver archivos con conflictos
git status

# 3. Abrir cada archivo y editar manualmente
# Decidir qué código mantener
# Eliminar los marcadores <<<<<< ====== >>>>>>

# 4. Código resuelto (ejemplo)
def calcular_total(items, descuento=0):
    subtotal = sum(item.precio * item.cantidad for item in items)
    return subtotal - descuento

# 5. Marcar como resuelto
git add archivo_resuelto.py

# 6. Completar el merge
git commit -m "merge: resolver conflictos con develop"

# 7. Subir cambios
git push
```

### Prevenir Conflictos

```bash
# Actualizar tu rama feature frecuentemente
git checkout feature/mi-rama
git pull origin develop

# Si hay conflictos, resolverlos inmediatamente
```

## 📝 Convenciones de Commits

### Formato Estándar

``
tipo(alcance): descripción breve

Descripción detallada (opcional)
``

### Tipos de Commits

- **feat**: Nueva funcionalidad

  ```bash
  git commit -m "feat(productos): agregar filtro por categoría"
  ```

- **fix**: Corrección de bug

  ```bash
  git commit -m "fix(carrito): corregir cálculo de subtotal"
  ```

- **docs**: Documentación

  ```bash
  git commit -m "docs(readme): actualizar instrucciones de instalación"
  ```

- **style**: Cambios de formato (sin afectar código)

  ```bash
  git commit -m "style(templates): mejorar indentación HTML"
  ```

- **refactor**: Refactorización de código

  ```bash
  git commit -m "refactor(models): optimizar queries de productos"
  ```

- **test**: Agregar o modificar tests

  ```bash
  git commit -m "test(orders): agregar tests para carrito"
  ```

- **chore**: Tareas de mantenimiento

  ```bash
  git commit -m "chore(deps): actualizar Django a 4.2.11"
  ```

### Ejemplos Completos

✅ **Buenos commits**:

```bash
git commit -m "feat(usuarios): implementar registro con validación de email"
git commit -m "fix(pagos): corregir error en procesamiento de tarjeta"
git commit -m "docs(api): agregar documentación de endpoints"
```

❌ **Malos commits**:

```bash
git commit -m "cambios"
git commit -m "fix"
git commit -m "asdfasdf"
git commit -m "ahora si funciona"
```

## 🎯 Comandos Git Esenciales

### Básicos

```bash
# Ver estado
git status

# Ver historial
git log
git log --oneline
git log --graph --oneline --all

# Ver diferencias
git diff
git diff archivo.py
git diff --staged

# Ver ramas
git branch
git branch -a  # incluye remotas
```

### Trabajar con Ramas

```bash
# Crear rama
git branch nombre-rama

# Cambiar de rama
git checkout nombre-rama
git switch nombre-rama  # versión moderna

# Crear y cambiar en un solo comando
git checkout -b nombre-rama

# Eliminar rama
git branch -d nombre-rama  # solo si está mergeada
git branch -D nombre-rama  # forzar eliminación
```

### Sincronizar con Remoto

```bash
# Clonar repositorio
git clone https://github.com/usuario/repo.git

# Ver remotos
git remote -v

# Descargar cambios (sin fusionar)
git fetch origin

# Descargar y fusionar
git pull origin develop

# Subir cambios
git push origin rama
```

### Deshacer Cambios

```bash
# Deshacer cambios en archivo (no staged)
git checkout -- archivo.py
git restore archivo.py  # versión moderna

# Quitar archivo del staging area
git reset HEAD archivo.py
git restore --staged archivo.py  # versión moderna

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer último commit (eliminar cambios) ⚠️
git reset --hard HEAD~1

# Ver commit específico
git show abc123

# Revertir commit (crear nuevo commit que deshace)
git revert abc123
```

## 🎓 Ejercicios Prácticos

### Ejercicio 1: Primera Feature

1. Actualizar develop: `git checkout develop && git pull`
2. Crear rama: `git checkout -b feature/ejercicio-practica`
3. Crear archivo: `echo "# Mi primera feature" > practica.md`
4. Agregar: `git add practica.md`
5. Commit: `git commit -m "feat(docs): agregar archivo de práctica"`
6. Push: `git push -u origin feature/ejercicio-practica`

### Ejercicio 2: Resolver Conflicto Simulado

1. Crear rama desde develop
2. Modificar mismo archivo en dos ramas diferentes
3. Hacer merge y resolver conflicto
4. Completar merge con commit

### Ejercicio 3: Historial y Log

1. Ver historial: `git log --oneline`
2. Ver gráfico: `git log --graph --all --decorate`
3. Ver cambios en commit: `git show <hash>`
4. Ver diferencias entre commits: `git diff <hash1>..<hash2>`

## 🚀 Workflow del Equipo

### Asignación de Features por Miembro

| Miembro | Feature | Rama ||---------|---------|------|
| Miembro 1 | Sistema de Usuarios | `feature/usuarios` |
| Miembro 2 | Catálogo de Productos | `feature/productos` |
| Miembro 3 | Carrito y Pedidos | `feature/pedidos` |
| Miembro 4 | Sistema de Pagos | `feature/pagos` |
| Miembro 5 | Rastreo GPS | `feature/gps-tracking` |

### Reuniones y Sincronización

1. **Daily Standup** (diario/frecuente):
   - ¿Qué hice ayer?
   - ¿Qué haré hoy?
   - ¿Tengo algún bloqueador?

2. **Code Review** (al crear PR):
   - Revisar código de compañeros
   - Dar feedback constructivo
   - Aprobar cuando esté listo

3. **Merge Party** (cuando sea necesario):
   - Fusionar todas las features a develop
   - Resolver conflictos en equipo
   - Probar integración

## 🛠️ Herramientas Útiles

### GUI para Git

- **GitHub Desktop**: Interfaz gráfica simple
- **GitKraken**: Visualización avanzada
- **VS Code**: Integración nativa

### Comandos Avanzados

```bash
# Ver quién modificó cada línea
git blame archivo.py

# Buscar en el historial
git log --grep="login"

# Guardar cambios temporalmente
git stash
git stash pop

# Ver branches merged
git branch --merged
git branch --no-merged
```

## 📚 Recursos Adicionales

- [Git Book Oficial](https://git-scm.com/book/es/v2)
- [GitHub Guides](https://guides.github.com/)
- [Visualizing Git](http://git-school.github.io/visualizing-git/)
- [Learn Git Branching](https://learngitbranching.js.org/)

## ⚠️ Buenas Prácticas

### ✅ Hacer

- Commits pequeños y frecuentes
- Mensajes de commit descriptivos
- Pull antes de push
- Code review antes de merge
- Resolver conflictos inmediatamente
- Mantener las ramas actualizadas

### ❌ Evitar

- Commits gigantes con muchos cambios
- Mensajes vagos ("fix", "cambios")
- Push sin pull primero
- Merge sin revisión
- Dejar conflictos sin resolver
- Trabajar en main directamente

---

**¿Dudas?** Pregunta a tu equipo o profesor. Git es fundamental para el desarrollo moderno.
