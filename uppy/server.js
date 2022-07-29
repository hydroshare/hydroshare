const express = require('express'); 
const bodyParser = require('body-parser'); 
const session = require('express-session'); 
const companion = require('.'); 

const app = express();

app.use(bodyParser.json())
app.use(session({
  secret: 'some-fubarred-secret',
  resave: true,
  saveUninitialized: true,
}))

app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*')
  next()
})

// Routes
app.get('/', (req, res) => {
  res.setHeader('Content-Type', 'text/plain')
  res.send('Welcome to Companion')
})

// initialize uppy
const uppyOptions = {
  providerOptions: {
    drive: {
      key: '876543925663-7v2tf3dg8p9nugtjtcm37ks8ckub8cf4.apps.googleusercontent.com',
      secret: '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',
    },
    dropbox: {
      key: '07xw8rzny3rgkno',
      secret: '7an6hhingzaqgif',
    },
    box: {
      key: 'rv3q3tz9cq7995uaguahjvc9m524uhso',
      secret: 'PupcsbgEtWblcIk9TiELudGpxXB3zbvD',
    },
    // you can also add options for additional providers here
  },
  server: {
    host: 'cuahsi-dev-1.hydroshare.org',
    protocol: 'https',
    implicitPath: '/companion', 
  },
  filePath: '/uppy_tmp',
  // sendSelfEndpoint: 'cuahsi-dev-1.hydroshare.org/companion', 
  secret: 'some-random-secret',
  debug: true,
  metrics: true, 
}

app.use(companion.app(uppyOptions))

// handle 404
app.use((req, res) => {
  return res.status(404).json({ message: 'Not Found' })
})

// handle server errors
app.use((err, req, res) => {
  console.error('\x1b[31m', err.stack, '\x1b[0m')
  res.status(err.status || 500).json({ message: err.message, error: err })
})

companion.socket(app.listen(3020))
console.log('Welcome to Companion!')
console.log(`Listening on http://0.0.0.0:${3020}`)
