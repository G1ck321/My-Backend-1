// const myForm = document.getElementById('userForm');
// const myName = document.getElementById('name');
// const myEmail = document.getElementById('email');

// myForm.addEventListener("submit",(e)=>{
//     e.preventDefault()

//     let data={
//         name: myName.value,
//         email: myEmail.value
//     }

// async function postdata() {
//     const options={
//         method:'POST',
//         headers:{
//             "Content-Type":"application/json"
//         },
//         body:JSON.stringify(data)
//     }
//     const response = await fetch("/api/create",options)
//     const details = await response.json()
//     console.log(details)
//     e.target.reset()
//     myName.value = ""
//     myEmail.value = ""

// }
// postdata()
// })


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
let currentPage;
let first_id = 0;
let last_id;
let current_element;
let current_text;
let firstElement = null;

function viewData(id, note_value) {

    // console.log(note_value)
    const note_text = `<div class="sideText" id="${note_value["id"]}">${note_value["content"]}</div>`
    noteList.innerHTML += note_text;



}
//display text area from database
async function displayNotes(notes) {
    noteList.innerHTML = ""

    for (const [id, note] of Object.entries(notes)) {
        viewData(id, note)

    }

    //last element id
    // last_id = notes[note_lengt h - 1]["id"]
    // console.log(maxId,"maxiim")
    myText.innerText = `${notes[0]["content"]}`
    current_id = Number(notes[0]["id"])
    console.log(notes[0]["id"], "ko")

    return current_id
}


//selects text area
async function selectTextArea(e) {
    try {

        const response = await fetch("/api/allnotes");

        const notes = await response.json()
        console.log(notes)


        //console.log(e.target)
        //this gets the properties of the element

        if (firstElement == null) {
            current_element = document.getElementById(current_id)

            firstElement = 1

            current_id = await displayNotes(notes)
            console.log(current_id)


            current_text = (current_element, "celem")
            console.log(current_text)

        } else {
            // for (let each of active) {
            // if (each.id == e.target.id) {

            current_id = Number(e.target.id)
            myText.value = e.target.textContent
            console.log(current_id, 'is here')

            // return current_id
            // }


            // return current_id
            // }
        }
    } catch (err) {
        console.log("There is an error fetching notes")
        console.log(err)
    }
}
// current_element = active[String(current_id)]
//console.log(num)



window.addEventListener('DOMContentLoaded', () => {
    selectTextArea()
})
console.log(current_id, "K")
textarea.addEventListener('click', selectTextArea)

// console.log(current_text, "cur_text")
// console.log(typeof(current_text), "cur_texttype")
//creates new notes
async function createTextArea() {

    const response = await fetch("/api/allnotes");

    const notes = await response.json()
    console.log(notes)
    note_length = notes.length
    const ids = notes.map(note => note.id);
    const maxId = Math.max(...ids) //...is the spread operator
    last_id = maxId;
    noteList.innerHTML = `<div class="sideText" id="${last_id}"></div>` + noteList.innerHTML;
    let newNote = noteList.firstElementChild;
    myText.value = newNote.textContent
    current_id = last_id
}
create.addEventListener('click', (e) => {
    createTextArea()

})
console.log(currentPage)

// search for notes
search_bar.addEventListener('input', searchNotes)
async function searchNotes(e) {

    const search_query = e.target.value;
    try {
        const response = await fetch(`/api/search?q=${search_query}`);
        if (response.ok) {
            const notes = await response.json()
            console.log(notes, "noted")
            //if there are no notes with the query
            if (notes.length > 0) {
                displayNotes(notes)
            } else {
                noteList.innerHTML = ""
                const note_text = `<div class="sideText" id="">Not Found</div><br>`
                noteList.innerHTML += note_text;

            }
        }
    } catch (err) {
        console.error("error")
    }
}

//submits text from textarea

textSubmit.addEventListener("submit", (e) => {
    e.preventDefault()
    //element or current_id is different from database id
    //try to fix
    current_element = document.getElementById(`${current_id}`)
    current_text = String(current_element.textContent)
    console.log(current_element)
    console.log(current_text)
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

        if (current_text) {
            const response = await fetch(`/update_notes/${current_id}`, options2);

            console.log(response.status, "updated")
            const info = await response.json()
            alert(info.message)
            current_element.textContent = myText.value;

            console.log(current_id, "is current_id")

            // console.log( `${info} yess`)

            // return  `${info[0]["id"]}`

        } else if (!current_text) {
            const response = await fetch("/create_notes", options);

            console.log(response.status, "created")
            const info = await response.json()

            console.log(info)

            alert(info.message)
            current_id = JSON.parse(info["note"])
            console.log(current_id, "is current_id")
            current_element.setAttribute("id",current_id)
            current_element.textContent = myText.value;

        } else {
            console.log("what")
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
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    current_element = document.getElementById(`${current_id}`)
    try {
        
        const response = await fetch(`/api/delete_note/${current_id}`, options3)
        if (!response.ok) {
            
            alert("Select a note")
            throw new Error(`Resource not found: ${response.status}`)
        }
        
        const data = await response.json()
            console.log(current_element)
            console.log(current_id)
            current_element.style.display = 'none';
            myText.value = ""
            alert("Note Deleted")
            
        
    }
    catch (err) {
        console.log(err, "is err")
    }
    
    // alert(data);

}