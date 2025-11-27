const myForm = document.getElementById('userForm');
const myName = document.getElementById('name');
const myEmail = document.getElementById('email');

myForm.addEventListener("submit",(e)=>{
    e.preventDefault()

    let data={
        name: myName.value,
        email: myEmail.value
    }

async function postData() {
    const options={
        method:'POST',
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify(data)
    }
    const response = await fetch("/api/create",options)
    const details = await response.json()
    console.log(details)
    e.target.reset()
    myName.value = ""
    myEmail.value = ""
    
}
postData()
})