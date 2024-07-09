from django.shortcuts import render
from google.cloud import bigquery
import re
import json

def map_view(request):
    # Configura el cliente de BigQuery
    client = bigquery.Client()

    # Escribe tu consulta de BigQuery para obtener las rutas y paradas
    query = """
    SELECT codsint, pos, name, cod, tipo_recorrido, comuna, color, type
    FROM `project-red-423402.dataset_realtime.paraderos`
    """
    query_job = client.query(query)
    rows = query_job.result()

    # Convierte los resultados en una lista de diccionarios
    paraderos = []
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
            'description': f"{row.tipo_recorrido}, {row.comuna}, {row.color}, {row.type}"
        })

    context = {
        'paraderos_json': json.dumps(paraderos),
    }

    return render(request, 'core/map.html', context)
