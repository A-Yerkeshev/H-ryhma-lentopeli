"use strict";

// Fetch final destination
fetch('dest')
    .then((response) => {
        return response.json();
    })
    .then((destination) => {
        console.log(typeof destination);
        console.dir(destination);
    })
    .catch((error) => {
        console.error('Failed to fetch destination. Error: ' + error.message);
    });