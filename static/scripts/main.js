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
const submitButton = document.getElementById('submit');

const map = L.map('map').setView([0, 0], 2);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

async function main() {
    // Fetch final destination
    const dest = await fetchTimes('dest', 3, 'destination');
    // If after 3 tries dest is undefined - abort the game
    if (!dest) { return; }

    console.log('Destination:');
    console.dir(dest);

    destNameTag.innerText = dest['airport_name'];
    destCountryTag.innerText = dest['country_name'];

    setUpFilters();

    // Fetch starting location, list of available airports, distance to destination,
    // current turn num, total km travelled and total co2 emitted
    const currentData = await fetchTimes('current', 3, 'current data');
    if (!currentData || Object.keys(currentData).length === 0) { return; }

    console.log('Current data:');
    console.dir(currentData);

    let {'current': curr, airports, dist, turn, 'total_km': totalKm,'total_co2': totalCO2} = currentData;

    updateHeader(curr, turn, totalKm, totalCO2);
    updateAirportsList(airports);

    // Add curr and dest markers
    map.panTo(([curr['lat'], curr['long']]));

    const markerCurr = L.marker([curr['lat'], curr['long']]).addTo(map);
    const markerDest = L.marker([dest['lat'], dest['long']]).addTo(map);
    markerDest._icon.style.filter = "hue-rotate(150deg)";

    // Zoom to the current location on first list hover
    airportsTag.addEventListener('mouseover', (event) => {
        map.zoomIn(3);
    }, {once : true});

    submitButton.addEventListener('click', (event) => {
        const li = document.getElementsByClassName('active')[0];
        if (li) {
            fetch('/move', {method: 'POST'}, li.dataset.ident)
                .then((response) => {
                        return response.json();
                    })
                    .catch((error) => {
                        console.error(`Failed to fetch ${String(resource)}. Error: ${error.message}`);
                    });
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
    totalKmTag.innerText = `Total km travelled: ${totalKm}`;
    totalCO2Tag.innerText = `Total CO2 emitted: ${totalCO2}`;
}

function updateAirportsList(airports) {
    const frag = new DocumentFragment;
    const liItems = [];
    let marker, markersel;

    // Empty airports list except for menu
    const oldItems = airportsTag.getElementsByTagName('li');
    for (let i=1; i<oldItems.length; i++) {
        oldItems[i].remove();
    }

    Array.from(airports).forEach((airport) => {
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

        name.innerText = airport['airport_name'];
        type.innerText = airport['type'].split('_').join(' ');
        country.innerText = airport['country_name'];
        direction.innerText = airport['direction'];
        dist.innerText = String(Math.round(airport['distance'])) + ' km';
        co2.innerText = Math.round(airport['co2']);

        li.dataset.ident = airport['ident'];

        li.addEventListener('mouseover', (event) => {
            marker = L.marker([airport['lat'], airport['long']]).addTo(map);
            marker._icon.style.filter = "hue-rotate(200deg)";
        });

        li.addEventListener('mouseout', (event) => {
            marker.remove();
        });

        li.addEventListener('click', (event) => {
            // Update active class
            liItems.forEach((item) => {
                item.classList.remove('active');
            })
            event.currentTarget.classList.add('active');

            // Update marker
            if (markersel) {
                markersel.remove();
            }
            markersel = L.marker([airport['lat'], airport['long']]).addTo(map);
            markersel._icon.style.filter = "hue-rotate(250deg)";
        });

        li.append(name, type, country, direction, dist, co2);
        liItems.push(li);
        frag.append(li);
    });

    airportsTag.append(frag);
}

function setUpFilters() {
    const buttons = Array.from(filtersTag.getElementsByTagName('span'));

    buttons.forEach((button) => {
        button.addEventListener('click', (event) => {
            // Clear data-order
            buttons.forEach((b) => {
                if (b !== button) {
                    delete b.dataset.order;
                }
            });

            // Set data-order
            console.log(button.dataset.order);

            if (button.dataset.order === 'desc') {
                button.dataset.order = 'asc';
            } else {
                button.dataset.order = 'desc';
            }
        });
    });
}