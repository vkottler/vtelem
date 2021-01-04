###############################################################################
MK_INFO := https://pypi.org/project/vmklib
ifeq (,$(shell which mk))
$(warning "No 'mk' in $(PATH), install 'vmklib' with 'pip' ($(MK_INFO))")
endif
ifndef MK_AUTO
$(error target this Makefile with 'mk', not '$(MAKE)' ($(MK_INFO)))
endif
###############################################################################

.PHONY: all clean run run-help

.DEFAULT_GOAL := all

all: python-lint python-sa python-test mk-todo

RUN_ARGS := -v -p 9000

run: $(VENV_CONC)
	@$(PYTHON_BIN)/python $($(PROJ)_DIR)/dev.py $(RUN_ARGS)

run-help: $(VENV_CONC)
	@$(PYTHON_BIN)/python $($(PROJ)_DIR)/dev.py -h
