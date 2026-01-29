// vetur.config.js
/** @type {import('vls').VeturConfig} */
module.exports = {
    // **optional** default: `{}`
    // override vscode settings
    // Notice: It only affects the settings used by Vetur.
    settings: {
      "vetur.useWorkspaceDependencies": true,
      "vetur.experimental.templateInterpolationService": true
    },
    // **optional** default: `[{ root: './' }]`
    // support monorepos
    projects: [
      './frontend', // Shorthand for specifying only the project root location
      {
        // **required**
        // Where is your project?
        // It is relative to `vetur.config.js`.
        root: './frontend',
      }
    ]
  }
  