import React from "react";

const ContactList = ({contacts}) =>{
    return <div>
        <h1>Contacts</h1>
        <table border="solid">
            <thead>
                <tr>
                    <th>First name</th>
                    <th>Last name</th>
                    <th>Email</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>{contacts.map((contact)=>(
                <tr align = "center" key={contact.id}>
                    <td>{contact.firstName}</td>
                    <td>{contact.lastName}</td>
                    <td>{contact.email}</td>
                    <td><button>Update</button>
                    <button>Delete</button>
                    </td>
                </tr>
            ))}</tbody>
        </table>
    </div>
}
export default ContactList;