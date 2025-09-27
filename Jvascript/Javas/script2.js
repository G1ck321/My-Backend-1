// API setup - Think of this like importing your API key in Python
const API_KEY = "3deff2f0";
const API_URL = "http://www.omdbapi.com/?apikey=" + API_KEY;

// Getting HTML elements - Similar to Python's input() but for web elements
const mainSection = document.getElementById("section");
const searchForm = document.getElementById("form");
const searchInput = document.getElementById("query");
const btn = document.getElementById("btn");
let currentPage = 1;
let movieName = "Batman";
// Simple function to show movies
// In Python you'd write:
// def show_movie(movie_data):
//     """
//     Creates HTML for a movie
//     Args:
//         movie_data (dict): Dictionary containing movie info
//     """
function showMovie(movie) {
    // Create a simple card for each movie
    
        const movieCard = `
        <div class="row">
            <div class="column">
                <div class="card">
                    <center>
                        <img src="${movie.Poster !== 'N/A' ? movie.Poster : 'fallback-image.png'}" 
                            class="thumbnail">
                    </center>
                    <h3>${movie.Title}</h3>
                </div>
            </div>
        </div>
    `;
        mainSection.innerHTML += movieCard;
    
}
// Function to fetch movies
// In Python you'd write:
// def get_movies(search_url):
//     """
//     Fetches movies from OMDB API
//     Args:
//         search_url (str): URL to fetch movies from
//     """
function getMovies(url) {
    // Clear previous results
    mainSection.innerHTML = "";

    // Fetch is like Python's requests.get()
    fetch(url)
        .then(response => response.json())  // Like response.json() in Python requests
        .then(data => {
            if (data.Search) {
                // For each movie in results, show it
                // Like: for movie in data['Search']: in Python
                for (let i = 0; i < 9 ; i++) {
                    showMovie(data.Search[i]);
                }
                // data.Search.forEach(movie => showMovie(movie));
            } else {
                mainSection.innerHTML = '<h2>No movies found</h2>';
            }
        })
        .catch(error => {
            mainSection.innerHTML = '<h2>Something went wrong</h2>';
            console.log(error);
        });
}

// Start with Batman movies when page loads
getMovies(API_URL + "&s=" + movieName+"&page="+currentPage);

// When someone searches for a movie
// Like Python's input handling in a while True loop
searchForm.addEventListener("submit", (e) => {
    e.preventDefault();  // Stop form from refreshing page
    const movieName = searchInput.value;

    if (movieName) {  // If search isn't empty
        getMovies(API_URL + "&s=" + movieName+"&page="+currentPage);
        searchInput.value = "";  // Clear the search box
    }
});
function loadMore() {
    currentPage++;
    getMovies(API_URL + "&s=" + movieName+"&page="+currentPage);


}