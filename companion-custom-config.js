// https://uppy.io/docs/companion/#s3bucket-companion_aws_bucket
const DefOpt = require('./default-config.js').defaultOptions;
const getMaskableSecrets = require('./default-config.js').getMaskableSecrets;
const validateConfig = require('./default-config.js').validateConfig;

const bucket = ({ filename, metadata, req }) => {
      console.log('dynamically setting bucket for filename:', filename, 'metadata:', metadata);
      // Use dynamic bucket from metadata or fall back to env var
      const bucket = metadata?.bucket_name || process.env.COMPANION_AWS_BUCKET;
      
      if (!bucket) {
        throw new Error('No bucket specified and COMPANION_AWS_BUCKET not set');
      }
      return bucket;
    }

const defaultOptions = { 
  ...DefOpt, 
  s3: {
    bucket: bucket,
  },
  providerOptions: {
    s3: {
      bucket: bucket,
    }
  }
};

console.log('Custom companion config loaded with options:', defaultOptions);

module.exports = {
    defaultOptions,
    getMaskableSecrets,
    validateConfig,
};