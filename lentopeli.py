import mysql.connector
import os
import math
import time
from flask import Flask
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

@app.route("/")
def home():
    return 'Lentopeli'

connection.close()
