########################################################

# Makefile for re-worker-func
#
# useful targets (not all implemented yet!):
#   make clean               -- Clean up garbage
#   make pyflakes, make pep8 -- source code checks
#   make test ----------------- run all unit tests (export LOG=true for /tmp/ logging)

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

RPMSPECDIR := .
RPMSPEC := $(RPMSPECDIR)/re-worker-func.spec

SRCDIR := replugin/funcworker

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

# rpmcommon: sdist
# 	@mkdir -p rpm-build
# 	@cp dist/*.gz rpm-build/

# srpm: rpmcommon
# 	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
# 	--define "_builddir %{_topdir}" \
# 	--define "_rpmdir %{_topdir}" \
# 	--define "_srcrpmdir %{_topdir}" \
# 	--define "_specdir $(RPMSPECDIR)" \
# 	--define "_sourcedir %{_topdir}" \
# 	-bs $(RPMSPEC)
# 	@echo "#############################################"
# 	@echo "$(NAME) SRPM is built:"
# 	@find rpm-build -maxdepth 2 -name '$(NAME)*src.rpm' | awk '{print "    " $$1}'
# 	@echo "#############################################"

# rpm: rpmcommon
# 	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
# 	--define "_builddir %{_topdir}" \
# 	--define "_rpmdir %{_topdir}" \
# 	--define "_srcrpmdir %{_topdir}" \
# 	--define "_specdir $(RPMSPECDIR)" \
# 	--define "_sourcedir %{_topdir}" \
# 	-ba $(RPMSPEC)
# 	@echo "#############################################"
# 	@echo "$(NAME) RPMs are built:"
# 	@find rpm-build -maxdepth 2 -name '$(NAME)*.rpm' | awk '{print "    " $$1}'
# 	@echo "#############################################"
