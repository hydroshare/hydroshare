// overriding the default middlewares from:
// https://github.com/transloadit/uppy/blob/main/packages/%40uppy/companion/src/server/middlewares.js
import * as defaultMiddlewares from './default-middlewares.js';
import { getURLBuilder } from './helpers/utils.js'
import getS3Client from './s3-client.js'

/**
 *
 * @param {object} options
 */
const customGetCompanionMiddleware = (options) => {
  /**
   * @param {object} req
   * @param {object} res
   * @param {Function} next
   */
  const middleware = (req, res, next) => {
    req.companion = {
      options,
      // we customize by passing the req as a parameter
      s3Client: getS3Client(req, options, false),
      s3ClientCreatePresignedPost: getS3Client(options, true),
      authToken: req.header('uppy-auth-token') || req.query.uppyAuthToken,
      buildURL: getURLBuilder(options),
    }
    next()
  }

  return middleware
}

// Export all middlewares with the updated custom function
export const {
  hasSessionAndProvider,
  hasOAuthProvider,
  hasSimpleAuthProvider,
  hasBody,
  hasSearchQuery,
  verifyToken,
  gentleVerifyToken,
  cookieAuthToken,
  cors,
  metrics,
} = defaultMiddlewares;

export { customGetCompanionMiddleware as getCompanionMiddleware };