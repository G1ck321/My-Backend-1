
const textSubmit = document.getElementById("textSubmit");
const myText = document.getElementById("yourText");
const textarea = document.getElementById("textArea");
const create = document.getElementById("create");
const active = document.getElementsByClassName("sideText");
const search_bar = document.getElementById("myInput")
const noteList = document.getElementById("noteList")
const delete_note = document.getElementById("delete")

//classname gives html collection

//takes id

let current_id;

let new_id;
let currentPage;
let last_created_id ;
let current_element ;

function viewData(id, note_value) {

    console.log(note_value)
    const note_text = `<br><div class="sideText" id= "${note_value["id"]}">${note_value["content"]}</div>`
    noteList.innerHTML += note_text;



}
//display text area from database
async function displayNotes() {

    const response = await fetch("http://127.0.0.1:3000/api/allnotes");

    const notes = await response.json()
    console.log(notes)




    for (const [id, note] of Object.entries(notes)) {
        viewData(id, note)
        
    }
    
    //last element id
    myText.innerText = `${notes[0]["content"]}`
    last_created_id = Number(notes[0]["id"])
    return last_created_id
}
displayNotes()

//selects text area
function selectTextArea(e) {

    //console.log(e.target)
    //this gets the properties of the element
    console.log(e.target.id)

    for (let each of active) {
        if (each.id == e.target.id) {
            myText.value = each.textContent
            current_id = each.id
            
            
            current_id = e.target.id
            console.log(current_id)
            return current_id
        }
    }
    // current_element = active[String(current_id)]
    //console.log(num)
}

console.log(current_id,'l')
textarea.addEventListener('click', selectTextArea)
//creates new notes
function createTextArea() {

    currentPage = null

    noteList.innerHTML += `<br><div class="sideText" id= "${last_created_id+1}"></div>`
    myText.value = noteList.lastElementChild.textContent
    
    

}
create.addEventListener('click', createTextArea)

// search for notes
search_bar.addEventListener('input', searchNotes)
async function searchNotes(e) {
    const search_query = e.target.value;
    try {
        const response = await fetch(`/api/search/${search_query}`);
        if (response.ok) {
            const notes = await response.json()
            console.log(notes.message)
        }
    }
    catch (err) {
        console.error("error")
    }
}

//submits text from textarea
current_element = document.getElementById(current_id)
textSubmit.addEventListener("submit", (e) => {
    e.preventDefault()

    let data = {
        content: myText.value,
        id: current_id
    }

    async function handleData() {

        const options = {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        }

        const options2 = {
            method: "PUT",
            headers: {
                "Content-type": "application/json"
            },
            body: JSON.stringify(data)
        }
        
        if (current_element) {
            const response = await fetch(`http://127.0.0.1:3000/update_notes/${current_id}`, options2);


            console.log(response.status, "updated")
            const info = await response.json()
            alert(info.message)
            console.log(info, "upf")

            current_element = document.getElementById(current_id)
            current_element.textContent = info
        // console.log( `${info} yess`)
        

        // return  `${info[0]["id"]}`
        
        }


        if (currentPage==null) {
            const response = await fetch("http://127.0.0.1:3000/create_notes", options);

            console.log(response.status, "created")
            const info = await response.json()
            current_element = document.getElementById(current_id)
            console.log(info)
            current_element.textContent = info['content']
            alert(info.message)

        }


        // fetch("http://127.0.0.1:3000/create_notes", options)
        // .then( res => {res.json() ;console.log(res.message)})
        // .then(resp=> console.log("Server says "+JSON.stringify(resp.a)))
        // .catch(err=>alert("Failed"))

    }
    handleData()
})
//deletes data


delete_note.addEventListener('click', deleteNote)
async function deleteNote(e) {
    const options3 = {
        'method':'DELETE',
        'Content-Type':'application/json'
    }
    const response = await fetch(`/api/delete_note/${current_id}`, options3)
    const data = response.json()
    noteList.remove(current_element)
    console.log(data);
    // alert(data);

}
