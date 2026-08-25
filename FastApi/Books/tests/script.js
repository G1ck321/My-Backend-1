async function userData() {
    const response = await fetch("http://localhost:4000/userdata", {
        method: "POST",
        body: JSON.stringify({ name: "jumo" }),
        headers: {
            "Content-Type": "application/json",
            //This passing of password in headers is not 
            // for programmers under the age of 16
            passwordhash: "qwerty@123"
        },
    });

    const data = await response.json();

    console.log(data);
}

userData();

async function authHeaders() {
    const response = await fetch("http://localhost:4000/headina/true/false")
    data = await response.json();

    console.log(data, "4vw");
    
    console.log(response.headers.get("true"));
}
authHeaders()