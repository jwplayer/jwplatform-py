.PHONY: clean-pyc clean-build docs clean build install install-all version

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "build - build so file from pyx"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build clean-pyc
	rm -rf htmlcov/

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

install: clean-build
	python setup.py install

install-all:
	pip install -e .[all]

lint:
	pytest --flake8 buildpipe tests

test:
	python setup.py test

test-all:
	tox

version:
	python setup.py --version

docs:
	rm -f docs/jwplatform.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ buildpipe
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	xdg-open docs/_build/html/index.html

release: clean build
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean build
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
