import influxdb_client, os
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("INFLUXDB_TOKEN")
org = os.environ.get("INFLUX_ORG")
url = os.environ.get("INFLUX_URL")

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)