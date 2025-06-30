import requests
import boto3
import uuid

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/2025"

    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la API de sismos'
        }

    try:
        datos = response.json()
        ultimos_10 = datos[-10:]
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error al procesar el JSON: {str(e)}'
        }

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaSismosIGP')

    try:
        scan = table.scan()
        with table.batch_writer() as batch:
            for item in scan.get('Items', []):
                batch.delete_item(Key={'id': item['id']})
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error al limpiar la tabla: {str(e)}'
        }

    try:
        for i, row in enumerate(ultimos_10, start=1):
            row['#'] = i
            row['id'] = str(uuid.uuid4())
            table.put_item(Item=row)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error al insertar los datos: {str(e)}'
        }

    return {
        'statusCode': 200,
        'body': ultimos_10
    }
