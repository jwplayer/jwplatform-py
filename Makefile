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
	pip3 install -e .[all]

test:
	python3 setup.py test

version:
	python3 setup.py --version

build:
	python3 setup.py sdist bdist_wheel

release: clean build
	twine upload dist/*

dist: clean build
	python3 setup.py sdist
	python3 setup.py bdist_wheel
	ls -l dist
