"""Verifica la matriz B.2 leyendo las notas directamente del informe.

Para cada fila comprueba: desglose = nota x peso, total = suma del desglose,
y que el ranking (con empates compartidos) sea consistente con los totales.
Sale con codigo 1 si encuentra alguna discrepancia.
"""
import re
import sys
from decimal import Decimal
from pathlib import Path

PESOS = [Decimal(p) for p in ("0.25", "0.20", "0.15", "0.15", "0.10", "0.10", "0.05")]
INFORME = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("informe-discovery.md")
ESPERADOS = 26


def num(texto):
    return Decimal(texto.strip().replace(",", "."))


def filas_matriz(texto):
    seccion = texto.split("### B.2", 1)[1].split("### B.3", 1)[0]
    for linea in seccion.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) == 11 and re.fullmatch(r"\d+", celdas[0]):
            yield celdas


def main():
    errores = []
    filas = list(filas_matriz(INFORME.read_text(encoding="utf-8")))
    if len(filas) != ESPERADOS:
        errores.append(f"se esperaban {ESPERADOS} sistemas y la matriz tiene {len(filas)}")

    calculados = []
    for rank, producto, *resto in filas:
        notas = [int(n) for n in resto[:7]]
        desglose = [num(p) for p in resto[7].split("+")]
        total_informe = num(resto[8])
        esperado = [n * p for n, p in zip(notas, PESOS)]
        total = sum(esperado)
        if any(n < 0 or n > 5 for n in notas):
            errores.append(f"{producto}: nota fuera de rango 0-5 {notas}")
        if desglose != esperado:
            errores.append(f"{producto}: desglose {resto[7]} no coincide con notas {notas}")
        if total != total_informe:
            errores.append(f"{producto}: total informado {total_informe} != calculado {total} (notas {notas})")
        calculados.append((producto, int(rank), total))
        print(f"{producto:24} {notas} -> {total:.2f} (informe {total_informe:.2f}, puesto {rank})")

    orden = sorted(calculados, key=lambda c: -c[2])
    previo, puesto = None, 0
    for i, (producto, rank, total) in enumerate(orden, 1):
        if total != previo:
            puesto = i
        previo = total
        if rank != puesto:
            errores.append(f"{producto}: puesto informado {rank} != esperado {puesto}")
    if [c[0] for c in calculados] != [c[0] for c in orden]:
        errores.append("las filas no estan ordenadas por total descendente")

    print()
    if errores:
        print(f"FALLA: {len(errores)} discrepancia(s)")
        for e in errores:
            print(" -", e)
        sys.exit(1)
    print(f"OK: {len(filas)} sistemas verificados contra la matriz del informe, sin discrepancias")


if __name__ == "__main__":
    main()
