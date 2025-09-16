// custom-companion.js
const Companion = require('@uppy/companion')
const express = require('express')
const app = express()

app.use(express.json())

// Parse CORS origins from environment variable or set default
const parseCorsOrigins = () => {
  if (process.env.COMPANION_CLIENT_ORIGINS === 'true') {
    return true // Allow all origins (not recommended for production)
  }
  
  if (process.env.COMPANION_CLIENT_ORIGINS) {
    const origins = process.env.COMPANION_CLIENT_ORIGINS.split(',').map(origin => origin.trim())
    console.log('Using CORS origins from environment variable:', origins)
    return origins
  }

  if (process.env.COMPANION_CLIENT_ORIGINS_REGEX) {
    const regex = new RegExp(process.env.COMPANION_CLIENT_ORIGINS_REGEX)
    console.log('Using CORS origins regex from environment variable:', regex)
    return [regex]
  }
  
  console.log('No CORS origins specified, defaulting to common localhost origins for development.')
  
  // Default to allowing common origins for development
  return [
    'https://localhost',
    'http://localhost:8080',
    'http://localhost:8000'
  ]
}

const COMPANION_FILE_PATH = process.env.COMPANION_FILE_PATH || '/mnt/companion-data'

// Mandatory configuration options
const companionOptions = {
  secret: process.env.COMPANION_SECRET || 'your-secret-key-change-in-production',
  filePath: COMPANION_FILE_PATH,
  server: {
    host: process.env.COMPANION_DOMAIN || 'localhost:3020',
    protocol: process.env.COMPANION_PROTOCOL || 'http'
  },
  corsOrigins: parseCorsOrigins(),
  s3: {
    getKey: (req, filename, metadata) => {
      // Use dynamic bucket from metadata or fall back to env var
      const bucket = metadata?.bucket_name || process.env.COMPANION_AWS_BUCKET
      
      if (!bucket) {
        throw new Error('No bucket specified and COMPANION_AWS_BUCKET not set')
      }
      
      // Add timestamp to prevent filename conflicts
      const timestamp = Date.now()
      const random = Math.random().toString(36).substring(2, 8)
      return `${bucket}/${timestamp}-${random}-${filename}`
    }
  }
}

// Apply Companion to your Express app
const { app: companionApp } = Companion.app(companionOptions)
app.use(companionApp)

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() })
})

// Create the file path directory if it doesn't exist
const fs = require('fs')
if (!fs.existsSync(COMPANION_FILE_PATH)) {
  fs.mkdirSync(COMPANION_FILE_PATH, { recursive: true })
}

const PORT = process.env.COMPANION_PORT || 3020
app.listen(PORT, () => {
  console.log(`Custom Companion server running on port ${PORT}`)
  console.log(`File path: ${COMPANION_FILE_PATH}`)
  console.log(`Server host: ${companionOptions.server.host}`)
  console.log(`CORS origins: ${JSON.stringify(companionOptions.corsOrigins)}`)
})