from pprint import pprint

from noaa_sdk import NOAA


n = NOAA()
pprint(n.active_alerts(issuedby="JAX"))