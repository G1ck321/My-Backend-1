from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

API_KEY = "3deff2f0"
API_URL = f"http://www.omdbapi.com/?apikey={API_KEY}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>OMDB Movie Search</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <h1>OMDB Movie Search</h1>
    <form method="get">
        <input type="text" name="movie_name" placeholder="Enter movie name" value="{{ movie_name or '' }}">
        <input type="number" name="page" min="1" value="{{ page }}">
        <button type="submit">Search</button>
    </form>
    {% if movies %}
        <h2>Results for "{{ movie_name }}" (Page {{ page }})</h2>
        <ul>
        {% for movie in movies %}
            <li>
                <strong>{{ movie.Title }}</strong><br>
                <img src="{{ movie.Poster if movie.Poster != 'N/A' else '' }}" alt="Poster" width="100"><br>
            </li>
        {% endfor %}
        </ul>
    {% elif movies is not none %}
        <p>No movies found.</p>
    {% endif %}
</body>
</html>
"""

def fetch_movies(movie_name, page=1):
    url = f"{API_URL}&s={movie_name}&page={page}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("Search", None)
    except Exception:
        return None

@app.route("/", methods=["GET"])
def index():
    movie_name = request.args.get("movie_name", "Batman")
    page = int(request.args.get("page", 1))
    movies = fetch_movies(movie_name, page)
    if movies is not None:
        movies = movies[:9]
    return render_template_string(HTML_TEMPLATE, movies=movies, movie_name=movie_name, page=page)

if __name__ == "__main__":
    app.run(debug=True)
    