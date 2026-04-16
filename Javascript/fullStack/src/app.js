const path = require('path')
const express = require('express')
const cors = require('cors')
const helmet = require('helmet')
const morgan = require('morgan')

const { requestLogger } = require('./middleware/requestLogger')
const { errorHandler, notFound } = require('./middleware/errorHandler')
const { apiRouter } = require('./routes')

function createApp() {
  const app = express()

  app.disable('x-powered-by')
  app.use(helmet())
  app.use(
    cors({
      origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : true,
      credentials: true,
    })
  )
  app.use(express.json({ limit: '1mb' }))
  app.use(express.urlencoded({ extended: true }))
  app.use(requestLogger)
  app.use(morgan('dev'))

  app.use('/public', express.static(path.join(__dirname, '..', 'public')))
  app.use('/static', express.static(path.join(__dirname, '..', 'static')))

  app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'index.html'))
  })

  app.use('/api/v1', apiRouter)

  app.use(notFound)
  app.use(errorHandler)

  return app
}

module.exports = { createApp }