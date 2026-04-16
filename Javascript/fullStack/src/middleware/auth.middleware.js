const { verifyToken } = require('../services/jwt.service')

function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '')

  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'Missing or invalid Authorization header.',
    })
  }

  try {
    const decoded = verifyToken(token)
    req.user = {
      id: decoded.sub,
      email: decoded.email,
      role: decoded.role,
    }
    next()
  } catch (error) {
    return res.status(401).json({
      success: false,
      message: 'Unauthorized: ' + error.message,
    })
  }
}

module.exports = { authMiddleware }
