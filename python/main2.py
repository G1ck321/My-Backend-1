import requests

API_KEY = "3deff2f0"
API_URL = f"http://www.omdbapi.com/?apikey={API_KEY}"

def show_movie(movie):
    """
    Prints movie details in a simple format.
    Args:
        movie (dict): Dictionary containing movie info
    """
    print(f"Title: {movie.get('Title', 'N/A')}")
    print(f"Poster: {movie.get('Poster', 'N/A')}")
    print("-" * 30)

def get_movies(movie_name, page=1):
    """
    Fetches movies from OMDB API and displays them.
    Args:
        movie_name (str): Movie name to search for
        page (int): Page number for pagination
    """
    url = f"{API_URL}&s={movie_name}&page={page}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("Search"):
            for movie in data["Search"][:9]:
                show_movie(movie)
        else:
            print("No movies found.")
    except Exception as e:
        print("Something went wrong:", e)

if __name__ == "__main__":
    movie_name = "Batman"
    current_page = 1
    get_movies(movie_name, current_page)
    # To search for another movie,