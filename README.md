# joel-test

Just a test repository to test a few things I'm not confident in.  This repo may end up being a template for the rest of the project. Not sure.

* Django
* Postgres Docker
* Unit tests with PyTest
* Branch protection in bitbucket
* Pull requests in bitbucket
* Pipelines (CI?)


# How run

## Install dependencies
It is recommended that you make a virtual env for the dependencies, to not
pollute your system wide dependencies.

```
pip install -r requirements.txt
```

## Install git hooks
Assuming you've set up the python virtual env correctly, you should now have `pre-commit` in your path
Run the command in the root git directory
```
pre-commit install
```

## Setting up environment variables
Run the following command to copy the example environment
```
cp .env.example .env
```

## Starting docker
Firstly ensure you have docker-compose installed on your system
Then run:
```
cd ./docker
docker-compose up
```

