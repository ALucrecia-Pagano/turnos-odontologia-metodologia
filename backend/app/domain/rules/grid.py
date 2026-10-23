"""Granularidad de la agenda, compartida por la duracion y el inicio del turno.

SU-02 pide una "constante configurable" (en singular): si la granularidad cambia, cambia
en un solo lugar para las dos reglas.
"""

from typing import Final

GRID_STEP_MIN: Final = 5
"""Paso de la grilla de la agenda en minutos (SU-02)."""
