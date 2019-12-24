.PHONY: clean-build clean install install-all version

help:
	@echo "clean-build - remove build artifacts"
	@echo "test - run tests quickly with the default Python"
	@echo "version - get the package version"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build
	rm -rf .coverage
	rm -rf .pytest_cache

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs
	rm -rf *.egg-info

install: clean-build
	python3 setup.py install

install-all:
	pip install -e .[all]

test:
	python3 setup.py test

version:
	python3 setup.py --version

release: clean build
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean build
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
