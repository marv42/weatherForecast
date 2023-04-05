#!/usr/bin/env python3

import argparse
import json
import locale
import logging
import os
import subprocess
from urllib.error import URLError
from datetime import datetime
from subprocess import PIPE
import requests
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import mplcursors
# from io import BytesIO
# import mpld3

from weatherIcons import openWeatherMapIconId_2_Icons8Name
from IconCache import IconCache

activate_script = f'{os.path.dirname(__file__)}/venv/bin/activate'
status = subprocess.run([f'. {activate_script}'], shell=True, stdout=PIPE, stderr=PIPE)
if status.returncode != 0:
    logging.warning(f"Activating virtual environment failed: {status.stderr}")

if 'OPEN_WEATHER_MAP_API_KEY' in os.environ:
    API_KEY = os.environ['OPEN_WEATHER_MAP_API_KEY']
else:
    from apiKey import API_KEY

ALPHA_LEGEND = 0.9
BIG_Z_ORDER = 999999
TIME = 'time'
RAIN = 'rain'
SNOW = 'snow'
WIND = 'wind'
TEMP = 'temp'
FEELS_LIKE = 'feels_like'
DAY_NIGHT = 'day_night'
ICON = 'icon'
MAIN = 'main'
THREE_HOURS = '3h'
LABEL_TEMP = "Temperatur"
LABEL_FEEL = "gefühlt"
LABEL_WIND = "Wind"
DEG = "°C"
MM = "mm"
MPS = "m/s"
COLOR_TEMP = 'red'
COLOR_RAIN = 'blue'
COLOR_WIND = 'thistle'
COLOR_INVISIBLE = 'white'

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast?units=metric"
CITY_DEFAULT = "Sankt Ingbert"
WEATHER_FORECAST_PNG = "weatherForecast.png"


