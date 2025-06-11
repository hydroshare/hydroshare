// import the defaultOptions from the companion copy
// https://github.com/transloadit/uppy/blob/5c0c831937c9b3d93313775cc5b629fc15874a4b/packages/%40uppy/companion/src/config/companion.js
let { defaultOptions, getMaskableSecrets, validateConfig } = require('./companion-old');

// override the default options with the new ones
// https://uppy.io/docs/companion/#s3getkey-filename-metadata-req-
// ({ req, filename, metadata }) => `${req.user.id}/${filename}`,
defaultOptions.s3.getKey = ({ req, filename, metadata }) => {
	if (metadata.existing_path_in_resources) {
		// log the existing path
		console.log('existing_path_in_resources:', metadata.existing_path_in_resources);
		return metadata.existing_path_in_resources;
	}
	return `${metadata.hs_res_id}/${filename}`;
};
// https://uppy.io/docs/companion/#s3bucket-companion_aws_bucket
defaultOptions.s3.bucket = ({ filename, metadata, req }) => {
	// log the filename and metadata
	console.log('filename:', filename);
	console.log('metadata:', metadata);
	// console.log('req:', req);
			return 'asdf'
		}


module.exports = {
    defaultOptions,
    getMaskableSecrets,
    validateConfig,
};