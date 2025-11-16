import { useState } from "react";

const ContactForm = ({contacts})=>{

    // contacts.map((contact)=>{
    //     console.log(contact)
    // })
const [firstName, setFirstname]= useState("")
const [lastName, setLastname]= useState("")
const [email, setEmail]= useState("")

const onSubmit = async (e)=>{//function
    e.preventDefault()//prevents page form reloading

    const data = {
        firstName,
        lastName,
        email
    }//this is a javascript object not veiwable in html
    const url = "http://127.0.0.1:5000/create_contact"
    const options={
        method: "POST",
        headers:{
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)//this converts to actual json
    }
    
    const response = await fetch(url,options);
    console.log(response.status)
    if (response.status !==201 || response.status !==200){
        const data = await response.json()
        alert(data.message)//we have a key called message that contains the error
        
        
    }
    else{
        //smth
    }
        

}

return (
<form onSubmit={onSubmit}>
    <div>
        <label htmlFor="firstName">First Name:</label>
        <input 
        type="text" 
        id="firstName" 
        value={firstName} 
        onChange={(e)=>{setFirstname(e.target.value)}}/>
    </div> <div>
        <label htmlFor="lastName">Last Name: </label>
        <input 
        type="text" 
        id="lastName" 
        value={lastName} 
        onChange={(e)=>{setLastname(e.target.value)}}/>
    </div> <div>
        <label htmlFor="email">Email:</label>
        <input 
        type="email" 
        id="email" 
        value={email} 
        onChange={(e)=>{setEmail(e.target.value)}}/>
    </div>
    <div>
    <button type="submit">Create Contact</button>
</div>
</form>
)

}
export default ContactForm;