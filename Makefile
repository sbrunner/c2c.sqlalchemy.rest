PIP_CMD ?= .build/venv/bin/pip
PIP_INSTALL_ARGS += install --trusted-host pypi.camptocamp.net

.PHONY: help
help:
	@echo "Usage: $(MAKE) <target>"
	@echo
	@echo "Main targets:"
	@echo
	@echo "- build 		Build and configure the project"
#	@echo "- tests 		Perform a number of tests on the code"
	@echo "- checks		Perform a number of checks on the code"
	@echo "- clean 		Remove generated files"
	@echo "- cleanall 		Remove all the build artefacts"

.PHONY: build
build: .build/requirements.timestamp

#.PHONY: tests
#tests: nose

.PHONY: checks
checks: flake8

.PHONY: clean
clean:
	rm -f .build/dev-requirements.timestamp
	rm -f .build/venv.timestamp

.PHONY: cleanall
cleanall: clean
	rm -rf .build

#.PHONY: nose
#nose: .build/dev-requirements.timestamp .build/requirements.timestamp
#	.build/venv/bin/python setup.py nosetests

.PHONY: flake8
flake8: .build/venv/bin/flake8
	# E712 is not compatible with SQLAlchemy
	find c2c -name \*.py | xargs .build/venv/bin/flake8 \
		--ignore=E712 \
		--max-complexity=20 \
		--max-line-length=100 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) [0-9\-]*$(shell date +%Y), Camptocamp SA"
	.build/venv/bin/flake8 \
		--ignore=E712 \
		--max-complexity=20 \
		--max-line-length=100 \
		--copyright-check \
		--copyright-min-file-size=1 \
		--copyright-regexp="Copyright \(c\) [0-9\-]*$(shell date +%Y), Camptocamp SA" \
		setup.py travis/quote
	travis/quote `find c2c -name '*.py'` setup.py

.build/venv/bin/flake8: .build/dev-requirements.timestamp

.build/dev-requirements.timestamp: .build/venv.timestamp dev-requirements.txt
	$(PIP_CMD) $(PIP_INSTALL_ARGS) -r dev-requirements.txt
	touch $@

.build/venv.timestamp:
	mkdir -p $(dir $@)
	virtualenv --setuptools --no-site-packages .build/venv
	$(PIP_CMD) install \
		--index-url http://pypi.camptocamp.net/pypi \
		'pip>=7' 'setuptools>=12'
	touch $@

.build/requirements.timestamp: .build/venv.timestamp setup.py \
		requirements.txt
	$(PIP_CMD) $(PIP_INSTALL_ARGS) -r requirements.txt
	touch $@
