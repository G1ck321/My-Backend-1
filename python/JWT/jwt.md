# Tutorial:(youtube channel)
**There are two ways to do authentication:**
--- 
**A. Traditional Approach(Cookies and sessions)** : 
-
 1. You use your browser to login or send data from any website
 2. You submit to server and it stores a session. It responds by sending a session ID to your client(browser)
 3. In the browser the session ID is stored in a Cookie or Cookie jar. Cookie is a text file saved in local storage in your browser in key valuee pair. 
 4. This cookie will be sent back for every subsequent request. Thee server will respond to the request if you're logged in. This is calle da stateful protocol between client and server
 5. **Stateful** saves everything in the backend. **Stateless** saves everything on the client side.
 ---
**B. JSON Web Tokens**:
-
 - **1.** User submits login form to server.
 - **2.** Instead of storing the session in the database and responding with a session ID. The server creates a JWT or JSON token with no sessions. Then client recieves it and stores it in local storage.
 - **3.** On future request the JWT is sent with the Authorization Header prefix, by the Bearer of the token. The server only needs to validate the signature.
 - **4.** In session the authentication state is handled on the server. The JWT are managed on the client

**Part One:**
-
send data(clent)->server generatestoken and hashes password
client saves login in browser->sends get and verifies.

**example:  `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30`**
-
    A JSON Web Token is just a text string seperated by dots(.):
    Header.Payload.Signature:
    * Header(The "What"): Describes the token("I am JWT using HS256 alg)
    - 
    * Payload(The "Who"): Contains the data. We put the user ID e.g{"sub":1,"role":"admin"}
    Anyone can read this part(It's just Base 64 Encoded, not encrypted don't put password here)
    -
    * Signature (The Proof): The server takes the Header+Payload+Your Secret Key and mixes them mathematically
    Why the Secret key matters:
    When a user sends a token back to you, your Flask app recalculates the Signature
    using the secret key you have on the server.
    * if the user tries to change the Payload(change role to admin) signature won't match
    * Flask will instantly reject with "Signature Verification faiiled"
Part One:
    - Hashing is a mathematical function that turns data into a scrambled string of characters
    - Encryption is like a suitcase with a key you can unlock it(decrypt)
    - When a user logs in you don't decrypt, you take the password, hash it, and see if the hash matches
    - Salting, if 2 users have same passwords, their hashes will look exactly the same 
    a hacker  could use a "Rainbow Table" (a giant list of pre-calculated hashes), to reverse them 
Fix: Salting: we can add a random string before it goes into the hash

Part Two:
    - We will use werkzeug.security, It comes installed with Flask,
    and handles comples math (algorithms like, scrypt or pdbkdf2) and automatic salting for you
    - functions used, generate_password_hash(password): Turns "monkey123" into scrypt:32768:8:1$kPv...,
    check_password_hash(hash, password): Takes the stored hash and the guess, and returns True or False

Part 3:
    - The Project (Admin Signup & Verification)
