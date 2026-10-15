"""Datos de calendario transcritos a mano desde los documentos oficiales.

Solo lo que no se puede extraer de forma automática y fiable (los festivos
del BOE y las fiestas locales del BOPA se leen directamente de los PDF en
`limpia_calendario.py`). Cada bloque cita su documento en
`data/raw/calendario/` y el apartado de donde sale. Transcrito leyendo el
texto (`.txt` / PDF) el 2026-10-15; nada se ha deducido ni completado.

Nivel de referencia de los calendarios escolares: Educación Infantil
(2.º ciclo) y Primaria. En Asturias el BOPA da una única fecha para
Infantil, Primaria, ESO y Bachillerato (salvo el curso 2021-22, en el que
el calendario gráfico de Educastur separa Inf+Prim de ESO+Bach).
"""
from datetime import date as D

# ---------------------------------------------------------------------------
# Calendarios escolares por comunidad y curso
#   inicio / fin: primer y último día lectivo de Infantil-Primaria
#   navidad / semana_santa: periodos de vacaciones (ambos inclusive)
#   no_lectivos: "otros días no lectivos" de la norma (no incluye festivos
#                laborales, que salen del BOE, ni las fiestas locales)
#   verificado: False si la fuente no es la norma oficial publicada en boletín
# ---------------------------------------------------------------------------

