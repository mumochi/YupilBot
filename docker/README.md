## Instructions
To build the docker image using the included docker file, run the following command from the YupilBot directory:
`docker build -t yupilbot ./docker/`

To run the first-time setup with setup.py, run interactively and mount the YupilBot directory:
`docker run -it -v .:/yupilbot yupilbot:latest python3 setup.py`

For a normal bot run, mount the YupilBot directory:
`docker run -v .:/yupilbot yupilbot:latest python3 setup.py`
