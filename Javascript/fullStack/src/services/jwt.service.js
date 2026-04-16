const jwt = require('jsonwebtoken')

const JWT_SECRET = process.env.JWT_SECRET
const ACCESS_TOKEN_EXPIRY = '24h'
const REFRESH_TOKEN_EXPIRY = '30d'

if (!JWT_SECRET) {
  throw new Error('JWT_SECRET is not set in environment variables')
}

function signAccessToken(userId, email, role = 'customer') {
  return jwt.sign(
    {
      sub: userId,
      email,
      role,
    },
    JWT_SECRET,
    { expiresIn: ACCESS_TOKEN_EXPIRY }
  )
}

function signRefreshToken(userId) {
  return jwt.sign(
    {
      sub: userId,
      type: 'refresh',
    },
    JWT_SECRET,
    { expiresIn: REFRESH_TOKEN_EXPIRY }
  )
}

function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET)
  } catch (error) {
    throw new Error(`Token verification failed: ${error.message}`)
  }
}

function decodeToken(token) {
  try {
    return jwt.decode(token)
  } catch (error) {
    throw new Error(`Token decode failed: ${error.message}`)
  }
}

module.exports = {
  signAccessToken,
  signRefreshToken,
  verifyToken,
  decodeToken,
}
