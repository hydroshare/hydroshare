# Hydroshare _(hydroshare)_

### Nightly Build Status (develop branch)

| Workflow | Clean | Build/Deploy | Unit Tests | Flake8 | Requirements |
| -------- | ----- | ------------ | ---------- | -------| ------------ |
| [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-workflow/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-workflow/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-clean/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-clean/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-deploy/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-deploy/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-test/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-test/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-flake8/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-flake8/) | [![Requirements Status](https://requires.io/github/hydroshare/hs_docker_base/requirements.svg?branch=develop)](https://requires.io/github/hydroshare/hs_docker_base/requirements/?branch=master) | 

Build generate by [Jenkins CI](http://ci.hydroshare.org:8080)

HydroShare is a collaborative website being developed for better access to data and models in the hydrologic sciences. HydroShare will provide the sustainable technology infrastructure needed to address critical issues related to water quantity, quality, accessibility, and management. HydroShare will expand the data sharing capability of the CUAHSI Hydrologic Information System by broadening the classes of data accommodated, expanding capability to include the sharing of models and model components, and taking advantage of emerging social media functionality to enhance information about and collaboration around hydrologic data and models. 

More information can be found in our [Wiki Pages](https://github.com/hydroshare/hydroshare/wiki)

## Install

This README file is for developers interested in working on the Hydroshare code itself, or for developers or researchers learning about how the application works at a deeper level. If you simply want to _use_ the application, go to http://hydroshare.org and register an account.

If you want to install and run the source code of application locally, read on.

### Dependencies
[VirtualBox](https://www.virtualbox.org/wiki/Downloads) is required, as the preferred development environment is encapuslated within a VM. This VM has the appropriate version of Ubuntu  nstalled, as well as python and docker and other necessary development tools. 

#### Simplified Installation Instructions 
1. Download the [latest OVA file here](http://distribution.hydroshare.org/public_html/)
2. Open the .OVA file with VirtualBox, this will create a guest VM
3. Follow the instructions here to share a local hydroshare folder with your guest VM
4. Start the guest VM
5. Log into the guest VM with either ssh or the GUI. The default username/password is hydro:hydro
6. From the root directory `/home/hydro`, clone this repository into the hydroshare folder
7. `cd` into the hydroshare folder and run `./hsctl rebuild --db` to build the applicationa nd run it
8. If all goes well, your local version of Hydroshare should be running at http://192.168.56.101:8000

For more detailed installation, please see this document: [Getting Started with HydroShare](https://github.com/hydroshare/hydroshare/wiki/getting_started)


## Usage

Coming Soon

## API

Coming Soon

## Contribute

Coming Soon

## License 

Coming Soon
