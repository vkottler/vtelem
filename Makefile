###############################################################################
MK_INFO := https://pypi.org/project/vmklib
ifeq (,$(shell which mk))
$(warning "No 'mk' in $(PATH), install 'vmklib' with 'pip' ($(MK_INFO))")
endif
ifndef MK_AUTO
$(error target this Makefile with 'mk', not '$(MAKE)' ($(MK_INFO)))
endif
###############################################################################

.PHONY: all clean edit lint run run-help readme check-env release yaml

.DEFAULT_GOAL := all

all: python-lint python-sa python-test mk-todo

RUN_ARGS := -v -p 9000 -a 0.5

edit: $(PY_PREFIX)edit

lint: $(YAML_PREFIX)lint-local $(YAML_PREFIX)lint-manifest.yaml

yaml: lint

run: $(VENV_CONC)
	@$(PYTHON_BIN)/python $($(PROJ)_DIR)/dev.py $(RUN_ARGS)

run-help: $(VENV_CONC)
	@$(PYTHON_BIN)/python $($(PROJ)_DIR)/dev.py -h

GRIP_PORT := 0.0.0.0:0

readme:
	mk grip-render GRIP_PORT=$(GRIP_PORT)

render-%:
	mk grip-render GRIP_FILE=docs/$*.md GRIP_PORT=$(GRIP_PORT)

$($(PROJ)_DIR)/.secrets:
	@rm -f $@
	@echo "export GITHUB_API_USER=$$USER" >> $@
	@echo "export GITHUB_API_TOKEN=`secrethub read vkottler/github/tokens/public_repo-api-token`" >> $@
	+@echo "wrote '$@'"

check-env: | $($(PROJ)_DIR)/.secrets
ifndef GITHUB_API_USER
	$(error GITHUB_API_USER not set, run 'source $($(PROJ)_DIR)/.secrets')
endif
ifndef GITHUB_API_TOKEN
	$(error GITHUB_API_TOKEN not set, run 'source $($(PROJ)_DIR)/.secrets')
endif

release: check-env $(DZ_PREFIX)sync
	@rm -f $($(PROJ)_DIR)/local/generated/git.*
	$(PYTHON_BIN)/dz $(DZ_ARGS) -c
	$(PYTHON_BIN)/dz $(DZ_ARGS)
	@chmod +x $($(PROJ)_DIR)/datazen-out/release.sh
	$($(PROJ)_DIR)/datazen-out/release.sh
