module.exports = {
  devServer: {
    disableHostCheck: true,
  },
  outputDir: "templates/hs_discover/",
  // Here profiding the ability to override the publicPath via an environment variable
  // Example export BUCKET_URL_PUBLIC_PATH=http://my-public-bucket && npm run build
  // This should be the same as the STATIC_URL in the Django settings
  publicPath: process.env.BUCKET_URL_PUBLIC_PATH ? process.env.BUCKET_URL_PUBLIC_PATH : "/static/static",
};
