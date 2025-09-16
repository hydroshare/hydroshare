// https://uppy.io/docs/companion/#s3bucket-companion_aws_bucket
const defaultOptions = require('./default-config.js').defaultOptions;
const getMaskableSecrets = require('./default-config.js').getMaskableSecrets;
const validateConfig = require('./default-config.js').validateConfig;

const bucket = ({ filename, metadata, req }) => {
  // https://uppy.io/docs/companion/#s3bucket-companion_aws_bucket
  console.log('dynamically setting bucket for filename:', filename, 'metadata:', metadata);
  // Use dynamic bucket from metadata or fall back to env var
  const bucket = metadata?.bucket_name || process.env.COMPANION_AWS_BUCKET;
  
  if (!bucket) {
    throw new Error('No bucket specified and COMPANION_AWS_BUCKET not set');
  }
  return bucket;
}

const getKey = ({ filename, metadata, req }) => {
  console.log('dynamically setting key for filename:', filename, 'metadata:', metadata);
  // Use dynamic key from metadata or default to filename
  const key = metadata?.dynamic_key || filename;

  if (!key) {
    throw new Error('No key specified and filename is empty');
  }
  return key;
}

defaultOptions.s3.bucket = bucket;
defaultOptions.s3.getKey = getKey;

// providerOptions
defaultOptions.providerOptions = {
  s3: {
    getKey,
    bucket,
  },
};
console.log('Custom companion config loaded with options:', defaultOptions);

module.exports = {
    defaultOptions,
    getMaskableSecrets,
    validateConfig,
};