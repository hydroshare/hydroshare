# Running Tests

## Selenium Tests with Firefox

### Provide an API for remote/docker control of host Firefox browser

-   Install Firefox on your host system
-   Install the [Selenium IDE Plugin](https://addons.mozilla.org/en-US/firefox/addon/selenium-ide/) for Firefox. This plugin can be helpful in determining page selectors.
-   Install the latest [geckodriver binary release](https://github.com/mozilla/geckodriver/releases).
-   Run the geckodriver binary eg:

> -   `geckodriver -vv --host 0.0.0.0 --port 4444 -b /usr/bin/firefox`

-   Now `geckodriver` is listening on port 4444 and providing an API to control the local Firefox browser.

### Configure the docker instance and start your notebook

-   Edit ``scripts/templates/docker-compose.template`` and add port 8888 to the listen ports for the hydroshare container. This port will be how we connect to the Jupyter notebook server.
-   To have this change take affect rebuild your docker environment.

> -   `hsctl rebuild`

-   Install the required Python dependencies for running the notebook server on the docker container.

> -   `docker exec hydroshare pip install ipython jupyter django-extensions`

-   Make sure that the notebook server listens to connections from the host by adding this to your `local_settings.py` :

        NOTEBOOK_ARGUMENTS = [
            '--ip', '0.0.0.0',
            '--port', '8888',
        ]

-   Start the notebook server.

> -   `./hsctl managepy shell_plus --notebook`

-   Click on link that is provided in your terminal that begins with <http://localhost:8888/>
-   Load up the `docs/SeleniumTests.ipynb` notebook and continue to follow the provided instructions.
