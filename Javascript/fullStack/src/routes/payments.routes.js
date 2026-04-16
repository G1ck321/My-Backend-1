const express = require('express')

const paymentsRouter = express.Router()

paymentsRouter.post('/paystack/initiate', (req, res) => {
  res.status(501).json({
    success: false,
    message: 'Paystack setup is scaffolded. Add secret keys and initialize transactions next.',
  })
})

paymentsRouter.post('/bank-transfer/receipt', (req, res) => {
  res.status(501).json({
    success: false,
    message: 'Receipt upload endpoint is scaffolded. Next step will support multipart uploads.',
  })
})

module.exports = { paymentsRouter }