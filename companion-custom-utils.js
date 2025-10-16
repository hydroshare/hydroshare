// Customizing the default companion utils to add a custom getKey function
// according to the docs (https://uppy.io/docs/companion/#s3getkey-filename-metadata-req-) we should be able to simply set getKey in providerOptions.s3
// but that doesn't seem to work, so we create a custom utils file that exports all the default utils plus our custom getKey function
// https://github.com/transloadit/uppy/blob/6f764122a947fc69aedf8e5ca18166ffb2643d03/packages/%40uppy/companion/src/server/helpers/utils.js
import * as defaultUtils from './default-utils.js';

const getKey = ({ filename, metadata, req }) => {
  console.log('dynamically setting key for filename:', filename, 'metadata:', metadata);
  const key = metadata?.dynamic_key || filename;

  if (!key) {
    throw new Error('No key specified and filename is empty');
  }
  return key;
}

// Export all utils with the updated custom function
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