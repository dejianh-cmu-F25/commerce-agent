.PHONY: ci ci-fast ci-image smoke-image setup-hooks serve

# Local CI gate (constitution GH-4).
ci:
	./scripts/ci.sh

# Same gate, skipping `npm ci` (reuse node_modules) — for pre-push.
ci-fast:
	./scripts/ci.sh --fast

# Full gate including the Docker image build + container smoke test (slow).
ci-image:
	./scripts/ci.sh --with-image

# Container smoke test against an existing image (keyless; no key needed).
smoke-image:
	./scripts/smoke_container.sh

# One-time: route git hooks to .githooks (enables the pre-push gate).
setup-hooks:
	git config core.hooksPath .githooks
	@echo "git hooks enabled: .githooks/pre-push runs 'make ci-fast'"

serve:
	./scripts/serve.sh
