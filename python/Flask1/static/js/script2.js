 function showData(element) {
            const tbody = document.getElementById("bod");
            //stbody.innerHTML = "";
        //     Object.keys(element).forEach((user) => {
        //       user = element[user]
        //    const td = `<tr>
        //     <td>${user[0]}</td>
        //     <td>${user[1]}</td>
        //     <td>${user[2]}</td>
        // </tr>`;
        //   tbody.innerHTML += td;
        // });
        //like key,value
        
          console.log(element[0])
            const td = `<tr>  
            <td>${element["username"]}</td>
            <td>${element["age"]}</td>
            <td>${element["job"]}</td>
        </tr>`;
          tbody.innerHTML += td;
        
    // for(let key in element)  {
    //   if (element.hasOwnProperty(key)){
    //     const user = element[key]
    //     tbody.innerHTML+=`<tr>
    //     <td>${user[0]}</td>
    //     <td>${user[1]}</td>
    //     <td>${user[2]}</td>`
        
    //   }
    // }
    }

    const URL = "http://127.0.0.1:5001/api/users";//uses post
    // const URL = "http://127.0.0.1:5000/api/users";uses get request only

    // fetch(URL)
    //     .then((res) => res.json())
    //     .then((data) => {
    //     if (data) {
    //         for (let i = 0; i < data.length; i++) {
    //         showData(data[i]);
    //         }
    //     }
    //     })

    //     .catch((err) => console.log(err));
    async function fetchandShow() {
      const resp = await fetch(URL)
      const data =await resp.json();
      
      for (const [username,arr] of Object.entries(data)){
        showData(arr)
      }
    }
    fetchandShow()