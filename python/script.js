const pro = 0
const URL = "http://127.0.0.1:55001/api/users"
fetch(URL).then(res => res.json())
    .then(data =>
        data.forEach(element =>
            console.log(element)
        )
    )
    .catch(err => console.log(err))