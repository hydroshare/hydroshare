import { S3Client } from "@aws-sdk/client-s3";
import { FetchHttpHandler } from "@smithy/fetch-http-handler";
import type { RequestSigner } from "@smithy/types";
import User from "@/models/user.model";

// Normally an S3 client signs each request with access keys. Here we want to
// authenticate with the user's HydroShare login instead. The proxy in front of
// storage accepts either: a signed request, OR — if there's no signature — the
// browser's session cookie. So we deliberately send requests unsigned by using
// this no-op signer, which makes the proxy fall back to cookie auth.
const anonymousSigner: RequestSigner = {
  sign: async (request) => request, // return the request unchanged (no signature)
};

/**
 * Create an S3 client that authenticates with the user's HydroShare session
 * instead of S3 access keys:
 *   - requests are left unsigned, so the proxy uses the session cookie;
 *   - fetch sends the cookies (sessionid + csrftoken) with every request;
 *   - write requests also send the X-CSRFToken header Django requires.
 *
 * Regular `client.send(new SomeCommand(...))` calls work exactly as usual.
 */
export function createCookieS3Client(endpoint: string): S3Client {
  const client = new S3Client({
    // The SDK requires a region, but it's unused — the proxy re-signs each
    // request with its own storage credentials before forwarding it.
    region: "us-east-1",
    endpoint,
    forcePathStyle: true,
    // The SDK requires credentials, but they're never used (we don't sign).
    // These are throwaway placeholders.
    credentials: { accessKeyId: "cookie-auth", secretAccessKey: "cookie-auth" },
    signer: anonymousSigner,
    requestHandler: new FetchHttpHandler({ credentials: "include" }),
    // Only add checksum headers when an operation actually needs them — fewer
    // extra headers to get through CORS and the proxy.
    requestChecksumCalculation: "WHEN_REQUIRED",
    responseChecksumValidation: "WHEN_REQUIRED",
  });

  // Add Django's CSRF token to every write request. Reads (GET/HEAD) are safe
  // and don't need it.
  client.middlewareStack.add(
    (next) => async (args) => {
      // args.request is the outgoing HTTP request (method, headers, ...). We
      // type it inline instead of importing the smithy type, which Vite can't
      // resolve here.
      const request = args.request as {
        method?: string;
        headers?: Record<string, string>;
      };
      if (
        request?.method &&
        request.headers &&
        !["GET", "HEAD"].includes(request.method.toUpperCase())
      ) {
        const token = await User.getCSRFToken();
        if (token) {
          request.headers["x-csrftoken"] = token;
        }
      }
      return next(args);
    },
    { step: "build", name: "cookieCsrfMiddleware" },
  );

  return client;
}
