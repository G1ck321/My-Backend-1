//My key: w56ef
//link http://www.omdbapi.com/?apikey=[yourkey]& the bracket is not used
//image or poster link http://img.omdbapi.com/?apikey=[yourkey]&
const API_KEY = "w56ef";
const APILINK = "http://www.omdbapi.com/?i=tt3896198&apikey=w56ef";
const IMG_PATH = "http://img.omdbapi.com/?apikey=w56ef&";
const SEARCHAPI = APILINK;
//OMDB uses same base url for search

const main = document.getElementById("section");
const form = document.getElementById("form");
const search = document.getElementById("query");

// function data and data=> are same
returnMovies(APILINK)
function returnMovies(url) {
    fetch(url).then(res => res.json()).then(function (data) {
        console.log(data.results);
        //OMDB API returns results in a property called Search, not .results.
        data.Search.forEach(element => {
            const div_card = document.createElement('div');
            div_card.setAttribute('class','card');
            const div_row = document.createElement('div');
            div_card.setAttribute('class','row');
            const div_column = document.createElement('div');
            div_card.setAttribute('class','column');
            const image = document.createElement('img');
            div_card.setAttribute('id','image');
            div_card.setAttribute('class','thumbnail');
            const title = document.createElement('h3');
            div_card.setAttribute('id','title');
            const center = document.createElement('center');

            //OMDB uses Title (capital T), not title.
            title.innerHTML = `${element.Title}`
            image.src = element.Poster !== "N/A" ? element.Poster : "fallback-image.png";
            center.appendChild(image);
            div_card.appendChild(center);
            div_card.appendChild(title);
            div_column.appendChild(div_card)
            div_row.appendChild(div_column)
            main.appendChild(div_row)

            return div_row
        });
    })
}
form.addEventListener("submit",(e)=>{
    //e is the event object
    e.preventDefault();
    main.innerHTML = ""//makes all the previous movies blank

    const searchItem = search.value;

    if (searchItem){
        returnMovies(APILINK+"s="+searchItem);
        search.value = "";//clears all the character in form
    }
})