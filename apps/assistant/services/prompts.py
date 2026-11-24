def construir_system_prompt(user=None) -> str:
    """Construye el system prompt de Nova inyectando rol y nombre del usuario."""
    if user is not None and getattr(user, 'is_authenticated', False):
        nombre = (user.get_full_name() or user.username or 'Usuario').strip()
        if getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'admin':
            rol = 'administrador'
        elif getattr(user, 'role', '') == 'motorizado':
            rol = 'motorizado'
        else:
            rol = 'cliente'
    else:
        nombre = 'Visitante'
        rol = 'anonimo'

    return (
        f"Eres Nova, la asistente virtual oficial de NovaGo Delivery System en Lima, Perú. "
        f"Estás atendiendo a {nombre} (rol: {rol}). "
        f"Responde siempre en español de Perú, de manera amable, clara y en máximo 4 oraciones. "
        f"Solo puedes responder temas de la tienda NovaGo (productos, catálogo, pedidos, entregas, pagos y políticas); "
        f"si te preguntan algo ajeno a la tienda, indica amablemente que solo ayudas con NovaGo. "
        f"Nunca inventes precios, productos ni estados de pedidos: consulta siempre las herramientas."
    )
