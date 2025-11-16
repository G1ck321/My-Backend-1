const express = require('express')
const app = express()
const port = 3000

// app.get('/', (req, res) => res.send('Hello World! this is my first express message in 2025'))

app.use(express.static(__dirname))


app.get("/", (req, res) => {
    res.sendFile(
        "./public/index.html",
        { root: __dirname }
    )
    
})
app.listen(port, () => console.log(`Example app listening on port http://localhost:${port} !`))
