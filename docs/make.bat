# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

@echo off
REM Minimal batch file for Sphinx on Windows.
REM From project root: pip install -r docs/requirements-docs.txt, then:
REM   cd docs && make.bat html

set SPHINXBUILD=sphinx-build
set SOURCEDIR=source
set BUILDDIR=build

if "%1" == "html" (
	%SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%
	echo Build finished. Open %BUILDDIR%\html\index.html
) else if "%1" == "clean" (
	rmdir /s /q %BUILDDIR% 2>nul
	echo Cleaned %BUILDDIR%
) else (
	echo Usage: make.bat html ^| clean
)
REM Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
