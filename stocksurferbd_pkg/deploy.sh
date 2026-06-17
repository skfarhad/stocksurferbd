#!/bin/bash
set -e

# Load PyPI credentials from a .env file if present (never committed; see
# .gitignore). twine reads TWINE_USERNAME / TWINE_PASSWORD from the env.
#   TWINE_USERNAME=__token__
#   TWINE_PASSWORD=pypi-<your-api-token>
set -a
[ -f ../.env ] && . ../.env
[ -f .env ] && . .env
set +a

rm -rf ./build*
rm -rf ./dist*
python setup.py sdist bdist_wheel
twine check dist/*
twine upload dist/*
