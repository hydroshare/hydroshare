// Cusomized Companion config to allow dynamic S3 bucket and key
// https://uppy.io/docs/companion/#s3bucket-companion_aws_bucket
// https://github.com/transloadit/uppy/blob/6f764122a947fc69aedf8e5ca18166ffb2643d03/packages/%40uppy/companion/src/config/companion.js
import { defaultOptions, getMaskableSecrets, validateConfig } from './default-config.js';

const bucket = ({ filename, metadata, req }) => {
  // https://uppy.io/docs/companion/#s3bucket-companion_aws_bucket
  // Use dynamic bucket from metadata or fall back to env var
  let bucket = metadata?.bucket_name || process.env.COMPANION_AWS_BUCKET;

  // if the bucket is still not set, get it from the req headers
  if (!bucket && req && req.headers['s3-bucket']) {
    bucket = req.headers['s3-bucket'];
  }
  
  if (!bucket) {
    throw new Error('No bucket specified and COMPANION_AWS_BUCKET not set');
  }
  return bucket;
}

// https://uppy.io/docs/companion/#s3getkey-filename-metadata-req-
const getKey = ({ filename, metadata, req }) => {
  // Use dynamic key from metadata or default to filename
  const key = metadata?.dynamic_key || filename;

  if (!key) {
    throw new Error('No key specified and filename is empty');
  }
  return key;
}

const getDefaultAwsKey = () => {
  const awsKey = process.env.COMPANION_AWS_KEY || 'temporarykey';
  console.log('Using default AWS key:', awsKey);
  return awsKey;
}

const getDefaultAwsSecret = () => {
  const awsSecret = process.env.COMPANION_AWS_SECRET || 'temporarysecret';
  console.log('Using default AWS secret:', awsSecret);
  return awsSecret;
}

defaultOptions.s3.bucket = bucket;
defaultOptions.s3.getKey = getKey;
defaultOptions.s3.key = getDefaultAwsKey();
defaultOptions.s3.secret = getDefaultAwsSecret();
// defaultOptions.s3.forcePathStyle = process.env.COMPANION_AWS_FORCE_PATH_STYLE || 'true'; // needed for minio

// providerOptions
defaultOptions.providerOptions = {
  s3: {
    getKey,
    bucket,
  },
};
console.log('Custom companion config loaded');

export { defaultOptions, getMaskableSecrets, validateConfig };