#!/usr/bin/env bash
black . -l 80 --skip-string-normalization --exclude ".git|.venv|.tox|env|src|docs|migrations|versioneer.py" $1
