// https://uppy.io/docs/companion/#s3bucket-companion_aws_bucket
import { defaultOptions, getMaskableSecrets, validateConfig } from './default-config.js';

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

// TODO: getkey doesn't seem to get triggered
// https://uppy.io/docs/companion/#s3getkey-filename-metadata-req-
const getKey = ({ filename, metadata, req }) => {
  console.log('dynamically setting key for filename:', filename, 'metadata:', metadata);
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
// defaultOptions.s3.forcePathStyle = true; // needed for minio
// defaultOptions.s3.region = process.env.COMPANION_AWS_REGION || 'us-east-1';
// defaultOptions.s3.endpoint = process.env.COMPANION_AWS_ENDPOINT || 'http://host.docker.internal:9000';
defaultOptions.s3.key = getDefaultAwsKey();
defaultOptions.s3.secret = getDefaultAwsSecret();
// defaultOptions.s3.forcePathStyle = process.env.COMPANION_AWS_FORCE_PATH_STYLE || 'true';

// providerOptions
defaultOptions.providerOptions = {
  s3: {
    getKey,
    bucket,
  },
};
console.log('Custom companion config loaded');

export { defaultOptions, getMaskableSecrets, validateConfig };