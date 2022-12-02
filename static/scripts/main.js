"use strict";

async function main() {
    // Fetch final destination
    const dest = await fetchTimes('dest', 3, 'destination');
    // If after 3 tries dest is undefined - abort the game
    if (!dest) { return; }

    console.log('Destination:');
    console.dir(dest);

    // Fetch starting location, list of available airports, distance to destination,
    // current turn num, total km travelled and total co2 emissed
    const currentData = await fetchTimes('current', 3, 'current data');
    if (!currentData || Object.keys(currentData).length === 0) { return; }

    console.log('Current data:');
    console.dir(currentData);
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

// Make several tries to fetch a resourse
async function fetchTimes(url, times=1, resource) {
    let res = await fetchFrom(url, resource);
    let tries = 1;

    while(!res && tries<Number(times)) {
        res = await fetchFrom(url, resource);
        tries++;
    }

    return res;
}
