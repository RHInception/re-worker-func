########################################################

# Makefile for re-worker-func
#
# useful targets (not all implemented yet!):
#   make clean               -- Clean up garbage
#   make pyflakes, make pep8 -- source code checks
#   make test ----------------- run all unit tests (export LOG=true for /tmp/ logging)
#   make ci ------------------- Execute CI steps (for travis or jenkins)

########################################################

# > VARIABLE = value
#
# Normal setting of a variable - values within it are recursively
# expanded when the variable is USED, not when it's declared.
#
# > VARIABLE := value
#
# Setting of a variable with simple expansion of the values inside -
# values within it are expanded at DECLARATION time.

########################################################
NAME := re-worker-func

RPMSPECDIR := ./contrib/rpm/
RPMSPEC := $(RPMSPECDIR)/re-worker-func.spec
TESTPACKAGE := replugin
SHORTNAME := replugin

SRCDIR := replugin/funcworker

################
# For CI deps
TMPDIR = $(shell mktemp -d)
FUNCDIR := $(TMPDIR)
REWORKERDIR := $(TMPDIR)
CMDIR := $(TMPDIR)

pip:
	@echo $(FUNCDIR)
	@echo $(REWORKERDIR)
	@echo $(CMDIR)


sdist: clean
	python setup.py sdist
	rm -fR funcworker.egg-info

tests: unittests pep8 pyflakes
	:

unittests:
	@echo "#############################################"
	@echo "# Running Unit Tests"
	@echo "#############################################"
	nosetests -v --with-cover --cover-min-percentage=80 --cover-package=replugin test/

clean:
	@find . -type f -regex ".*\.py[co]$$" -delete
	@find . -type f \( -name "*~" -or -name "#*" \) -delete
	@rm -fR build dist rpm-build MANIFEST htmlcov .coverage funcworker.egg-info

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
	pep8 --ignore=E501,E121,E124 $(SRCDIR)

pyflakes:
	@echo "#############################################"
	@echo "# Running Pyflakes Sanity Tests"
	@echo "# Note: most import errors may be ignored"
	@echo "#############################################"
	-pyflakes $(SRCDIR)

rpmcommon: sdist
	@mkdir -p rpm-build
	@cp dist/*.gz rpm-build/

srpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-bs $(RPMSPEC)
	@echo "#############################################"
	@echo "$(NAME) SRPM is built:"
	@find rpm-build -maxdepth 2 -name '$(NAME)*src.rpm' | awk '{print "    " $$1}'
	@echo "#############################################"

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-ba $(RPMSPEC)
	@echo "#############################################"
	@echo "$(NAME) RPMs are built:"
	@find rpm-build -maxdepth 2 -name '$(NAME)*.rpm' | awk '{print "    " $$1}'
	@echo "#############################################"

virtualenv:
	@echo "#############################################"
	@echo "# Creating a virtualenv"
	@echo "#############################################"
	virtualenv $(NAME)env
	. $(NAME)env/bin/activate && PYTHONUSERBASE=$(NAME)env pip install -r requirements.txt
	. $(NAME)env/bin/activate && pip install pep8 nose coverage mock

#       If there are any special things to install do it here
	. $(NAME)env/bin/activate && cd $(REWORKERDIR) && wget https://github.com/RHInception/re-worker/archive/master.zip && unzip master && cd re-worker-master && pip install .
	. $(NAME)env/bin/activate && cd $(FUNCDIR) && wget https://fedorahosted.org/releases/f/u/func/func-0.28.tar.gz && tar xvzf func-0.28.tar.gz && cd func-0.28 && python ./setup.py install --root=$(NAME)env
	. $(NAME)env/bin/activate && cd $(CMDIR) && wget https://fedorahosted.org/releases/c/e/certmaster/certmaster-0.28.tar.gz  && tar xvzf certmaster-0.28.tar.gz && cd certmaster-0.28 && python setup.py install --root=$(NAME)env


ci-unittests:
	@echo "#############################################"
	@echo "# Running Unit Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && nosetests -v --with-cover --cover-min-percentage=80 --cover-package=$(TESTPACKAGE) test/

ci-list-deps:
	@echo "#############################################"
	@echo "# Listing all pip deps"
	@echo "#############################################"
	. $(NAME)env/bin/activate && pip freeze

ci-pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && pep8 --ignore=E501,E121,E124 $(SHORTNAME)/


ci: clean virtualenv ci-list-deps ci-pep8 ci-unittests
	:
