"use strict";

const currNameTag = document.getElementById('curr-name');
const currCountryTag = document.getElementById('curr-country');
const destNameTag = document.getElementById('dest-name');
const destCountryTag = document.getElementById('dest-country');
const turnTag = document.getElementById('turn');
const totalKmTag = document.getElementById('total-km');
const totalCO2Tag = document.getElementById('total-co2');
const airportsTag = document.getElementById('airports');
const filtersTag = document.getElementById('filter-controls');
const rulesButton = document.getElementById('showRules');
const rules = document.getElementById('rules');
const submitButton = document.getElementById('submit');

const map = L.map('map').setView([0, 0], 2);
const mapMarkers = {
    'curr': null,
    'dest': null,
    'sel': null,
    'tmp': null
}
let dest;

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

showRules.addEventListener('click', (event) => {
    rules.showModal();
});

async function main() {
    // Fetch final destination
    dest = await fetchTimes('dest', 3, 'destination');
    // If after 3 tries dest is undefined - abort the game
    if (!dest) { return; }

    console.log('Destination:');
    console.dir(dest);

    destNameTag.innerText = dest['airport_name'];
    destCountryTag.innerText = dest['country_name'];

    // Fetch starting location, list of available airports, distance to destination,
    // current turn num, total km travelled and total co2 emitted
    const currentData = await fetchTimes('current', 3, 'current data');
    if (!currentData || Object.keys(currentData).length === 0) { return; }

    console.log('Current data:');
    console.dir(currentData);

    let {'current': curr, airports, dist, turn, 'total_km': totalKm,'total_co2': totalCO2} = currentData;

    updateHeader(curr, turn, totalKm, totalCO2);
    // setUpFilters(airports);
    updateAirportsList(curr, airports);

    // Add curr and dest markers
    mapMarkers['curr'] = updateCurrent(curr['lat'], curr['long']);
    mapMarkers['dest'] = L.marker([dest['lat'], dest['long']]).addTo(map);
    mapMarkers['dest']._icon.style.filter = "hue-rotate(150deg)";

    // Zoom to the current location on first list hover
    airportsTag.addEventListener('mouseover', (event) => {
        map.zoomIn(3);
    }, {once : true});

    submitButton.addEventListener('click', (event) => {
        const li = document.getElementsByClassName('active')[0];
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': "application/json"
            },
            body: JSON.stringify(li.dataset.ident)
        }

        if (li) {
            fetch('/move', options)
                .then((response) => {
                    // If move succeded - fetch new data
                    if (response.status == 200) {
                        return fetchTimes('current', 3, 'current data');
                    }
                    else {
                        return response.json();
                    }
                })
                .then((currentData) => {
                    // Validate new data
                    if (!currentData || Object.keys(currentData).length === 0) { return; }
                    if (currentData['error']) {
                        throw new Error(currentData['error']);
                    }

                    console.log('Current data:');
                    console.dir(currentData);

                    let {'current': curr, airports, dist, turn, 'total_km': totalKm,'total_co2': totalCO2} = currentData;

                    // Check if player has arrived
                    if (curr['ident'] === dest['ident']) {
                        window.location.href = '/success';
                    }

                    updateHeader(curr, turn, totalKm, totalCO2);
                    updateAirportsList(curr, airports);
                    mapMarkers['curr'] = updateCurrent(curr['lat'], curr['long'], mapMarkers['curr']);
                })
                .catch((error) => {
                    console.dir(error);
                    console.error(`Failed to make a move. Error: ${error.message}`);
                });
        } else {
            console.log('Airport is not selected!');
        }
    })
}

main();

// FUNCTIONS
function fetchFrom(url, resource) {
    const promise = fetch(String(url))
        .then((response) => {
            return response.json();
        })
        .catch((error) => {
            console.error(`Failed to fetch ${String(resource)}. Error: ${error.message}`);
        });
    return promise;
}

// Make several tries to fetch a resource
async function fetchTimes(url, times=1, resource) {
    let res = await fetchFrom(url, resource);
    let tries = 1;

    while(!res && tries<Number(times)) {
        res = await fetchFrom(url, resource);
        tries++;
    }

    return res;
}

function updateHeader(curr, turn, totalKm, totalCO2) {
    currNameTag.innerText = curr['airport_name'];
    currCountryTag.innerText = curr['country_name'];
    turnTag.innerText = `Turn: ${turn}`;
    totalKmTag.innerText = `Total km travelled: ${Math.round(totalKm)} km`;
    totalCO2Tag.innerText = `Total CO2 emitted: ${Math.round(totalCO2)} gm`;
}

function updateAirportsList(curr, airports) {
    const frag = new DocumentFragment;
    const liItems = [];

    airportsTag.innerHTML = '';

    if (mapMarkers['sel']) { mapMarkers['sel'].remove(); }
    if (mapMarkers['tmp']) { mapMarkers['tmp'].remove(); }

    airports.forEach((airport) => {
        const li = document.createElement('li');
        const name = document.createElement('span');
        const country = document.createElement('span');
        const direction = document.createElement('span');
        const type = document.createElement('span');
        const dist = document.createElement('span');
        const co2 = document.createElement('span');

        name.classList.add('airport-name');
        type.classList.add('airport-type');
        country.classList.add('airport-country');
        direction.classList.add('airport-direction');
        dist.classList.add('airport-dist');
        co2.classList.add('airport-co2');

        if (dest['ident'] === airport['ident']) {
            li.classList.add('dest');
        }

        name.innerText = airport['airport_name'];
        type.innerText = airport['type'].split('_').join(' ');
        country.innerText = airport['country_name'];
        direction.innerText = airport['direction'];
        dist.innerText = String(Math.round(airport['distance'])) + ' km';
        co2.innerText = Math.round(airport['co2']);

        li.dataset.ident = airport['ident'];

        li.addEventListener('mouseover', (event) => {
            mapMarkers['tmp'] = L.marker([airport['lat'], airport['long']]).addTo(map);
            mapMarkers['tmp']._icon.style.filter = "hue-rotate(200deg)";
        });

        li.addEventListener('mouseout', (event) => {
            mapMarkers['tmp'].remove();
        });

        li.addEventListener('click', (event) => {
            // Update active class
            liItems.forEach((item) => {
                item.classList.remove('active');
            })
            event.currentTarget.classList.add('active');

            // Update marker
            if (mapMarkers['sel']) {
                mapMarkers['sel'].remove();
            }
            mapMarkers['sel'] = L.marker([airport['lat'], airport['long']]).addTo(map);
            mapMarkers['sel']._icon.style.filter = "hue-rotate(250deg)";
        });

        li.append(name, type, country, direction, dist, co2);
        liItems.push(li);
        frag.append(li);
    });

    airportsTag.append(frag);
}

function updateCurrent(lat, long, marker) {
    if (marker) {
        marker.remove();
    }

    map.panTo([lat, long]);

    return L.marker([lat, long]).addTo(map);
}

// function setUpFilters(airports) {
//     const buttons = Array.from(filtersTag.getElementsByTagName('span'));

//     buttons.forEach((button) => {
//         button.addEventListener('click', (event) => {
//             // Clear data-order
//             buttons.forEach((b) => {
//                 if (b !== button) {
//                     delete b.dataset.order;
//                 }
//             });

//             // Set data-order and sort
//             if (button.dataset.order === 'asc') {
//                 button.dataset.order = 'desc';

//                 sortAirports(airports, 'name', 'desc');
//                 updateAirportsList(airports);
//             } else {
//                 button.dataset.order = 'asc';

//                 sortAirports(airports, 'name', 'asc');
//                 updateAirportsList(airports);
                
//             }
//         });
//     });
// }

// function sortAirports(airports, by, order) {
//     switch (by) {
//         case 'name':
//             airports.sort((a1, a2) => {
//                 if (order === 'asc') {
//                     return a1['airport_name'].localeCompare(a2['airport_name']);
//                 } else if (order === 'desc') {
//                     return a2['airport_name'].localeCompare(a1['airport_name']);
//                 }
//             });
//             break;
//         case 'country':
//             break;
//         case 'type':
//             break;
//         case 'direction':
//             break;
//         case 'distance':
//             break;
//         case 'co2':
//             break;
//     }
// }