ESCOLAR = {
    "ast": [
        dict(curso="2021-22", fuente="educastur_calendario_escolar_2021-22_grafico.pdf (calendario gráfico de la Consejería; el BOPA de 1-jun-2021 no se obtuvo)",
             verificado=False,
             # "Inicio de la actividad lectiva: 9 sep Inf+Prim+EE"; "Fin: 21 jun Inf+Prim+EE"
             inicio=D(2021, 9, 9), fin=D(2022, 6, 21),
             # "Vacaciones: 24 diciembre 2021 a 7 enero 2022; 11 a 15 abril 2022"
             navidad=(D(2021, 12, 24), D(2022, 1, 7)), semana_santa=(D(2022, 4, 11), D(2022, 4, 15)),
             # "Días no lectivos: 29 octubre 2021, 2 noviembre 2021, 7 diciembre 2021, 25 y 28 febrero 2022, 1 marzo 2022"
             no_lectivos=[D(2021, 10, 29), D(2021, 11, 2), D(2021, 12, 7), D(2022, 2, 25), D(2022, 2, 28), D(2022, 3, 1)]),
        dict(curso="2022-23", fuente="BOPA 25-abr-2022, cód. 2022-02717 (bopa_calendario_escolar_2022-23.pdf), anexo 2-4",
             verificado=True,
             inicio=D(2022, 9, 12), fin=D(2023, 6, 23),
             navidad=(D(2022, 12, 27), D(2023, 1, 5)), semana_santa=(D(2023, 4, 3), D(2023, 4, 11)),
             no_lectivos=[D(2022, 10, 31), D(2022, 11, 2), D(2022, 12, 5), D(2023, 2, 17), D(2023, 2, 20), D(2023, 2, 21)]),
        dict(curso="2023-24", fuente="BOPA 10-may-2023, cód. 2023-03661 (bopa_calendario_escolar_2023-24.pdf), anexo 2-4",
             verificado=True,
             inicio=D(2023, 9, 11), fin=D(2024, 6, 21),
             navidad=(D(2023, 12, 26), D(2024, 1, 5)), semana_santa=(D(2024, 3, 25), D(2024, 4, 1)),
             no_lectivos=[D(2023, 11, 2), D(2023, 11, 3), D(2023, 12, 7), D(2024, 2, 12), D(2024, 2, 13), D(2024, 5, 2), D(2024, 5, 3)]),
        dict(curso="2024-25", fuente="BOPA 30-may-2024, cód. 2024-04412 (bopa_calendario_escolar_2024-25.pdf), anexo I 2-4",
             verificado=True,
             inicio=D(2024, 9, 10), fin=D(2025, 6, 20),
             navidad=(D(2024, 12, 23), D(2025, 1, 7)), semana_santa=(D(2025, 4, 14), D(2025, 4, 20)),
             no_lectivos=[D(2024, 10, 30), D(2024, 10, 31), D(2025, 2, 28), D(2025, 3, 3), D(2025, 3, 4), D(2025, 5, 2)]),
        dict(curso="2025-26", fuente="BOPA 21-may-2025, cód. 2025-03852 (bopa_calendario_escolar_2025-26.pdf), anexo I 2-4",
             verificado=True,
             inicio=D(2025, 9, 9), fin=D(2026, 6, 19),
             navidad=(D(2025, 12, 22), D(2026, 1, 7)), semana_santa=(D(2026, 3, 30), D(2026, 4, 5)),
             no_lectivos=[D(2025, 11, 3), D(2025, 11, 4), D(2026, 2, 13), D(2026, 2, 16), D(2026, 2, 17), D(2026, 5, 4)]),
        dict(curso="2026-27", fuente="BOPA 1-jun-2026, cód. 2026-04361 (bopa_calendario_escolar_2026-27.pdf), anexo I 2-4",
             verificado=True,
             inicio=D(2026, 9, 9), fin=D(2027, 6, 23),
             navidad=(D(2026, 12, 23), D(2027, 1, 10)), semana_santa=(D(2027, 3, 22), D(2027, 3, 28)),
             no_lectivos=[D(2026, 10, 30), D(2026, 11, 3), D(2026, 11, 4), D(2027, 2, 8), D(2027, 2, 9), D(2027, 4, 30), D(2027, 5, 3)]),
    ],
    "mad": [
        dict(curso="2021-22", fuente="Orden 1734/2021, BOCM 24-jun-2021 (madrid_calendario_escolar_2021-22.pdf), 2.2.2, 4.1 y 4.2.2",
             verificado=True,
             inicio=D(2021, 9, 7), fin=D(2022, 6, 24),
             navidad=(D(2021, 12, 23), D(2022, 1, 6)), semana_santa=(D(2022, 4, 9), D(2022, 4, 17)),
             no_lectivos=[D(2021, 10, 11), D(2021, 12, 7), D(2022, 1, 7), D(2022, 2, 25), D(2022, 2, 28), D(2022, 4, 8), D(2022, 4, 18)]),
        dict(curso="2022-23", fuente="Orden 1210/2022, BOCM 23-may-2022 (madrid_calendario_escolar_2022-23.pdf), 2.2.2, 4.1 y 4.2.2",
             verificado=True,
             inicio=D(2022, 9, 7), fin=D(2023, 6, 22),
             navidad=(D(2022, 12, 23), D(2023, 1, 8)), semana_santa=(D(2023, 4, 1), D(2023, 4, 9)),
             no_lectivos=[D(2022, 10, 31), D(2022, 12, 5), D(2022, 12, 7), D(2023, 2, 24), D(2023, 2, 27), D(2023, 3, 31), D(2023, 4, 10)]),
        dict(curso="2023-24", fuente="Orden 1952/2023, BOCM 12-jun-2023 (madrid_calendario_escolar_2023-24.pdf), 2.2.2, 4.1 y 4.2.2",
             verificado=True,
             inicio=D(2023, 9, 6), fin=D(2024, 6, 21),
             navidad=(D(2023, 12, 23), D(2024, 1, 7)), semana_santa=(D(2024, 3, 23), D(2024, 3, 31)),
             no_lectivos=[D(2023, 10, 13), D(2023, 12, 7), D(2024, 2, 22), D(2024, 2, 23), D(2024, 3, 22), D(2024, 4, 1), D(2024, 5, 3)]),
        dict(curso="2024-25", fuente="Orden 1177/2024, BOCM 19-abr-2024 (madrid_calendario_escolar_2024-25.pdf), 2.2.2, 5.1 y 5.2.2",
             verificado=True,
             inicio=D(2024, 9, 9), fin=D(2025, 6, 20),
             navidad=(D(2024, 12, 21), D(2025, 1, 6)), semana_santa=(D(2025, 4, 12), D(2025, 4, 20)),
             no_lectivos=[D(2025, 1, 7), D(2025, 2, 28), D(2025, 3, 3), D(2025, 4, 11), D(2025, 4, 21)]),
        dict(curso="2025-26", fuente="Orden 1476/2025, BOCM 13-may-2025 (madrid_calendario_escolar_2025-26.pdf), 2.2.2, 5.1 y 5.2.2",
             verificado=True,
             inicio=D(2025, 9, 8), fin=D(2026, 6, 19),
             navidad=(D(2025, 12, 20), D(2026, 1, 6)), semana_santa=(D(2026, 3, 28), D(2026, 4, 5)),
             no_lectivos=[D(2025, 10, 13), D(2025, 11, 3), D(2026, 1, 7), D(2026, 3, 27), D(2026, 4, 6)]),
        dict(curso="2026-27", fuente="Orden 2034/2026, BOCM 4-jun-2026 (madrid_calendario_escolar_2026-27.pdf), 2.2.2, 5.1 y 5.2.2",
             verificado=True,
             inicio=D(2026, 9, 7), fin=D(2027, 6, 18),
             navidad=(D(2026, 12, 23), D(2027, 1, 6)), semana_santa=(D(2027, 3, 20), D(2027, 3, 28)),
             no_lectivos=[D(2027, 1, 7), D(2027, 1, 8), D(2027, 2, 12), D(2027, 2, 15), D(2027, 3, 19), D(2027, 3, 29)]),
    ],
    # Castilla y León: las vacaciones se expresan como "se iniciarán al término de
    # las actividades del día X; las actividades lectivas comenzarán el día Y";
    # se transcriben como (X+1, Y-1).
    "cyl": [
        dict(curso="2021-22", fuente="Orden EDU/501/2021, BOCYL 5-may-2021 (cyl_calendario_escolar_2021-22.pdf), arts. 3.º, 5.º, 7.º y 8.º",
             verificado=True,
             inicio=D(2021, 9, 10), fin=D(2022, 6, 23),
             navidad=(D(2021, 12, 23), D(2022, 1, 9)), semana_santa=(D(2022, 4, 7), D(2022, 4, 17)),
             no_lectivos=[D(2021, 10, 11), D(2021, 12, 7), D(2022, 2, 28), D(2022, 3, 1)]),
        dict(curso="2022-23", fuente="Orden EDU/624/2022, BOCYL 10-jun-2022 (cyl_calendario_escolar_2022-23.pdf), arts. 3.º, 5.º, 7.º y 8.º",
             verificado=True,
             inicio=D(2022, 9, 9), fin=D(2023, 6, 23),
             navidad=(D(2022, 12, 23), D(2023, 1, 8)), semana_santa=(D(2023, 3, 30), D(2023, 4, 9)),
             no_lectivos=[D(2022, 10, 31), D(2022, 12, 9), D(2023, 2, 20), D(2023, 2, 21)]),
        dict(curso="2023-24", fuente="Orden EDU/578/2023, BOCYL 9-may-2023 (cyl_calendario_escolar_2023-24.pdf), arts. 3.º, 5.º, 7.º y 8.º",
             verificado=True,
             inicio=D(2023, 9, 7), fin=D(2024, 6, 21),
             navidad=(D(2023, 12, 23), D(2024, 1, 7)), semana_santa=(D(2024, 3, 23), D(2024, 4, 2)),
             no_lectivos=[D(2023, 10, 13), D(2023, 12, 7), D(2024, 2, 12), D(2024, 2, 13), D(2024, 4, 22)]),
        dict(curso="2024-25", fuente="Orden EDU/463/2024, BOCYL 24-may-2024 (cyl_calendario_escolar_2024-25.pdf), arts. 3.º, 5.º, 7.º y 8.º",
             verificado=True,
             inicio=D(2024, 9, 6), fin=D(2025, 6, 23),
             navidad=(D(2024, 12, 21), D(2025, 1, 7)), semana_santa=(D(2025, 4, 12), D(2025, 4, 23)),
             no_lectivos=[D(2024, 10, 31), D(2025, 3, 3), D(2025, 3, 4), D(2025, 5, 2)]),
        dict(curso="2025-26", fuente="Orden EDU/527/2025, BOCYL 29-may-2025 (cyl_calendario_escolar_2025-26.pdf), arts. 3.º, 5.º, 7.º y 8.º",
             verificado=True,
             inicio=D(2025, 9, 8), fin=D(2026, 6, 24),
             navidad=(D(2025, 12, 20), D(2026, 1, 7)), semana_santa=(D(2026, 3, 27), D(2026, 4, 6)),
             no_lectivos=[D(2025, 10, 31), D(2026, 2, 16), D(2026, 2, 17), D(2026, 4, 24)]),
        dict(curso="2026-27", fuente="Orden EDU/478/2026, BOCYL 28-may-2026 (cyl_calendario_escolar_2026-27.pdf), arts. 3.º, 5.º, 7.º y 8.º",
             verificado=True,
             inicio=D(2026, 9, 9), fin=D(2027, 6, 24),
             navidad=(D(2026, 12, 23), D(2027, 1, 10)), semana_santa=(D(2027, 3, 20), D(2027, 3, 30)),
             no_lectivos=[D(2026, 10, 30), D(2027, 2, 8), D(2027, 2, 9)]),
    ],
}

