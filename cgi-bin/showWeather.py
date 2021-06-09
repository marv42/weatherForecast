#!/usr/bin/env python3

import base64
import io

import weatherForecast
from weatherForecast import WeatherForecast


def remove_prefix_and_quotes(bytes):
    return str(bytes)[2:][:-1]


ioBytes = io.BytesIO()
weatherForecast = WeatherForecast(weatherForecast.CITY_DEFAULT, [ioBytes])
weatherForecast.run()
ioBytes.seek(0)
base64PngData = base64.b64encode(ioBytes.read())
pureBase64PngData = remove_prefix_and_quotes(base64PngData)

print(f"""
<html>
  <head>
	 <meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
  </head>

  <body>
	 <img src="data:image/png;base64, {pureBase64PngData}" alt="Wetter-Vorhersage als Linien-Diagramm der Temperatur und des Niederschlags" />
  </body>
</html>
""")
