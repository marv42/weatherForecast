import argparse
import locale
from datetime import datetime

import requests
import json
import matplotlib

from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator

from apiKey import API_KEY

ALPHA = 0.5
TEMP_OFFSET = 3
# TIME_UTC = 'time_utc'
TIME = 'time'
RAIN = 'rain'
SNOW = 'snow'
TEMP = 'temp'
FEELS_LIKE = 'feels_like'
DAY_OR_NIGHT = 'day_or_night'
THREE_HOURS = '3h'
LABEL_TEMP = "Temperatur"

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast?units=metric"


def visualize_data(data, city_name):
    range_length = range(len(data))
    time = [data[i][TIME] for i in range_length]
    temp = [data[i][TEMP] for i in range_length]
    feels_like = [data[i][FEELS_LIKE] for i in range_length]
    rain = [data[i][RAIN] for i in range_length]
    snow = [data[i][SNOW] for i in range_length]
    day_or_night = [data[i][DAY_OR_NIGHT] for i in range_length]
    set_mpl_params()
    figure, axes = plt.subplots(constrained_layout=True)
    set_title(city_name)
    secondary_axes = axes.twinx()
    draw_graphs(axes, secondary_axes, time, temp, feels_like, rain, snow, day_or_night)
    set_axes(axes, secondary_axes)
    set_legend(axes, secondary_axes)
    plt.show()


def draw_graphs(axes, secondary_axes, time, temp, feels_like, rain, snow, day_or_night):
    temp_line = axes.plot(time, temp, 'red', label=LABEL_TEMP)
    feels_like_line = axes.plot(time, feels_like, 'lightsalmon', label="gefühlt", zorder=0)
    rain_line = secondary_axes.plot(time, rain, 'blue', label="Regen")
    if any(s > 0 for s in snow):
        snow_line = secondary_axes.plot(time, snow, 'lightskyblue', label="Schnee", zorder=0)
    max_height = max(temp) - min(temp) + TEMP_OFFSET
    height = get_height_array(day_or_night, max_height)
    bottom = min(temp) - TEMP_OFFSET
    day_or_night_bars = axes.bar(time, height, bottom=bottom, width=1, color='whitesmoke', zorder=0)


def get_height_array(day_or_night, height):
    return [height if dn == 'n' else 0 for dn in day_or_night]


def set_mpl_params():
    matplotlib.use('TkAgg')
    matplotlib.rcParams['toolbar'] = 'None'


def set_title(city_name):
    plt.title(f"Wetter-Vorhersage für {city_name}")


def set_axes(axes, secondary_axes):
    set_x_axes(axes)
    set_y_axes(axes, secondary_axes)


def set_x_axes(axes):
    axes.xaxis.set_major_locator(MultipleLocator(4))
    axes.xaxis.set_minor_locator(MultipleLocator(1))
    # axes.set_xlabel("Zeit")
    set_labels_rotation(axes)


def set_labels_rotation(axes):
    plt.setp(axes.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")


def set_y_axes(axes, secondary_axes):
    axes.set_ylabel(f"{LABEL_TEMP} (°C)")
    axes.yaxis.grid(True)
    # secondary_axes.yaxis.grid(True)
    secondary_axes.set_ylabel("Niederschlag (mm)")


def set_legend(axes, secondary_axes):
    temp_legend = axes.legend(loc='upper left')
    temp_legend.get_frame().set_alpha(ALPHA)  # TODO geht net :-(
    precipitation_legend = secondary_axes.legend(loc='upper right')
    precipitation_legend.get_frame().set_alpha(ALPHA)


def json_2_data_table(json):
    data = []
    for json_line in json['list']:
        data_point = {TIME: reformat_time(json_line['dt_txt']),
                      RAIN: 0, SNOW: 0,
                      TEMP: json_line['main']['temp'],
                      FEELS_LIKE: json_line['main']['feels_like'],
                      DAY_OR_NIGHT: json_line['sys']['pod']}
        if RAIN in json_line and THREE_HOURS in json_line[RAIN]:
            data_point[RAIN] = json_line[RAIN][THREE_HOURS]
        if SNOW in json_line and THREE_HOURS in json_line[SNOW]:
            data_point[SNOW] = json_line[SNOW][THREE_HOURS]
        data.append(data_point)
    return data


def reformat_time(in_date):
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    date_time = datetime.strptime(in_date, "%Y-%m-%d %H:%M:%S")
    return date_time.strftime("%a %d.%m. %H:%M")


def get_data(city):
    url = f"{BASE_URL}&appid={API_KEY}&q={city}"
    response = requests.get(url)
    return json.loads(response.text)


def parse_args():
    parser = argparse.ArgumentParser(description='Get weather forecast data and display it')
    parser.add_argument('--city', help='Name of the city the weather for which should be shown')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    city_name = args.city
    if not city_name:
        city_name = "Sankt Ingbert"
    json = get_data(city_name)
    if json['cod'] != 200:
        print(f"Error: {json['message']}")
    data = json_2_data_table(json)
    visualize_data(data, city_name)