# Después del último curso publicado (2026-27) las normas dicen "vacaciones de
# verano desde el 1 de julio de 2027 hasta el día anterior al comienzo del curso
# 2027-28". El inicio de ese curso no está publicado: se asume que no es anterior
# al 1-sep-2027 (todos los cursos 2021-2027 empiezan en septiembre) y esos días
# se marcan escolar_verificado=False. Desde el 2027-09-01, NaN.
FIN_CONOCIDO_VERANO_2027 = D(2027, 8, 31)

# ---------------------------------------------------------------------------
# Acceso regulado a los Lagos de Covadonga (CO-04, p.k. 0-12,5)
# Fuente: resolución anual de la DGT (BOE), anexo de medidas especiales,
# fila "ASTURIAS. Covadonga. CO-04". 2024 y 2025 revisados sobre la imagen
# de la página del PDF (p. 60 de 2024 y p. 59 de 2025).
#   rangos: (inicio, fin) ambos inclusive
#   findes: meses (número) cuyos sábados y domingos están regulados
#   excepto: días excluidos de los rangos
#   tarde_libre: días en los que solo se exceptúa la tarde (regulado = True,
#                con nota en el horario)
#   horario: lista de (inicio, fin, texto)
# ---------------------------------------------------------------------------

LAGOS = {
    2022: dict(boe="BOE-A-2022-1125",
               rangos=[(D(2022, 4, 9), D(2022, 4, 17)), (D(2022, 4, 23), D(2022, 4, 24)), (D(2022, 4, 30), D(2022, 4, 30)),
                       (D(2022, 5, 1), D(2022, 5, 2)), (D(2022, 6, 1), D(2022, 10, 16)),
                       (D(2022, 10, 22), D(2022, 10, 23)), (D(2022, 10, 29), D(2022, 11, 1)), (D(2022, 12, 3), D(2022, 12, 11))],
               findes=[5], excepto=[D(2022, 7, 25), D(2022, 9, 8)], tarde_libre=[],
               horario=[(D(2022, 4, 9), D(2022, 9, 30), "08:00-21:00"), (D(2022, 10, 1), D(2022, 12, 11), "08:00-19:00")]),
    2023: dict(boe="BOE-A-2023-2159",
               rangos=[(D(2023, 4, 1), D(2023, 4, 9)), (D(2023, 4, 15), D(2023, 4, 16)), (D(2023, 4, 22), D(2023, 4, 23)),
                       (D(2023, 4, 29), D(2023, 5, 1)), (D(2023, 6, 1), D(2023, 10, 15)),
                       (D(2023, 10, 21), D(2023, 10, 22)), (D(2023, 10, 28), D(2023, 11, 1)), (D(2023, 12, 2), D(2023, 12, 10))],
               findes=[5], excepto=[D(2023, 7, 25), D(2023, 9, 8)], tarde_libre=[],
               horario=[(D(2023, 4, 1), D(2023, 9, 30), "07:30-21:00"), (D(2023, 10, 1), D(2023, 12, 10), "07:30-19:00")]),
    2024: dict(boe="BOE-A-2024-1773",
               rangos=[(D(2024, 3, 23), D(2024, 3, 31)), (D(2024, 4, 29), D(2024, 5, 3)), (D(2024, 6, 1), D(2024, 10, 13)),
                       (D(2024, 10, 19), D(2024, 10, 20)), (D(2024, 10, 26), D(2024, 10, 27)), (D(2024, 11, 1), D(2024, 11, 3)),
                       (D(2024, 11, 30), D(2024, 12, 9))],
               findes=[4, 5], excepto=[D(2024, 7, 25), D(2024, 9, 8)], tarde_libre=[],
               horario=[(D(2024, 1, 1), D(2024, 12, 31), "00:00-24:00")]),
    # 2025: "12 al 30 de abril" y "26 al 30 de abril" se solapan en el propio BOE
    # (comprobado sobre la imagen de la página); se toma la unión.
    2025: dict(boe="BOE-A-2025-1329",
               rangos=[(D(2025, 4, 5), D(2025, 4, 6)), (D(2025, 4, 12), D(2025, 4, 30)), (D(2025, 4, 26), D(2025, 4, 30)),
                       (D(2025, 5, 1), D(2025, 5, 1)), (D(2025, 5, 4), D(2025, 5, 4)), (D(2025, 6, 1), D(2025, 10, 19)),
                       (D(2025, 10, 25), D(2025, 10, 26)), (D(2025, 11, 1), D(2025, 11, 2)), (D(2025, 11, 29), D(2025, 12, 8))],
               findes=[5], excepto=[D(2025, 7, 25), D(2025, 9, 8)], tarde_libre=[D(2025, 7, 24)],
               horario=[(D(2025, 1, 1), D(2025, 12, 31), "00:00-24:00")]),
    2026: dict(boe="BOE-A-2026-1255",
               rangos=[(D(2026, 3, 28), D(2026, 4, 12)), (D(2026, 4, 18), D(2026, 4, 19)), (D(2026, 4, 25), D(2026, 5, 1)),
                       (D(2026, 6, 1), D(2026, 10, 18)), (D(2026, 10, 24), D(2026, 10, 25)), (D(2026, 10, 31), D(2026, 11, 2)),
                       (D(2026, 12, 1), D(2026, 12, 8))],
               findes=[5], excepto=[D(2026, 6, 6), D(2026, 7, 25), D(2026, 9, 8)], tarde_libre=[D(2026, 7, 24)],
               horario=[(D(2026, 1, 1), D(2026, 12, 31), "00:00-24:00")]),
}

