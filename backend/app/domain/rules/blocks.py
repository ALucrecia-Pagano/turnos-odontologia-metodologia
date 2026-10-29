"""Reglas de los bloqueos de agenda de los profesionales (RN-AG-05, RN-DI-03, RN-DI-04).

Un bloqueo es un intervalo semiabierto `[inicio, fin)` de instantes en UTC (DD-07) que
puede durar varios dias. Las reglas devuelven violaciones y nunca lanzan excepciones por
una regla de negocio.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Final
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain.intervals import format_local_date_time, format_local_time
from app.domain.model import Appointment, Block
from app.domain.rules.overlap import OCCUPYING_STATUSES
from app.domain.violations import Violation, ViolationCode

_INVALID_BLOCK_MESSAGE: Final = "El bloqueo no es válido: el inicio debe ser anterior al fin."


def validate_block(block: Block) -> list[Violation]:
    """Valida un bloqueo que carga el usuario (RN-DI-03; US-011 CA-1 y CA-2).

    `Block` no valida el orden al construirse: un bloqueo con `inicio >= fin` se puede
    armar y esta funcion lo rechaza con un resultado tipado. No exige la grilla de 5
    minutos ni compara con otros bloqueos (pueden pisarse).

    Args:
        block: Bloqueo a validar.

    Returns:
        Una `INVALID_BLOCK` sin ids en conflicto si `inicio >= fin`; si no, lista vacia.
    """
    if block.start_at >= block.end_at:
        return [Violation(code=ViolationCode.INVALID_BLOCK, message=_INVALID_BLOCK_MESSAGE)]
    return []


def _overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    """Indica si dos intervalos semiabiertos de instantes se solapan (DD-07).

    Compara los instantes directamente, sin `Interval`, para no lanzar con un bloqueo
    invalido: si `inicio >= fin`, el bloqueo nunca se solapa con nada.
    """
    return start_a < end_b and start_b < end_a


def _overlapping_blocks(
    professional_id: UUID, start_at: datetime, end_at: datetime, blocks: Sequence[Block]
) -> list[Block]:
    """Bloqueos del profesional que se solapan con `[start_at, end_at)`, en orden estable.

    El orden es `(start_at, str(id))`: el id solo desempata dos bloqueos con el mismo
    inicio, para que el resultado no dependa del orden de la lista recibida.
    """
    return sorted(
        (
            block
            for block in blocks
            if block.professional_id == professional_id
            and _overlaps(start_at, end_at, block.start_at, block.end_at)
        ),
        key=lambda block: (block.start_at, str(block.id)),
    )


def check_blocks(
    professional_id: UUID,
    start_at: datetime,
    end_at: datetime,
    blocks: Sequence[Block],
    tz: ZoneInfo,
) -> list[Violation]:
    """Una violacion `BLOCKED_TIME` por cada bloqueo del profesional que pisa el turno (RN-AG-05).

    El dominio elige los bloqueos del profesional: el llamador no necesita filtrarlos.
    Turno y bloqueo se comparan como instantes UTC, asi que un bloqueo de varios dias no
    necesita tratamiento especial; la hora local solo se usa en el mensaje. Los bloqueos
    se suponen validos (`validate_block`); uno con `inicio >= fin` se ignora.

    Args:
        professional_id: Profesional del turno.
        start_at: Inicio del turno (instante con zona horaria).
        end_at: Fin del turno (instante con zona horaria).
        blocks: Bloqueos de uno o varios profesionales.
        tz: Zona horaria en la que se muestran las horas del mensaje.

    Returns:
        Violaciones ordenadas por inicio del bloqueo, con `conflicting_block_id`; vacia si
        el turno no pisa ningun bloqueo.
    """
    return [
        Violation(
            code=ViolationCode.BLOCKED_TIME,
            message=_blocked_message(start_at, end_at, block, tz),
            conflicting_block_id=block.id,
        )
        for block in _overlapping_blocks(professional_id, start_at, end_at, blocks)
    ]


def _blocked_message(start_at: datetime, end_at: datetime, block: Block, tz: ZoneInfo) -> str:
    """Arma el mensaje de `BLOCKED_TIME`: el turno y el bloqueo en hora local.

    El bloqueo va con fecha porque puede durar varios dias. El motivo va como oracion
    aparte solo si tiene algo mas que espacios; se muestra tal como se cargo.
    """
    message = (
        f"El turno de {format_local_time(start_at, tz)} a {format_local_time(end_at, tz)} "
        f"(hora local) se superpone con el bloqueo {block.id} del profesional, del "
        f"{format_local_date_time(block.start_at, tz)} al "
        f"{format_local_date_time(block.end_at, tz)} (hora local)."
    )
    if block.reason is not None and block.reason.strip():
        message += f" Motivo: {block.reason}."
    return message


def appointments_affected_by_block(
    block: Block, appointments: Sequence[Appointment]
) -> list[Appointment]:
    """Turnos existentes que pisa un bloqueo nuevo (RN-DI-04, SU-05; US-011 CA-3).

    Crear el bloqueo no cancela ni mueve esos turnos: se devuelven los mismos objetos,
    sin cambios, para que recepcion los reprograme. Cuentan los del mismo profesional en
    un estado que ocupa agenda (`OCCUPYING_STATUSES`, RN-AG-08) que se solapan con el
    bloqueo (semiabiertos). El llamador valida antes el bloqueo con `validate_block`; con
    un bloqueo de `inicio >= fin` el resultado es vacio, sin excepcion.

    Args:
        block: Bloqueo nuevo.
        appointments: Turnos existentes, sin filtrar.

    Returns:
        Los turnos afectados, ordenados por `(start_at, str(id))`; vacia si no hay.
    """
    return sorted(
        (
            appointment
            for appointment in appointments
            if appointment.professional_id == block.professional_id
            and appointment.status in OCCUPYING_STATUSES
            and _overlaps(appointment.start_at, appointment.end_at, block.start_at, block.end_at)
        ),
        key=lambda appointment: (appointment.start_at, str(appointment.id)),
    )
