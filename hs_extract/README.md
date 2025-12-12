# hs_extract

## Building the Docker Image

To build the Docker image for this project, ensure you are in the parent directory of the repository. Run the following command:

```bash
docker-compose -f local-dev.yml up -d --build hs_extract
```

This ensures that the Dockerfile located in the parent directory is used for the build process.