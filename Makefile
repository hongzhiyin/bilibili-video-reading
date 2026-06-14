.PHONY: install install-cli install-command sync-skill check doctor update package-release

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

update:
	@./scripts/update_cli.sh

package-release:
	@./scripts/package_release.sh
