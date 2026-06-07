.PHONY: install install-cli install-command sync-skill check doctor

install:
	@./scripts/install.sh

install-cli:
	@./scripts/install_cli.sh

install-command:
	@./scripts/install_command.sh

sync-skill:
	@./scripts/sync_skill.sh

check:
	@./scripts/check_install.sh

doctor: check
