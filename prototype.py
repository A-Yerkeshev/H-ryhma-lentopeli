airports = []
flight_compare = ""
temp_dest = ""
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


def get_distance(curr_lat, curr_long, dest_lat, dest_long):
    distance_result = distance.distance([curr_lat, curr_long],
                                        [dest_lat, dest_long]).km
    return distance_result


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


def fetch_available_airports(curr_lat, curr_long, type):
    # Define flight radius based on airport type
    if type in dist_by_type:
        radius_km = dist_by_type[type]
    else:
        raise Exception(f"Airport type '{type}' is invalid.")

    # Select all airports within the reach of current location, based on airport type
    # Distance = 3963.0 * arccos[(sin(lat1) * sin(lat2)) + cos(lat1) * cos(lat2) * cos(long2 – long1)] * 1.609344
    sql = f"""SELECT ident, airport.name, country.name, type, latitude_deg, longitude_deg FROM airport, country
    WHERE 3963.0 * acos((sin(RADIANS({curr_lat})) * sin(RADIANS(latitude_deg))) +
    cos(RADIANS({curr_lat})) * cos(RADIANS(latitude_deg)) *
    cos(RADIANS(longitude_deg) - RADIANS({curr_long}))) * 1.609344 <= {radius_km}
    AND type != 'closed'
    AND ident != '{curr["ident"]}'
    AND country.iso_country = airport.iso_country;"""
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    airports.clear()

    # Order airports by direction
    direction_names = ['North', 'North-East', 'East', 'South-East', 'South', 'South-West', 'West', 'North-West']
    direction_groups = [[], [], [], [], [], [], [], []]

    for entry in result:
        airport = tuple_to_dict(entry)

        # Calculate in which direction airport is located
        x = (math.cos(math.radians(airport['lat'])) *
             math.sin(math.radians(airport['long'] - curr['long'])))
        y = (math.cos(math.radians(curr['lat'])) *
             math.sin(math.radians(airport['lat'])) -
             math.sin(math.radians(curr['lat'])) *
             math.cos(math.radians(airport['lat'])) *
             math.cos(math.radians(airport['long'] - curr['long'])))
        bearing = math.degrees(math.atan2(x, y))

        i = round(((bearing + 180)/45)+4)%8
        airport['direction'] = direction_names[i]
        direction_groups[i].append(airport)

    # Order airports by direction
    for group in direction_groups:
        for airport in group:
            airports.append(airport)


def print_available_airports():
    global dest
    for i, airport in enumerate(airports):
        if airport['ident'] == dest['ident']:
            print("V-" * 7 + "   YOUR DESTINATION   " + "-V" * 7)

        print(f"{str(i + 1) + ':':<5} {airport['airport_name'][0:43] + ',':<45}"
              f" {airport['type']:<20} {airport['country_name'][0:23]:<25}"
              f" {str(round(get_distance(curr['lat'], curr['long'], airport['lat'], airport['long']), 2)) + ' km':<15}"
              f" {airport['direction']}")


def print_results():
    global turns_total, km_total, dest
    # One CO2 gram = 1km * 90gr/km
    print(f"\nCongratulations! You made it to your destination, {dest['airport_name']}.\n"
          f"It took you {turns_total} turns and {km_total:.1f} km in total.\n"
          f"Your trip emitted {km_total * 90:.0f} grams of CO2.")


def move(index, flight):
    global curr, turns_total, km_total
    turns_total = turns_total + 1
    km_total = km_total + flight
    curr = airports[index]
    print(f"\nYou fly {flight:.1f} km to {curr['airport_name']}.")
    print("\r>", end="")
    time.sleep(0.2)
    print("\r----->", end="")
    time.sleep(0.2)
    print("\r---------->", end="")
    time.sleep(0.2)
    print("\r      --------->", end="")
    time.sleep(0.2)
    print("\r               >", end="")
    time.sleep(0.3)


def print_starting_message():
    print("Welcome to Group H's flight game. Your goal is to reach the given destination in as few turns as possible."
          "\n\nThe range where you can fly is determined by your current airport's type:"
          f"\n{'From balloon ports you can only fly':<35} {dist_by_type['balloonport']} km"
          f"\n{'From heliports you can fly':<35} {dist_by_type['heliport']} km"
          f"\n{'From seaplane bases you can fly':<35} {dist_by_type['seaplane_base']} km"
          f"\n{'From small airports you can fly':<35} {dist_by_type['small_airport']} km"
          f"\n{'From medium airports you can fly':<35} {dist_by_type['medium_airport']} km"
          f"\n{'Large airports allow a whopping':<35} {dist_by_type['large_airport']} km\n"
          "\nFind the right direction and fly to as large and as far away airports you can.")
    print("""

             -=\`\`
                \`\`
     |\ _________\_\__
   -=\c`oo oo oo ooo o`)
      `~~~~~~~~~~/ /~~`
                / /
            -==/ /
              '-'
          """)


# initialize start and end locations, calculate distance
curr = generate_random_location()
dest = generate_random_location()
dist = get_distance(curr["lat"], curr["long"], dest["lat"], dest["long"])

# set game length by making sure destination is X to Y km away
while dest == curr or (dist > 4000 or dist < 1500):
    dest = generate_random_location()
    dist = get_distance(curr["lat"], curr["long"], dest["lat"], dest["long"])

# Start the game
print_starting_message()

while curr['ident'] != dest['ident']:
    # Inform player about their current position and destination
    print(f"\nYour current location is '{curr['airport_name']}', {curr['type']} in {curr['country_name']}"
          f"\nYour destination is '{dest['airport_name']}' in {dest['country_name']}."
          f"\nThe destination is {dist:.0f} km away.")

    # Fetch and display airports within reach of the current location
    input("\nPress 'Enter' to fetch the nearest airports.")
    fetch_available_airports(curr["lat"], curr["long"], curr["type"])
    print_available_airports()

    # Ask player for airport index and check their input is valid
    index = input("\nEnter the index of the airport you want to fly to: ")
    while not index.isdigit() or (int(index) >= len(airports) + 1 or int(index) < 1):
        print(f"Your input is invalid. Please type a number from 1 to {len(airports)}")
        index = input("\nEnter the index of the airport you want to fly to: ")
    index = int(index) - 1

    # Update distance to the destination
    airport_dist = get_distance(curr['lat'], curr['long'], airports[index]['lat'], airports[index]['long'])
    dest_dist = get_distance(curr["lat"], curr["long"], dest["lat"], dest["long"])

    dist = get_distance(airports[index]['lat'], airports[index]['long'], dest["lat"], dest["long"])

    if airport_dist > dest_dist:
        dist *= -1

    move(index, airport_dist)

print_results()