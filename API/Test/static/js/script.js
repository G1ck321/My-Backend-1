 let num = 0
        const textSubmit = document.getElementById("textSubmit");
        const myText = document.getElementById("yourText");
        const textarea = document.getElementById("textArea");
        const create = document.getElementById("create");
        var active = document.getElementsByClassName("sideText");
        

        //classname gives html collection

        //takes id

        console.log(num)
        
        //console.logcurrent_element.textContent
        // var store_num = []
        function selectTextArea(e) {
            
            //console.log(e.target)
            //this gets the properties of the element
            console.log(e.target.id)
            num = Number(e.target.id);

            //console.log(num)
            console.log(typeof (num))
            current_element = active[num]
            myText.value = current_element.textContent
            // store_num.push(num)
            return num
        }

        textarea.addEventListener('click', selectTextArea)
        //creates new notes
        function createTextArea() {

            textarea.innerHTML += `<br><div class="sideText" id= ${num+1}></div>`
            myText.value =  textarea.lastElementChild.textContent
            return num=num+1
        }
        create.addEventListener('click', createTextArea)

        //submits text from textarea
        
        textSubmit.addEventListener("submit", (e) => {
            e.preventDefault()
            console.log(myText.value)
            current_element = active[num]
            current_element.textContent = myText.value
            let data = {note:myText.value,
                id: num
            }
            
            async function postData() {

                const options = {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                }

                const options2 = {
                    method :"POST",
                    headers:{
                        "Content-type":"application/json"
                    },
                    body:JSON.stringify(data)
                }
                const response = await fetch("http://127.0.0.1:3000/create_notes", options);
                if (response.status==400){
                    const get_response = await fetch("http://127.0.0.1:3000/update_notes",options2);
                    console.log(get_response.status)
                    const get_info = await get_response.json()
                    alert(get_info.message)
                    
                }
                else{
                    console.log(response.status,"jdjhd")
                    const info = await response.json()
                    alert(info.message)  
                }
                
                // fetch("http://127.0.0.1:3000/create_notes", options)
                // .then( res => {res.json() ;console.log(res.message)})
                // .then(resp=> console.log("Server says "+JSON.stringify(resp.a)))
                // .catch(err=>alert("Failed"))

            }
            postData()
        })