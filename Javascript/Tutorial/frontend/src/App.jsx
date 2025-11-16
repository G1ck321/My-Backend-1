import { useEffect, useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'
import ContactList from './contacts'
import Clock from './Clock'
import ContactForm from './ContactForm'
function App() {
  const [contacts, setContact] = useState([]) // can set it manually
  // const [contacts, setContact] = useState([{"firstName":"Akin","lastName":"Paw paw","email":"akp@gmail.com"}])

  useEffect(()=>{
    fetchContacts()
  },[])//once everything should load call the fetch contacts

  const fetchContacts = async ()=>{
    const response = await fetch("http://127.0.0.1:5000/contacts")//fetch-get request http is needed
    const data = await response.json()
    setContact(data.contacts)
    console.log(data.contacts)
    
  }

  return (
    <>
      <Clock/>
      <ContactList contacts={contacts}/>
      <ContactForm contacts = {contacts}/>
    </>
  )
}

export default App
