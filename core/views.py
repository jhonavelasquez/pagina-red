from django.shortcuts import render
from google.cloud import bigquery
import re
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'core/index.html')

def map_view(request):
    # Obtener el valor de codsint filtrado desde la solicitud GET o usar 'None' por defecto
    codsint_filter = request.GET.get('codsint')

    # Configurar el cliente de BigQuery
    client = bigquery.Client()

    # Consulta de BigQuery para obtener los codsint disponibles
    query_codsint = """
    SELECT DISTINCT codsint
    FROM `project-red-423402.dataset_realtime.paraderos`
    """
    query_job_codsint = client.query(query_codsint)
    codsint_rows = query_job_codsint.result()

    # Lista de codsint disponibles para el dropdown
    codsint_choices = [row.codsint for row in codsint_rows]
    codsint_choices = sorted(codsint_choices, key=lambda x: (x.isdigit(), x))  # Ordenar los codsint

    paraderos = []
    path_ida = []
    path_regreso = []
    color = '#3388ff'

    if codsint_filter:
        # Consulta de BigQuery para obtener las rutas y paradas filtradas por codsint
        query_paraderos = """
        SELECT codsint, pos, name, cod, tipo_recorrido, comuna, color, type
        FROM `project-red-423402.dataset_realtime.paraderos`
        WHERE codsint = '{codsint_filter}'
        """
        query_paraderos = query_paraderos.format(codsint_filter=codsint_filter)
        query_job_paraderos = client.query(query_paraderos)
        rows = query_job_paraderos.result()

        # Convertir los resultados en una lista de diccionarios
        for row in rows:
            # Parsear las coordenadas si vienen como un string
            if isinstance(row.pos, str):
                coords_match = re.match(r'\[(-?\d+\.\d+), (-?\d+\.\d+)\]', row.pos)
                if coords_match:
                    coords = [float(coords_match.group(1)), float(coords_match.group(2))]
                else:
                    coords = [None, None]
            else:
                coords = [None, None]

            paraderos.append({
                'codsint': row.codsint,
                'coords': coords,
                'name': row.name,
                'code': row.cod,
                'color': row.color,
                'description': f"Recorrido de {row.tipo_recorrido}<br>En la comuna {row.comuna}<br>{row.color}"
            })

        # Consulta de BigQuery para obtener el camino de la ruta
        query_ruta = """
        SELECT path_ida, path_regreso, color
        FROM `project-red-423402.dataset_realtime.ruta`
        WHERE codsint = '{codsint_filter}'
        """
        query_ruta = query_ruta.format(codsint_filter=codsint_filter)
        query_job_ruta = client.query(query_ruta)
        ruta_row = None

        # Iterar sobre los resultados de la consulta para obtener el primer resultado
        for row in query_job_ruta.result():
            ruta_row = row
            break

        if ruta_row:
            path_ida = json.loads(ruta_row.path_ida) if ruta_row.path_ida else []
            path_regreso = json.loads(ruta_row.path_regreso) if ruta_row.path_regreso else []
            color = ruta_row.color if ruta_row.color else '#3388ff'

    context = {
        'paraderos_json': json.dumps(paraderos),  # Convertir la lista a JSON para usar en la plantilla
        'path_ida': json.dumps(path_ida),
        'path_regreso': json.dumps(path_regreso),
        'ruta_color': color,
        'codsint_filter': codsint_filter,  # Mantener el valor de codsint seleccionado para el dropdown
        'codsint_choices': codsint_choices,  # Lista de todos los codsint disponibles, ordenada
    }

    return render(request, 'core/map.html', context)

def schedule_view(request):
    # Configurar el cliente de BigQuery
    client = bigquery.Client()

    # Obtener el valor de codsint filtrado desde la solicitud GET
    codsint_filter = request.GET.get('codsint', None)

    # Consulta de BigQuery para obtener los horarios de las rutas
    query_horarios = """
    SELECT codsint, tipo_dia, inicio, fin
    FROM `project-red-423402.dataset_realtime.horarios`
    """
    
    # Aplicar el filtro solo si se proporciona un codsint
    if codsint_filter:
        query_horarios += f" WHERE codsint = '{codsint_filter}'"

    query_job_horarios = client.query(query_horarios)
    rows = query_job_horarios.result()

    # Convertir los resultados en una lista de diccionarios
    horarios = []
    for row in rows:
        horarios.append({
            'codsint': row.codsint,
            'tipo_dia': row.tipo_dia,
            'inicio': row.inicio,
            'fin': row.fin,
        })

    # Consulta de BigQuery para obtener los codsint disponibles
    query_codsint = """
    SELECT DISTINCT codsint
    FROM `project-red-423402.dataset_realtime.horarios`
    """
    query_job_codsint = client.query(query_codsint)
    codsint_rows = query_job_codsint.result()

    # Lista de codsint disponibles para el dropdown
    codsint_choices = [row.codsint for row in codsint_rows]
    codsint_choices = sorted(codsint_choices, key=lambda x: (x.isdigit(), x))  # Ordenar los codsint

    context = {
        'horarios': horarios,
        'codsint_filter': codsint_filter,
        'codsint_choices': codsint_choices,
    }

    return render(request, 'core/horario.html', context)

def historico_view(request):
    # Obtener el valor de shape_id filtrado desde la solicitud GET o usar 'None' por defecto
    shape_id_filter = request.GET.get('shape_id')

    # Configurar el cliente de BigQuery
    client = bigquery.Client()

    # Consulta de BigQuery para obtener los shape_id disponibles
    query_shape_ids = """
    SELECT DISTINCT shape_id
    FROM `project-red-423402.dataset_historicos.Shapes`
    """
    query_job_shape_ids = client.query(query_shape_ids)
    shape_id_rows = query_job_shape_ids.result()

    # Lista de shape_id disponibles para el dropdown
    shape_id_choices = [row.shape_id for row in shape_id_rows]

    shapes = []

    if shape_id_filter:
        logger.debug(f"Filtrando por shape_id: {shape_id_filter}")

        # Consulta de BigQuery para obtener las coordenadas del shape_id filtrado
        query_shapes = """
        SELECT shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence
        FROM `project-red-423402.dataset_historicos.Shapes`
        WHERE shape_id = '{shape_id_filter}'
        ORDER BY shape_pt_sequence
        """
        query_shapes = query_shapes.format(shape_id_filter=shape_id_filter)
        query_job_shapes = client.query(query_shapes)
        rows = query_job_shapes.result()

        # Convertir los resultados en una lista de diccionarios
        for row in rows:
            shapes.append({
                'shape_id': row.shape_id,
                'coords': [row.shape_pt_lat, row.shape_pt_lon],
                'sequence': row.shape_pt_sequence
            })

        logger.debug(f"Shape encontrado: {shapes}")

    context = {
        'shapes_json': json.dumps(shapes),  # Convertir la lista a JSON para usar en la plantilla
        'shape_id_filter': shape_id_filter,  # Mantener el valor de shape_id seleccionado para el dropdown
        'shape_id_choices': shape_id_choices,  # Lista de todos los shape_id disponibles
    }

    return render(request, 'core/historico.html', context)