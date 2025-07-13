import influxdb_client, os
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.environ.get("INFLUXDB_TOKEN")
org = os.environ.get("INFLUX_ORG")
url = os.environ.get("INFLUX_URL")

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)