class WeatherForecast:

    def __init__(self, city_name, picture_file):
        self.city_name = city_name
        self.picture_file = picture_file

    def run(self):
        json_data = self.get_data(self.city_name)
        if json_data['cod'] != '200':
            print(f"Error: {json_data['message']}")
            exit(1)
        data = self.json_2_data_table(json_data['list'])
        figure = self.create_picture(data, json_data['city']['name'])
        if self.picture_file:
            self.picture_file = self.picture_file[0]
            if not self.picture_file:
                self.picture_file = WEATHER_FORECAST_PNG
            # if isinstance(self.picture_file, BytesIO):
            #    # mpld3.save_html(figure, self.picture_file)  # https://github.com/mpld3/mpld3/issues/362
            #    self.picture_file.write(mpld3.fig_to_html(figure).encode())
            #else:
            plt.savefig(self.picture_file)
        else:
            plt.show()

    def create_picture(self, data, city_name):
        self.set_mpl_params()
        figure, ax = plt.subplots(constrained_layout=True)
        wind_axis = ax.twinx()  # deepest axes -- drawing is done per axes, first ax first
        precipitation_axis = ax.twinx()
        temperature_axis = ax.twinx()
        graphs = self.draw_graphs(ax, temperature_axis, precipitation_axis, wind_axis, data)
        self.set_title(city_name)
        self.set_axes(ax, temperature_axis, precipitation_axis, wind_axis)
        self.set_legend(graphs)
        self.activate_tooltip(figure)
        return figure

    @staticmethod
    def set_mpl_params():
        matplotlib.use('TkAgg')
        matplotlib.rcParams['toolbar'] = 'None'

    def draw_graphs(self, ax, temperature_axis, precipitation_axis, wind_axis, data):
        range_length = range(len(data))
        time = [data[i][TIME] for i in range_length]
        temp = [data[i][TEMP] for i in range_length]
        feels_like = [data[i][FEELS_LIKE] for i in range_length]
        rain = [data[i][RAIN] for i in range_length]
        snow = [data[i][SNOW] for i in range_length]
        wind = [data[i][WIND] for i in range_length]
        day_night = [data[i][DAY_NIGHT] for i in range_length]
        icons = [data[i][ICON] for i in range_length]
        min_temp = min(min(temp), min(feels_like), 0)
        max_temp = max(max(temp), max(feels_like))

        self.draw_icons(ax, time, icons, min_temp, max_temp)
        self.plot_invisible(temperature_axis, precipitation_axis, wind_axis)
        self.plot_day_night(ax, time, day_night, min_temp, max_temp)
        temp_line = temperature_axis.plot(time, temp, COLOR_TEMP, label=LABEL_TEMP, linewidth=2)
        feels_like_line = temperature_axis.plot(time, feels_like, 'lightsalmon', label=LABEL_FEEL, linewidth=2)
        rain_line = precipitation_axis.plot(time, rain, COLOR_RAIN, label="Regen")
        snow_line = self.plot_snow_line(precipitation_axis, time, snow)
        wind_line = wind_axis.plot(time, wind, COLOR_WIND, label=LABEL_WIND)
        return [temp_line, feels_like_line, rain_line, snow_line, wind_line]

    @staticmethod
    def draw_icons(ax, time, icons, min_temp, max_temp):
        offset = [0 if n % 2 == 0 else 1 for n in range(len(time))]
        for t, i, o in zip(time, icons, offset):
            url = f"https://img.icons8.com/{openWeatherMapIconId_2_Icons8Name[i]}.png"
            try:
                image_file = IconCache(url).get_icon
                image = OffsetImage(image_file, zoom=0.6, alpha=0.3)
                box = AnnotationBbox(image, (t, min_temp + 0.95 * (max_temp - min_temp) - o),
                                     bboxprops=dict(edgecolor='white', alpha=0))
                ax.add_artist(box)
            except URLError:
                continue

    @staticmethod
    def plot_invisible(temperature_axis, precipitation_axis, wind_axis):
        temperature_axis.plot(0, 0, COLOR_INVISIBLE, visible=False)  # 0 as reference
        precipitation_axis.plot(0, 0, COLOR_INVISIBLE, visible=False)
        precipitation_axis.plot(0, 8, COLOR_INVISIBLE, visible=False)  # little rain to not appear as much
        wind_axis.plot(0, 0, COLOR_INVISIBLE, visible=False)
        wind_axis.plot(0, 10, COLOR_INVISIBLE, visible=False)

    def plot_day_night(self, ax, time, day_night, min_temp, max_temp):
        height = self.get_height_array(day_night, max_temp - min_temp)
        ax.bar(time, height, bottom=min_temp, width=1, color='whitesmoke', zorder=0)

    @staticmethod
    def get_height_array(day_or_night, height):
        return [height if dn == 'n' else 0 for dn in day_or_night]

    @staticmethod
    def plot_snow_line(precipitation_axis, time, snow):
        snow_line = None
        if any(s > 0 for s in snow):
            snow_line = precipitation_axis.plot(time, snow, 'lightskyblue', label="Schnee")
        return snow_line

    @staticmethod
    def set_title(city_name):
        plt.title(f"Wetter-Vorhersage für {city_name}")

    def set_axes(self, ax, temperature_axis, precipitation_axis, wind_axis):
        self.set_ticks(ax, temperature_axis, precipitation_axis, wind_axis)
        self.set_labels(ax, precipitation_axis, wind_axis)
        wind_axis.spines.right.set_position(('axes', 1.15))
        ax.yaxis.grid(True)
        # precipitation_axis.yaxis.grid(True)

    @staticmethod
    def set_ticks(ax, temperature_axis, precipitation_axis, wind_axis):
        ax.xaxis.set_major_locator(MultipleLocator(4))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        temperature_axis.set_yticks([])
        ax.tick_params(axis='y', labelcolor=COLOR_TEMP)
        precipitation_axis.tick_params(axis='y', labelcolor=COLOR_RAIN)
        wind_axis.tick_params(axis='y', labelcolor=COLOR_WIND)

    def set_labels(self, ax, precipitation_axis, wind_axis):
        self.set_labels_rotation(ax)
        ax.set_ylabel(f"{LABEL_TEMP} ({DEG})", color=COLOR_TEMP)
        # precipitation_axis.set_xlabel("Zeit")
        precipitation_axis.set_ylabel(f"Niederschlag ({MM})", color=COLOR_RAIN)
        wind_axis.set_ylabel(f"{LABEL_WIND} ({MPS})", color=COLOR_WIND)

    @staticmethod
    def set_labels_rotation(ax):
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    @staticmethod
    def set_legend(graphs):
        handles = []
        for g in graphs:
            if g is not None:
                handles.append(g[0])
        legend = plt.legend(handles=handles, loc='upper right')
        legend.get_frame().set_alpha(ALPHA_LEGEND)

    @staticmethod
    def activate_tooltip(figure):
        lines = [line for ax in figure.axes for line in ax.lines]
        cursor = mplcursors.cursor(lines, hover=True)  # , annotation_kwargs={'zorder': np.inf})

        @cursor.connect("add")
        def _(sel):  # on_add
            text = sel.annotation.get_text().split('\n')
            time = f"{text[1].split('=')[1]} {text[3]}"
            sel.annotation.get_bbox_patch().set(fc="white", alpha=1, zorder=BIG_Z_ORDER)
            sel.annotation.set_text(f"{sel.target[1]:.2f} {MM}\n{time}")
            labels = [line.get_label() for line in sel.artist.axes.lines]
            if labels[1] in [LABEL_TEMP, LABEL_FEEL]:
                sel.annotation.set_text(f"{sel.target[1]:.1f} {DEG}\n{time}")
            if labels[1] in [LABEL_WIND]:
                sel.annotation.set_text(f"{sel.target[1]:.1f} {MPS}\n{time}")

    def json_2_data_table(self, json):
        data = []
        for json_line in json:
            data_point = {TIME: self.reformat_time(json_line['dt_txt']),
                          RAIN: 0, SNOW: 0,
                          TEMP: json_line[MAIN]['temp'],
                          FEELS_LIKE: json_line[MAIN]['feels_like'],
                          WIND: json_line[WIND]['speed'],
                          DAY_NIGHT: json_line['sys']['pod'],
                          ICON: json_line['weather'][0]['icon']}
            if RAIN in json_line and THREE_HOURS in json_line[RAIN]:
                data_point[RAIN] = json_line[RAIN][THREE_HOURS]
            if SNOW in json_line and THREE_HOURS in json_line[SNOW]:
                data_point[SNOW] = json_line[SNOW][THREE_HOURS]
            data.append(data_point)
        return data

    @staticmethod
    def reformat_time(in_date):
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
        date_time = datetime.strptime(in_date, "%Y-%m-%d %H:%M:%S")
        return date_time.strftime("%a %d.%m. %H:%M")

    @staticmethod
    def get_data(city):
        url = f"{BASE_URL}&appid={API_KEY}&q={city}"
        response = requests.get(url)
        return json.loads(response.text)
        # return {"cod":"200","message":0,"cnt":4,"list":[
        #     {"dt":1623931200,"main":{"temp":30,"feels_like":20},
        #      "sys":{"pod":"d"},"dt_txt":"2021-06-17 12:00:00"},
        #     {"dt":1623942000,"main":{"temp":0,"feels_like":20},
        #      "sys":{"pod":"d"},"dt_txt":"2021-06-17 15:00:00"},
        #     {"dt":1623952800,"main":{"temp":-10,"feels_like":20},
        #      "sys":{"pod":"n"},"dt_txt":"2021-06-22 09:00:00"}],
        #         "city":{"id":2841590,"name":"Sankt Ingbert"}}


def parse_args():
    parser = argparse.ArgumentParser(description="get weather forecast data and display it")
    parser.add_argument('--city', default=CITY_DEFAULT,
                        help="name of the city the weather forecast for which should be shown (default: '%(default)s')")
    parser.add_argument('--save_pic', action='append', nargs='?',
                        help=f"save the picture file with the given name instead of displaying it (default: '{WEATHER_FORECAST_PNG}')")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    city_name = args.city
    picture_file = args.save_pic
    weatherForecast = WeatherForecast(city_name, picture_file)
    weatherForecast.run()
