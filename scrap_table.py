import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web'
        }

    soup = BeautifulSoup(response.content, "html.parser")
    tabla_html = soup.find("table")
    if not tabla_html:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    rows_html = tabla_html.find("tbody").find_all("tr")
    if not rows_html:
        return {
            'statusCode': 204,
            'body': 'No se encontraron filas de datos'
        }

    # Conectar a DynamoDB
    dynamodb = boto3.resource('dynamodb')
    tabla_dynamo = dynamodb.Table('TablaSismosIGP')

    # Limpiar tabla antes de insertar nuevos datos
    scan = tabla_dynamo.scan()
    with tabla_dynamo.batch_writer() as batch:
        for item in scan.get('Items', []):
            batch.delete_item(Key={'id': item['id']})

    # Procesar los primeros 10 sismos
    sismos = []
    for row in rows_html[:10]:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue
        sismo = {
            "id": str(uuid.uuid4()),
            "reporte": cols[0].get_text(strip=True),
            "referencia": cols[1].get_text(strip=True),
            "fecha_hora": cols[2].get_text(strip=True),
            "magnitud": cols[3].get_text(strip=True),
        }
        tabla_dynamo.put_item(Item=sismo)
        sismos.append(sismo)

    return {
        'statusCode': 200,
        'body': sismos
    }