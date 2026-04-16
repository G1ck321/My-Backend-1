# FoodyBites app.js Breakdown Guide

This guide explains what is happening in the Express application setup, especially in `src/app.js`.

It covers:
- What `helmet` and `morgan` do
- How middleware works from first principles
- What `config`, `utils`, `routes`, and `middleware` folders generally mean
- Analogies to help you build a strong mental model
- Neighboring concepts from Flask and Django

---

## The file being explained

Source file: `src/app.js`

```js
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
```

---

## First principles: what a web app is doing

At its core, a web server does 3 things:
1. Receive a request
2. Run steps in order to process it
3. Return a response

In Express, each step is usually a middleware function.

Think of middleware as a conveyor belt in a kitchen:
- A request is a food ticket moving down the belt
- Each station adds something (security headers, parse body, log, route decision)
- One station eventually serves output
- If something goes wrong, error stations handle it

---

## What helmet does

`helmet` adds security-focused HTTP headers.

Why this matters:
- Browsers use headers to decide security behavior
- Missing/weak headers can make attacks easier (clickjacking, sniffing, mixed content issues)

In plain terms:
- `helmet` is like putting safety rails around your endpoints
- It does not "secure everything"
- It reduces common web attack surface by default

Typical things it helps with:
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- Content Security Policy (when configured)

Neighboring concept:
- Flask/Django equivalents are security middlewares and secure response header configuration.

---

## What morgan does

`morgan` is HTTP request logging middleware.

Why this matters:
- You need visibility: who called what, and with what status
- Logs are essential for debugging, monitoring, and incident response

In plain terms:
- `morgan` is like a receptionist logbook at your office entrance
- Every request is recorded with useful metadata

`morgan('dev')` format usually prints:
- method
- path
- status code
- response time

Neighboring concept:
- Similar to request logging middleware in Django or Flask + gunicorn/nginx access logs.

---

## Line-by-line conceptual breakdown of app.js

### 1) Imports

```js
const path = require('path')
const express = require('express')
const cors = require('cors')
const helmet = require('helmet')
const morgan = require('morgan')
```

- `path`: safe cross-platform file path joining
- `express`: web framework runtime
- `cors`: browser cross-origin policy control
- `helmet`: secure default headers
- `morgan`: request logs

### 2) Internal modules

```js
const { requestLogger } = require('./middleware/requestLogger')
const { errorHandler, notFound } = require('./middleware/errorHandler')
const { apiRouter } = require('./routes')
```

- `requestLogger`: custom middleware to attach request metadata
- `notFound`: handles unknown routes
- `errorHandler`: central error response middleware
- `apiRouter`: grouped business routes

### 3) App factory

```js
function createApp() {
  const app = express()
```

Why app factory pattern is good:
- Easier to test
- Easier to reuse in different environments
- Keeps bootstrapping separate from server start

Python analogy:
- Flask `create_app()` factory pattern.

### 4) Security and parser middleware pipeline

```js
  app.disable('x-powered-by')
```
- Hides Express signature header to reduce fingerprinting.

```js
  app.use(helmet())
```
- Adds secure response headers.

```js
  app.use(
    cors({
      origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : true,
      credentials: true,
    })
  )
```
- Controls who can call your API from browsers.
- If env is set, uses explicit allowlist.
- `credentials: true` enables cookies/auth headers for allowed origins.

```js
  app.use(express.json({ limit: '1mb' }))
  app.use(express.urlencoded({ extended: true }))
```
- Parses incoming request bodies.
- JSON parser for API requests.
- URL-encoded parser for form submissions.
- Size limit helps reduce abuse risk.

```js
  app.use(requestLogger)
  app.use(morgan('dev'))
```
- Adds custom request metadata and standard request logs.

### 5) Static file serving

```js
  app.use('/public', express.static(path.join(__dirname, '..', 'public')))
  app.use('/static', express.static(path.join(__dirname, '..', 'static')))
```

- Exposes static assets (CSS/JS/images)
- `/public/...` maps to local `public` folder
- `/static/...` maps to local `static` folder

Python analogy:
- Flask static folder handling
- Django static files mapping in development.

### 6) Root page route

```js
  app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'index.html'))
  })
```

- Serves landing page HTML on homepage.

### 7) API router mount

```js
  app.use('/api/v1', apiRouter)
```

- Everything inside `apiRouter` gets versioned prefix `/api/v1`
- Keeps API evolution manageable without breaking older clients

### 8) Fallback and error handling (order matters)

```js
  app.use(notFound)
  app.use(errorHandler)
```

- `notFound`: catches requests that matched nothing
- `errorHandler`: catches thrown errors or `next(error)` calls

Important concept:
- Middleware order in Express is the control flow.
- If you move these up, behavior changes.

### 9) Export

```js
  return app
}

module.exports = { createApp }
```

- Exports app factory for use by `main.js`.

---

## Why middleware order is critical

Express runs middleware top-to-bottom.

If you reorder incorrectly, examples of breakage:
- Routes before body parsers: `req.body` may be empty
- Error handlers before routes: errors not handled correctly
- Static serving after catch-all notFound: static files 404

Rule of thumb:
1. security and request preprocessing
2. logging
3. static routes and app routes
4. 404 handler
5. error handler

---

## Folder role map (general architecture)

- `src/config`: environment and external clients setup
  - Example: Supabase client, env variable access
- `src/middleware`: request pipeline components
  - Auth, logging, validation, error handlers
- `src/routes`: endpoint grouping by domain
  - auth, menu, orders, payments
- `src/utils`: shared helpers
  - async wrappers, formatters, pure utilities

Analogy:
- `config` is infrastructure wiring
- `middleware` is traffic control system
- `routes` are business counters/desks
- `utils` are reusable tools in the back office

---

## Neighboring concepts (for Python background)

Flask mapping:
- `createApp()` -> `create_app()`
- `app.use(middleware)` -> `before_request` / WSGI middleware
- `routes` modules -> blueprints
- `errorHandler` -> `@app.errorhandler`

Django mapping:
- Express middleware stack -> `MIDDLEWARE` list execution
- routes -> `urls.py` + views by app
- config -> `settings.py` + service init modules
- error handlers -> custom 404/500 handlers and exception middleware

---

## Practical mental model to keep

`app.js` is your composition root.

That means:
- It should wire pieces together
- It should stay thin and declarative
- Heavy business logic should live in route handlers/services, not here

If this remains clean, your codebase scales better as features are added.
