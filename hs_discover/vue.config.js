module.exports = {
  devServer: {
    allowedHosts: 'all',
  },
  outputDir: "templates/hs_discover/",
  // publicPath should be the same as the STATIC_URL in the Django settings
  // This is not known at build time so we use a placeholder for production builds and /static/static for local builds
  // https://cli.vuejs.org/config/#publicpath
  publicPath: 'VUE_APP_BUCKET_URL_PUBLIC_PATH_PLACEHOLDER',
  // https://cli.vuejs.org/config/#crossorigin
  crossorigin: "anonymous",
};
