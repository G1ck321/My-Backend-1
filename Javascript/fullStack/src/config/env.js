const dotenv = require('dotenv')

dotenv.config()

function getEnv(name, fallback = undefined) {
  const value = process.env[name]
  if (value === undefined || value === '') {
    if (fallback !== undefined) {
      return fallback
    }
    throw new Error(`Missing required environment variable: ${name}`)
  }
  return value
}

module.exports = { getEnv }