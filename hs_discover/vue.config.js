module.exports = {
  devServer: {
    allowedHosts: 'all',
  },
  outputDir: "templates/hs_discover/",
  // Here profiding the ability to override the publicPath via an environment variable
  // Example export VUE_APP_BUCKET_URL_PUBLIC_PATH=http://my-public-bucket && npm run build
  // This should be the same as the STATIC_URL in the Django settings
  // https://cli.vuejs.org/config/#publicpath
  publicPath: process.env.VUE_APP_BUCKET_URL_PUBLIC_PATH || 'VUE_APP_BUCKET_URL_PUBLIC_PATH_PLACEHOLDER',
  // https://cli.vuejs.org/config/#crossorigin
  crossorigin: "anonymous",
};
