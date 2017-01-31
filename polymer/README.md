# Your first Polymer element

This repo goes with the [Build your first Polymer element codelab](http://www.code-labs.io/codelabs/polymer-first-elements/).

The codelab is designed to be used with [Chrome Dev Editor](https://chrome.google.com/webstore/detail/chrome-dev-editor-develop/pnoffddplpippgcfjdhbmhkofpnaalpg?hl=en).
See the next section if you'd like to use another editor for the codelab.

## Running the codelab without Chrome Dev Editor

If you're not using CDE, you'll need to install some command-line tools to manage
dependencies and to run the demo.

1.  Download and install Node from [https://nodejs.org/](https://nodejs.org/). Node includes the node package manager command, `npm`.

2.  Install `bower` and `polyserve`:

        npm install -g bower polymer-cli

3.  Clone this repo:

        https://github.com/googlecodelabs/polymer-first-elements.git
        
4.  Change directory to your local repo and install dependencies with `bower`:

        cd polymer-first-elements
        bower install
        
5.  To preview your element, run `polymer serve` from the repo directory:

        polymer serve
        
    Open `localhost:8080/components/icon-toggle/demo/` in your browser. (Note that the path uses `icon-toggle`—the 
    component name listed in this element's `bower.json` file—rather than the actual directory name.) 
    
If you're wondering what `polymer serve` does, see [Testing elements with local bower dependencies](https://www.polymer-project.org/1.0/docs/start/reusableelements.html#local-dependencies) 
in the Polymer docs. 
