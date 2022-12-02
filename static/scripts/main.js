"use strict";

async function main() {
    // Fetch final destination
    const dest = await fetchDest();

    console.log('Destination:');
    console.dir(dest);

    // If destination fetch failed - make 2 more tries. If both of them fail - abort the game
    let tries = 0;
    while(!dest && tries<2) {
        dest = await fetchDest();
        tries++;
    }
    if (!dest) { return; }
}

main();

// FUNCTIONS
function fetchDest() {
    const promise = fetch('dest')
        .then((response) => {
            return response.json();
        })
        .catch((error) => {
            console.error('Failed to fetch destination. Error: ' + error.message);
        });
    return promise;
}
