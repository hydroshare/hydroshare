import * as defaultUtils from './default-utils.js';

const getKey = ({ filename, metadata, req }) => {
  console.log('dynamically setting key for filename:', filename, 'metadata:', metadata);
  const key = metadata?.dynamic_key || filename;

  if (!key) {
    throw new Error('No key specified and filename is empty');
  }
  return key;
}

// Export all utils with your custom function
export const {
  jsonStringify,
  getURLBuilder,
  getRedirectPath,
  encrypt,
  decrypt,
  HttpError,
  prepareStream,
  getBasicAuthHeader,
  truncateFilename,
  getBucket,
  hasMatch,
  rfc2047EncodeMetadata,
} = defaultUtils;

export { getKey as defaultGetKey };