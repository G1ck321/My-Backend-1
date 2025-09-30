 function showData(element) {
            const tbody = document.getElementById("bod");
            //stbody.innerHTML = "";
            /*Object.values(element).forEach((user) => {
          const td = `<tr>
            <td>${user[0]}</td>
            <td>${user[1]}</td>
            <td>${user[2]}</td>
        </tr>`;
          tbody.innerHTML += td;
        });*/
        //like key,value
        for(const[username,user] of Object.entries(element)){
            const td = `<tr>
            <td>${user[0]}</td>
            <td>${user[1]}</td>
            <td>${user[2]}</td>
        </tr>`;
          tbody.innerHTML += td;
        }
      }

    const URL = "http://127.0.0.1:5000/api/users";
    fetch(URL)
        .then((res) => res.json())
        .then((data) => {
        if (data) {
            for (let i = 0; i < data.length; i++) {
            showData(data[i]);
            }
        }
        })

        .catch((err) => console.log(err));