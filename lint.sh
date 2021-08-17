#!/bin/bash

find . -type f -name "*.py" | xargs pylint
