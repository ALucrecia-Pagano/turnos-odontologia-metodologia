"""Nombre del profesional o del sillon como sujeto de un mensaje de conflicto (US-006 CA-3)."""


def subject_name(name: str, generic: str) -> str:
    """Devuelve el nombre recortado, o el sustantivo generico si esta vacio o en blanco.

    El nombre se muestra sin los espacios del principio ni del final, para que el mensaje
    no tenga espacios dobles; la entidad conserva el valor tal como se cargo. El generico lo
    elige el llamador segun el lugar en la oracion: "El profesional" o "El sillon" al
    principio, "el profesional" en minuscula despues de dos puntos.

    Args:
        name: Nombre de la entidad, tal como se cargo (puede estar vacio o en blanco).
        generic: Sustantivo que reemplaza al nombre cuando no hay nada que mostrar.

    Returns:
        `name` sin espacios alrededor si tiene algo mas que espacios; si no, `generic`.
    """
    stripped = name.strip()
    return stripped if stripped else generic
