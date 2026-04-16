const express = require('express')

const { healthRouter } = require('./health.routes')
const { authRouter } = require('./auth.routes')
const { menuRouter } = require('./menu.routes')
const { ordersRouter } = require('./orders.routes')
const { paymentsRouter } = require('./payments.routes')
const { notificationsRouter } = require('./notifications.routes')

const apiRouter = express.Router()

apiRouter.use('/health', healthRouter)
apiRouter.use('/auth', authRouter)
apiRouter.use('/menu', menuRouter)
apiRouter.use('/orders', ordersRouter)
apiRouter.use('/payments', paymentsRouter)
apiRouter.use('/notifications', notificationsRouter)

module.exports = { apiRouter }