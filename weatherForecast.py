#!/usr/bin/python3

import argparse
import json
import locale
import os
from datetime import datetime

import numpy as np
import requests
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator
import mplcursors

if 'OPEN_WEATHER_MAP_API_KEY' in os.environ:
    API_KEY = os.environ['OPEN_WEATHER_MAP_API_KEY']
else:
    from apiKey import API_KEY

ALPHA_LEGENDS = 0.9
TIME = 'time'
RAIN = 'rain'
SNOW = 'snow'
TEMP = 'temp'
FEELS_LIKE = 'feels_like'
DAY_NIGHT = 'day_night'
THREE_HOURS = '3h'
LABEL_TEMP = "Temperatur"
LABEL_FEEL = "gefühlt"
DEG = "°C"
MM = "mm"

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
        data = self.json_2_data_table(json_data)
        picture = self.create_picture(data, self.city_name)
        if self.picture_file:
            self.picture_file = self.picture_file[0]
            if not self.picture_file:
                self.picture_file = WEATHER_FORECAST_PNG
            picture.savefig(self.picture_file)
        else:
            picture.show()

    def create_picture(self, data, city_name):
        self.set_mpl_params()
        figure, day_night_axis = plt.subplots(constrained_layout=True)
        self.set_title(city_name)
        precipitation_axis = day_night_axis.twinx()
        temperature_axis = day_night_axis.twinx()
        self.draw_graphs(day_night_axis, precipitation_axis, temperature_axis, data)
        self.set_axes(day_night_axis, precipitation_axis)
        self.set_legend(precipitation_axis, temperature_axis)
        self.activate_tooltip(figure)
        return plt

    def draw_graphs(self, day_night_axis, precipitation_axis, temperature_axis, data):
        range_length = range(len(data))
        time = [data[i][TIME] for i in range_length]
        temp = [data[i][TEMP] for i in range_length]
        feels_like = [data[i][FEELS_LIKE] for i in range_length]
        rain = [data[i][RAIN] for i in range_length]
        snow = [data[i][SNOW] for i in range_length]
        day_night = [data[i][DAY_NIGHT] for i in range_length]

        min_height = min(min(temp), 0)
        height = self.get_height_array(day_night, max(temp), min_height)
        day_night_bars = day_night_axis.bar(time, height, bottom=min_height, width=1, color='whitesmoke', zorder=0)
        temperature_axis.set_yticks([])  # TODO warum nich day_night_axis?
        # the order is relevant for the legends
        precipitation_axis.plot(0, 1, 'white', visible=False)
        rain_line = precipitation_axis.plot(time, rain, 'blue', label="Regen", zorder=2.3)
        snow_line = None
        if any(s > 0 for s in snow):
            snow_line = precipitation_axis.plot(time, snow, 'lightskyblue', label="Schnee", zorder=2.2)
        temperature_axis.plot(0, 0, 'white', visible=False)
        temp_line = temperature_axis.plot(time, temp, 'red', label=LABEL_TEMP, zorder=2.5)
        feels_like_line = temperature_axis.plot(time, feels_like, 'lightsalmon', label=LABEL_FEEL, zorder=2.4)

    @staticmethod
    def get_height_array(day_or_night, height, min_height):
        return [height if dn == 'n' else min_height for dn in day_or_night]

    @staticmethod
    def set_mpl_params():
        matplotlib.use('TkAgg')
        matplotlib.rcParams['toolbar'] = 'None'

    @staticmethod
    def set_title(city_name):
        plt.title(f"Wetter-Vorhersage für {city_name}")

    def set_axes(self, day_night_axis, precipitation_axis):
        self.set_ticks(day_night_axis)
        self.set_labels(day_night_axis, precipitation_axis)

    @staticmethod
    def set_ticks(day_night_axis):
        day_night_axis.xaxis.set_major_locator(MultipleLocator(4))
        day_night_axis.xaxis.set_minor_locator(MultipleLocator(1))
        day_night_axis.yaxis.grid(True)
        # precipitation_axis.yaxis.grid(True)

    def set_labels(self, day_night_axis, precipitation_axis):
        self.set_labels_rotation(day_night_axis)
        day_night_axis.set_ylabel(f"{LABEL_TEMP} ({DEG})")
        # precipitation_axis.set_xlabel("Zeit")
        precipitation_axis.set_ylabel(f"Niederschlag ({MM})")

    @staticmethod
    def set_labels_rotation(day_night_axis):
        plt.setp(day_night_axis.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    @staticmethod
    def set_legend(precipitation_axis, temperature_axis):
        temp_legend = temperature_axis.legend(loc='upper left')
        temp_legend.get_frame().set_alpha(ALPHA_LEGENDS)
        precipitation_legend = precipitation_axis.legend(loc='upper right')
        precipitation_legend.get_frame().set_alpha(ALPHA_LEGENDS)
        precipitation_legend.get_frame().set_zorder(np.inf)  # TODO hilft net :-(

    @staticmethod
    def activate_tooltip(figure):
        lines = [line for a in figure.axes for line in a.lines]
        cursor = mplcursors.cursor(lines, hover=True)

        @cursor.connect("add")
        def _(sel):  # on_add
            text = sel.annotation._text.split('\n')
            time = f"{text[1].split('=')[1]} {text[3]}"
            sel.annotation.get_bbox_patch().set(fc="white", alpha=1, zorder=np.inf)  # TODO is immer noch hinter der temperature_axis
            sel.annotation.set_text(f"{sel.target[1]:.2f} {MM}\n{time}")
            labels = [line._label for line in sel.artist.axes.lines]
            if labels[0] in [LABEL_TEMP, LABEL_FEEL]:
                sel.annotation.set_text(f"{sel.target[1]:.1f} {DEG}\n{time}")

    def json_2_data_table(self, json):
        data = []
        for json_line in json['list']:
            data_point = {TIME: self.reformat_time(json_line['dt_txt']),
                          RAIN: 0, SNOW: 0,
                          TEMP: json_line['main']['temp'],
                          FEELS_LIKE: json_line['main']['feels_like'],
                          DAY_NIGHT: json_line['sys']['pod']}
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
