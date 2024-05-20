module.exports = {
  devServer: {
    disableHostCheck: true,
  },
  outputDir: "templates/hs_discover/",
  // Here profiding the ability to override the publicPath via an environment variable
  // Example export BASE_URL=http://my-public-bucket && npm run build
  // This should be the same as the STATIC_URL in the Django settings
  // https://cli.vuejs.org/config/#publicpath
  publicPath: process.env.BASE_URL ? process.env.BASE_URL : "/static/static",
  // https://cli.vuejs.org/config/#crossorigin
  // TODO: figure out how to get crossorigin to work with the Django static files
  crossorigin: "anonymous",
};
