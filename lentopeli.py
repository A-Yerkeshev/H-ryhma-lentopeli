import mysql.connector
import os
import math
import time
import json
import jsonpickle
import requests
from flask import Flask, send_file
from geopy import distance
from dotenv import load_dotenv

# CONFIGS
load_dotenv()
connection = mysql.connector.connect(
    host='127.0.0.1',
    port=3306,
    database='flight_game',
    user=os.environ['db_user'],
    password=os.environ['db_password'],
    autocommit=False
)
cursor = connection.cursor()
app = Flask(__name__)

# VARIABLES
curr = None
dest = None
dist = None
airports = []
currdata = None
turns_total = 0
km_total = 0
co2_total = 0
dist_by_type = {
    "balloonport": 50,
    "heliport": 100,
    "small_airport": 300,
    "medium_airport": 500,
    "large_airport": 1000,
    "seaplane_base": 100
}


# ROUTES
@app.route("/")
def init():
    global curr, dest, dist
    curr = generate_random_location()
    dest = generate_random_location()
    dist = get_distance(curr.lat, curr.long, dest.lat, dest.long)

    while dest == curr or (dist > 4000 or dist < 1500):
        dest = generate_random_location()
        dist = get_distance(curr.lat, curr.long, dest.lat, dest.long)
    return send_file('static/index.html')


@app.route("/dest")
def send_destination():
    return json.dumps(dest.__dict__)


@app.route("/current")
def send_current():
    global currdata, curr, airports, dist, turn, km_total, co2_total

    airports.clear()
    airports = fetch_available_airports(curr.lat, curr.long, curr.type)

    # Add direction and distance
    for airport in airports:
        add_direction(airport)
        airport.distance = round(get_distance(curr.lat, curr.long, airport.lat, airport.long), 2)

    # Calculate CO2 emission
    add_co2(airports)

    currdata = {'current': curr, 'airports': airports, 'dist': dist,
                'turn': turns_total, 'total_km': km_total, 'total_co2': co2_total}
    return jsonpickle.encode(currdata)


# FUNCTIONS
def generate_random_location():
    sql = "SELECT ident, airport.name as airport_name," \
          "country.name as country_name, type, latitude_deg, longitude_deg, iata_code " \
          "FROM airport, country WHERE NOT type='closed' " \
          "and airport.iso_country = country.iso_country" \
          " ORDER BY RAND() LIMIT 1;"
    cursor.execute(sql)
    result = cursor.fetchall()

    airport = Airport(result[0][0], result[0][1], result[0][2],
                      result[0][3], result[0][4], result[0][5], result[0][6])
    return airport

# def tuple_to_dict(tuple):
#     ident, airport_name, country_name, type, lat, long = tuple

#     return {
#         "ident": ident,
#         "airport_name": airport_name,
#         "country_name": country_name,
#         "type": type,
#         "lat": lat,
#         "long": long,
#     }


def get_distance(curr_lat, curr_long, dest_lat, dest_long):
    distance_result = distance.distance([curr_lat, curr_long],
                                        [dest_lat, dest_long]).km
    return distance_result


def fetch_available_airports(curr_lat, curr_long, type):
    # Define flight radius based on airport type
    if type in dist_by_type:
        radius_km = dist_by_type[type]
    else:
        raise Exception(f"Airport type '{type}' is invalid.")

    # Select all airports within the reach of current location, based on airport type
    # Distance = 3963.0 * arccos[(sin(lat1) * sin(lat2)) + cos(lat1) * cos(lat2) * cos(long2 – long1)] * 1.609344
    sql = f"""SELECT ident, airport.name, country.name, type, latitude_deg, longitude_deg, iata_code FROM airport, country
    WHERE 3963.0 * acos((sin(RADIANS({curr_lat})) * sin(RADIANS(latitude_deg))) +
    cos(RADIANS({curr_lat})) * cos(RADIANS(latitude_deg)) *
    cos(RADIANS(longitude_deg) - RADIANS({curr_long}))) * 1.609344 <= {radius_km}
    AND type != 'closed'
    AND ident != '{curr.ident}'
    AND country.iso_country = airport.iso_country;"""
    cursor = connection.cursor()
    cursor.execute(sql)
    db_result = cursor.fetchall()

    result = []

    # Create airport object from entries of db_results
    for entry in db_result:
        airport = Airport(entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6])
        result.append(airport)

    return result

def add_direction(airport):
    global curr

    direction_names = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

    # Calculate in which direction airport is located
    x = (math.cos(math.radians(airport.lat)) *
            math.sin(math.radians(airport.long - curr.long)))
    y = (math.cos(math.radians(curr.lat)) *
            math.sin(math.radians(airport.lat)) -
            math.sin(math.radians(curr.lat)) *
            math.cos(math.radians(airport.lat)) *
            math.cos(math.radians(airport.long - curr.long)))
    bearing = math.degrees(math.atan2(x, y))

    i = round(((bearing + 180)/45)+4)%8
    airport.direction = direction_names[i]

def add_co2(airports):
    global curr

    computable_flights = []
    airport_indexes = []

    # If either of airports has no iata_code - calculate co2 according to formula:
    # One CO2 gram = 1km * 90gr/km
    for i, airport in enumerate(airports):
        if curr.iata_code == '' or airport.iata_code == '':
            airport.airport_name += ' NOT COMPUTABLE'
            airport.co2 = airport.distance * 90
        else:
    # Otherwise, make a call to API to calculate it more precisely
            computable_flights.append({
                'from': curr.iata_code,
                'to': airport.iata_code
            })
            airport_indexes.append(i)

    headers = {
        'Content-Type': 'multipart/form-data',
        'Authorization': 'Bearer ' + os.environ['climatiq_key']
    }

    res = requests.post('https://beta3.api.climatiq.io/travel/flights', headers=headers, json={'legs': computable_flights})
    data = res.json()

    if res.status_code == 200:
        # Add calculated co2 to remaining airports
        for j, flight in enumerate(data['legs']):
            airports[airport_indexes[j]].co2 = flight['co2e']
    else:
        print('Failed to calculate co2 emission.')
        print(f"Status code: {res.status_code}")
        print(f"Error: {res.text}")


# CLASSES
class Airport:

    def __init__(self, ident, airport_name, country_name, type, lat, long, iata_code):
        self.ident = ident
        self.airport_name = airport_name
        self.country_name = country_name
        self.type = type
        self.lat = lat
        self.long = long
        self.iata_code = iata_code


if __name__ == '__main__':
    app.run(use_reloader=True, host='127.0.0.1', port=3000)
