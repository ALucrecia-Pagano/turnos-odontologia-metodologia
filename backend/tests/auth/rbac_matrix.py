"""Copia literal e independiente de la tabla "Matriz RBAC" de design.md (C-19).

No importa `app.auth.permissions`: un cambio en el código no arrastra al test.
`docs/evidencias/matriz-C-19.py` compara esta copia contra design.md, celda por celda.
"""

from dataclasses import dataclass

DENIED = "—"
ALL = "todos"
OWN = "propio"
ROLES = ("odontologo", "recepcion", "administrador")


@dataclass(frozen=True)
class MatrixRow:
    number: int
    resource: str
    action: str
    odontologo: str
    recepcion: str
    administrador: str
    message: str

    def cell(self, role: str) -> str:
        return {
            "odontologo": self.odontologo,
            "recepcion": self.recepcion,
            "administrador": self.administrador,
        }[role]


MATRIX: tuple[MatrixRow, ...] = (
    MatrixRow(1, "APPOINTMENT", "CREATE", DENIED, ALL, ALL, "dar turnos"),
    MatrixRow(2, "APPOINTMENT", "READ_AGENDA", ALL, ALL, ALL, "leer la agenda"),
    MatrixRow(3, "APPOINTMENT", "RESCHEDULE", DENIED, ALL, ALL, "reprogramar turnos"),
    MatrixRow(4, "APPOINTMENT", "CANCEL", DENIED, ALL, ALL, "cancelar turnos"),
    MatrixRow(5, "APPOINTMENT", "CHANGE_STATUS", OWN, ALL, ALL, "cambiar el estado de turnos"),
    MatrixRow(6, "APPOINTMENT_HISTORY", "READ", OWN, ALL, ALL, "leer el historial de turnos"),
    MatrixRow(7, "WORKING_HOURS", "CREATE", OWN, DENIED, ALL, "crear horarios"),
    MatrixRow(8, "WORKING_HOURS", "READ", OWN, ALL, ALL, "leer horarios"),
    MatrixRow(9, "WORKING_HOURS", "UPDATE", OWN, DENIED, ALL, "actualizar horarios"),
    MatrixRow(10, "WORKING_HOURS", "DELETE", DENIED, DENIED, ALL, "borrar horarios"),
    MatrixRow(11, "BLOCK", "CREATE", OWN, DENIED, ALL, "crear bloqueos"),
    MatrixRow(12, "BLOCK", "READ", OWN, ALL, ALL, "leer bloqueos"),
    MatrixRow(13, "BLOCK", "UPDATE", OWN, DENIED, ALL, "actualizar bloqueos"),
    MatrixRow(14, "BLOCK", "DELETE", OWN, DENIED, ALL, "borrar bloqueos"),
    MatrixRow(15, "PROFESSIONAL", "CREATE", DENIED, DENIED, ALL, "crear profesionales"),
    MatrixRow(16, "PROFESSIONAL", "READ", ALL, ALL, ALL, "leer profesionales"),
    MatrixRow(17, "PROFESSIONAL", "UPDATE", DENIED, DENIED, ALL, "actualizar profesionales"),
    MatrixRow(18, "PROFESSIONAL", "DELETE", DENIED, DENIED, ALL, "borrar profesionales"),
    MatrixRow(19, "CHAIR", "CREATE", DENIED, DENIED, ALL, "crear sillones"),
    MatrixRow(20, "CHAIR", "READ", ALL, ALL, ALL, "leer sillones"),
    MatrixRow(21, "CHAIR", "UPDATE", DENIED, DENIED, ALL, "actualizar sillones"),
    MatrixRow(22, "CHAIR", "DELETE", DENIED, DENIED, ALL, "borrar sillones"),
    MatrixRow(23, "SERVICE", "CREATE", DENIED, DENIED, ALL, "crear prestaciones"),
    MatrixRow(24, "SERVICE", "READ", ALL, ALL, ALL, "leer prestaciones"),
    MatrixRow(25, "SERVICE", "UPDATE", DENIED, DENIED, ALL, "actualizar prestaciones"),
    MatrixRow(26, "SERVICE", "DELETE", DENIED, DENIED, ALL, "borrar prestaciones"),
    MatrixRow(27, "PATIENT", "CREATE", DENIED, ALL, ALL, "crear pacientes"),
    MatrixRow(28, "PATIENT", "READ", ALL, ALL, ALL, "leer pacientes"),
    MatrixRow(29, "PATIENT", "UPDATE", DENIED, ALL, ALL, "actualizar pacientes"),
    MatrixRow(30, "PATIENT", "DELETE", DENIED, DENIED, DENIED, "borrar pacientes"),
    MatrixRow(31, "USER", "CREATE", DENIED, DENIED, ALL, "crear usuarios"),
    MatrixRow(32, "USER", "READ", DENIED, DENIED, ALL, "leer usuarios"),
    MatrixRow(33, "USER", "UPDATE", DENIED, DENIED, ALL, "actualizar usuarios"),
    MatrixRow(34, "USER", "DELETE", DENIED, DENIED, ALL, "borrar usuarios"),
)
