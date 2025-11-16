// API Configuration
// Your OMDB API key
const API_KEY = "3deff2f0";

// Base URL for OMDB API - Using proper format without brackets
const APILINK = "http://www.omdbapi.com/?apikey=" + API_KEY;

// Search API uses the same base URL as APILINK
const SEARCHAPI = APILINK;

// Get DOM elements
const main = document.getElementById("section");
const form = document.getElementById("form");
const search = document.getElementById("query");

/**
 * Creates a movie card element with poster and title
 * @param {Object} movie - Movie data from OMDB API
 * @returns {HTMLElement} - The constructed card element
 */
function createMovieCard(movie) {
    // Create all necessary elements
    const div_card = document.createElement('div');
    const div_row = document.createElement('div');
    const div_column = document.createElement('div');
    const image = document.createElement('img');
    const title = document.createElement('h3');
    const center = document.createElement('center');

    // Set proper classes for layout
    div_card.className = 'card';
    div_row.className = 'row';
    div_column.className = 'column';
    image.className = 'thumbnail';
    
    // Set movie title (OMDB uses Title with capital T)
    title.innerHTML = movie.Title;
    
    // Set movie poster (with fallback for missing posters)
    image.src = movie.Poster !== "N/A" ? movie.Poster : "fallback-image.png";
    
    // Assemble the card structure
    center.appendChild(image);
    div_card.appendChild(center);
    div_card.appendChild(title);
    div_column.appendChild(div_card);
    div_row.appendChild(div_column);
    
    return div_row;
}

/**
 * Fetches and displays movies from OMDB API
 * @param {string} url - The API URL to fetch movies from
 */
function returnMovies(url) {
    fetch(url)
        .then(res => res.json())
        .then(function (data) {
            // Clear existing content
            main.innerHTML = "";
            
            // Check if we have search results
            if (data.Search && Array.isArray(data.Search)) {
                // Create and append movie cards for each result
                data.Search.forEach(movie => {
                    const movieCard = createMovieCard(movie);
                    main.appendChild(movieCard);
                });
            } else if (data.Error) {
                // Handle API errors
                main.innerHTML = `<div class="error">${data.Error}</div>`;
            }
        })
        .catch(error => {
            // Handle fetch errors
            console.error('Error:', error);
            main.innerHTML = '<div class="error">Failed to fetch movies. Please try again.</div>';
        });
}

// Load initial movies (searching for "Batman" as default)
returnMovies(SEARCHAPI + "&s=Batman");

// Handle search form submission
form.addEventListener("submit", (e) => {
    e.preventDefault();
    const searchItem = search.value.trim();

    if (searchItem) {
        // Use proper URL construction for search
        returnMovies(SEARCHAPI + "&s=" + encodeURIComponent(searchItem));
        search.value = ""; // Clear search input
    }
});
