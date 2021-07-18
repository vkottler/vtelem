###############################################################################
MK_INFO := https://pypi.org/project/vmklib
ifeq (,$(shell which mk))
$(warning "No 'mk' in $(PATH), install 'vmklib' with 'pip' ($(MK_INFO))")
endif
ifndef MK_AUTO
$(error target this Makefile with 'mk', not '$(MAKE)' ($(MK_INFO)))
endif
###############################################################################

.PHONY: all clean run run-help readme

.DEFAULT_GOAL := all

all: python-lint python-sa python-test mk-todo

RUN_ARGS := -v -p 9000 -a 0.5

run: $(VENV_CONC)
	@$(PYTHON_BIN)/python $($(PROJ)_DIR)/dev.py $(RUN_ARGS)

run-help: $(VENV_CONC)
	@$(PYTHON_BIN)/python $($(PROJ)_DIR)/dev.py -h

GRIP_PORT := 0.0.0.0:0

readme:
	mk grip-render GRIP_PORT=$(GRIP_PORT)

render-%:
	mk grip-render GRIP_FILE=docs/$*.md GRIP_PORT=$(GRIP_PORT)
