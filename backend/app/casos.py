"""Casos de ejemplo: quién llega a urgencias, a qué clínica, quién lo atiende y por qué.

Los datos clínicos de cada paciente están en las fuentes (`app.sources`); aquí solo va lo
que pasa hoy en urgencias: el motivo de consulta (va al Encounter del RDA) y la nota que
el visor sugiere al médico después de revisar la historia en Hilo Clínico.
"""

from dataclasses import dataclass

from app.mpi.indice import normalizar_documento


@dataclass(frozen=True)
class Caso:
    documento: str
    nombre: str
    medico: str  # id en app.actores.MEDICOS
    motivo: str
    nota: str


CASOS: list[Caso] = [
    Caso(
        "1032456789", "Mariana Sofía López Castro", "prac-0192",
        "Dolor abdominal y fiebre",
        "Antecedentes revisados en Hilo Clínico: alergia a la penicilina y exámenes del "
        "7 de noviembre. No se repiten hemograma ni proteína C reactiva.",
    ),
    Caso(
        "79845120", "Jorge Eliecer Pardo Ruiz", "prac-0192",
        "Dolor torácico",
        "Antecedentes revisados en Hilo Clínico: solo hay datos de afiliación en la EPS "
        "(régimen subsidiado). Sin alergias ni exámenes registrados en la red.",
    ),
    Caso(
        "1017234567", "Carlos Andrés Gómez Restrepo", "prac-0347",
        "Hiperglucemia y malestar general",
        "Antecedentes revisados en Hilo Clínico: diabetes tipo 2 en tratamiento con metformina, "
        "alergia a las sulfonamidas y hemoglobina glicosilada de 8,4 % del 5 de noviembre. "
        "No se repite la hemoglobina glicosilada.",
    ),
    Caso(
        "52987654", "Luisa Fernanda Rojas Herrera", "prac-0418",
        "Cefalea intensa y cifras tensionales elevadas",
        "Antecedentes revisados en Hilo Clínico: hipertensión en tratamiento con losartán y "
        "alergia grave a los AINE (angioedema). No se formula ibuprofeno. El ecocardiograma "
        "ya está autorizado por la EPS.",
    ),
    Caso(
        "1144056789", "Andrés Felipe Martínez Ospina", "prac-0611",
        "Trauma en rodilla derecha por caída de moto",
        "Antecedentes revisados en Hilo Clínico: hemograma normal del 28 de octubre y "
        "resonancia de rodilla ya autorizada por la EPS. Sin alergias registradas en la red.",
    ),
    Caso(
        "1000345678", "Valentina Ruiz Quintero", "prac-0735",
        "Cefalea intensa con fotofobia",
        "Antecedentes revisados en Hilo Clínico: migraña en manejo con acetaminofén, alergia "
        "al látex (usar guantes de nitrilo) y anemia leve en el hemograma del 10 de noviembre.",
    ),
    Caso(
        "19456321", "Héctor Julio Cárdenas Pinzón", "prac-0523",
        "Disnea progresiva y tos con expectoración",
        "Antecedentes revisados en Hilo Clínico: EPOC con exacerbación el 30 de octubre, "
        "alergia grave a la aspirina (broncoespasmo) y gases arteriales del 31 de octubre con "
        "acidosis respiratoria. Se comparan con los gases de ingreso.",
    ),
]


def caso_de(documento: str) -> Caso | None:
    doc = normalizar_documento(documento)
    return next((c for c in CASOS if c.documento == doc), None)
