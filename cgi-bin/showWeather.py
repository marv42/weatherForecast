#!/usr/bin/env python3

import base64
import io

import weatherForecast
from weatherForecast import WeatherForecast

ioBytes = io.BytesIO()
weatherForecast = WeatherForecast(weatherForecast.CITY_DEFAULT, [ioBytes])
weatherForecast.run()
ioBytes.seek(0)

base64PngData = base64.b64encode(ioBytes.read()).decode(encoding='unicode_escape')
# mpld3_html = ioBytes.read().decode(encoding='unicode_escape')

print(f"""
<html>
  <head>
     <meta charset="utf-8"> <!-- HTML5 -->
     <meta http-equiv="content-type" content="text/html; charset=utf-8">
  </head>

  <body>
     <img src="data:image/png;base64, {base64PngData}" alt="Wetter-Vorhersage als Linien-Diagramm der Temperatur und des Niederschlags" />
     <!-- {{mpld3_html}} --> 
  </body>
</html>
""")
