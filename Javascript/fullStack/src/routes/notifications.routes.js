const express = require('express')

const notificationsRouter = express.Router()

notificationsRouter.post('/reminders/weekly', (req, res) => {
  res.status(501).json({
    success: false,
    message: 'Reminder scheduling is scaffolded. Next step will integrate email and SMS providers.',
  })
})

module.exports = { notificationsRouter }