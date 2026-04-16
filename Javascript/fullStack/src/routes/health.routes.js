const express = require('express')

const healthRouter = express.Router()

healthRouter.get('/', (req, res) => {
  res.json({
    success: true,
    service: 'FoodyBites API',
    status: 'healthy',
    timestamp: new Date().toISOString(),
  })
})

module.exports = { healthRouter }