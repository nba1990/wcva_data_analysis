# Minimal Makefile for Sphinx: build HTML docs.
# From project root: pip install -r docs/requirements-docs.txt, then:
#   cd docs && make html
# Output: docs/build/html/index.html

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

.PHONY: html clean help

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

html:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
	@echo "Build finished. Open $(BUILDDIR)/html/index.html"

clean:
	rm -rf "$(BUILDDIR)"
