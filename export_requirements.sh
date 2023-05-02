#!/bin/bash

# Export dependencies installed with Poetry to requirements files that can be
# used with pip install
# https://dealroom.atlassian.net/wiki/spaces/DATA/pages/930611318/Poetry+Quickstart

poetry export --output requirements.txt --without-hashes & \
poetry export --with dev --output requirements-dev.txt --without-hashes; \
sed -e 's/ *;.*$//g' requirements.txt > requirements-temp.txt; mv requirements-temp.txt requirements.txt; \
sed -e 's/ *;.*$//g' requirements-dev.txt > requirements-dev-temp.txt; mv requirements-dev-temp.txt requirements-dev.txt
