module.exports = {
  devServer: {
    disableHostCheck: true,
  },
  // outputDir: '/usr/local/Cellar/nginx/1.19.3/html/', # TODO OBRIEN THIS IS WHEN DEPLOYING LOCALLY WITH NO DJANGO
  outputDir: 'templates/hs_resource_landing',
  publicPath: '/static',
};
