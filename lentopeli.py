import mysql.connector
import os
import math
import time
from flask import Flask, render_template
from geopy import distance
from dotenv import load_dotenv

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

curr = None
dest = None
airports = []
turns_total = 0
km_total = 0
dist_by_type = {
    "balloonport": 50,
    "heliport": 100,
    "small_airport": 300,
    "medium_airport": 500,
    "large_airport": 1000,
    "seaplane_base": 100
}

@app.route("/")
def init():
    global curr, dest
    curr = generate_random_location()
    dest = generate_random_location()
    dist = get_distance(curr["lat"], curr["long"], dest["lat"], dest["long"])

    while dest == curr or (dist > 4000 or dist < 1500):
        dest = generate_random_location()
        dist = get_distance(curr["lat"], curr["long"], dest["lat"], dest["long"])
    return render_template('index.html')

@app.route("/dest")
def send_destination():
    return 

def generate_random_location():
    sql = "SELECT ident, airport.name as airport_name," \
          "country.name as country_name, type, latitude_deg, longitude_deg " \
          "FROM airport, country WHERE NOT type='closed' " \
          "and airport.iso_country = country.iso_country" \
          " ORDER BY RAND() LIMIT 1;"
    cursor.execute(sql)
    result = cursor.fetchall()

    return tuple_to_dict(result[0])


def tuple_to_dict(tuple):
    ident, airport_name, country_name, type, lat, long = tuple

    return {
        "ident": ident,
        "airport_name": airport_name,
        "country_name": country_name,
        "type": type,
        "lat": lat,
        "long": long,
    }

def get_distance(curr_lat, curr_long, dest_lat, dest_long):
    distance_result = distance.distance([curr_lat, curr_long],
                                        [dest_lat, dest_long]).km
    return distance_result


if __name__ == '__main__':
    app.run(use_reloader=True, host='127.0.0.1', port=3000)

connection.close()