# Incidencias excepcionales: solo prensa (NO OFICIAL), verificado = False.
LAGOS_INCIDENCIAS = [
    dict(inicio=D(2023, 8, 3), fin=D(2023, 8, 31), tipo="cierre_co4_particulares_ampliado",
         fuente="prensa: Telecinco/Europa Press 03-ago-2023 (prensa_telecinco_cierre_co4_agosto2023.html)",
         nota="'la CO-4 cerrará para los vehículos no autorizados hasta el mes de septiembre'; fecha de fin aproximada (no dice el día), "
              "y la noticia aclara que no cambia el calendario del plan sino que amplía las restricciones dentro de él"),
    dict(inicio=D(2025, 8, 16), fin=D(2025, 8, 18), tipo="suspension_transporte_publico_incendio",
         fuente="prensa: El Fielato 16-ago-2025 (prensa_elfielato_suspension_lagos_agosto2025.html); Vozpópuli 19-ago-2025",
         nota="'suspender hasta el próximo lunes, día 18 de agosto'; no consta si el 18 se incluye. Evacuación de ~400 personas el 16-ago"),
]

# Transcripción del folleto (imagen, sin texto) turismocangasdeonis_folleto_acceso_lagos.pdf,
# p. 2, recuadro "Fechas del Plan". Leído a ojo sobre la imagen renderizada; no
# indica el año (metadatos de mayo de 2024 y fechas iguales a las del BOE 2024).
FOLLETO_LAGOS = [
    ("S. Santa", "23-31 marzo"),
    ("Abril y mayo", "sábados, domingos y puentes"),
    ("Verano", "del 1 de junio al 13 de octubre (salvo 25 de julio y 8 de septiembre)"),
    ("Fines de semana de octubre", ""),
    ("Todos los Santos", "1-3 de noviembre"),
    ("Puente de la Constitución", "30 de noviembre al 9 de diciembre"),
    ("Horarios", "Del 23/03 al 30/09: primera subida 8:00h, última subida 17:45h, última bajada 20:50h; "
                 "del 1/10 al 9/12: primera subida 8:00h, última subida 16:00h, última bajada 19:05h"),
    ("Capacidad", "máximo de 3.000 viajeros diarios en autobús"),
]
