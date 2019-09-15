# Credo

Our stack consists of
* Django
* Postgres Docker
* Unit tests with PyTest [None so far]
* Bitbucket Pipelines for CI/CD [Not yet implemented]


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

# Testing

## Unit tests

### Running tests

```python -Wa manage.py test```
Note that the -Wa flag tells Python to display deprecation warnings for postgres etc.

Make sure to run tests before each pull request. This is the responsibility of the person logging the PR, however reviewers should double check with the logger.

### Adding new test cases

All unit tests should be created inside `./src/tests/*`.

Test discovery is based on the `unittest` module’s built-in test discovery. By default, this will discover tests in any file named “test*.py” under the current working directory.

See the [Django docs](https://docs.djangoproject.com/en/2.2/topics/testing/overview/) for more information on writing test cases.


