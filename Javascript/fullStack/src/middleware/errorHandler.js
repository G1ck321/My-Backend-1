function notFound(req, res) {
  res.status(404).json({
    success: false,
    message: `Route not found: ${req.method} ${req.originalUrl}`,
  })
}

function errorHandler(err, req, res, next) {
  const isZodError = err && err.name === 'ZodError'
  const statusCode = isZodError ? 400 : err.statusCode || 500
  const message = isZodError ? 'Validation failed' : err.message || 'Internal server error'

  if (res.headersSent) {
    return next(err)
  }

  res.status(statusCode).json({
    success: false,
    message,
    errors: isZodError ? err.issues : undefined,
  })
}

module.exports = { notFound, errorHandler }