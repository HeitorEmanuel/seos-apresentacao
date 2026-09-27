# Notificações internas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Informar usuários sobre eventos relevantes sem serviços externos.

**Architecture:** Um modelo de notificação e um serviço de domínio centralizam destinatários e deduplicação. Views exibem e marcam como lidas; Admin e fluxos de OS/estoque chamam o serviço sem duplicar regras.

**Tech Stack:** Python 3.12, Django 6, SQLite, Django TestCase.

**Spec:** `docs/superpowers/specs/2026-09-27-comunicacao-documentos-relatorios-design.md`

## Global Constraints

- Não usar e-mail, SMS, tokens ou serviços externos.
- Não expor notificações de outro usuário por consulta ou URL.
- Alerta contínuo de estoque baixo não pode duplicar.
- Manter auditoria e histórico existentes.

## Review Focus

- Usuário anônimo deve ir ao login, sem receber lista de notificações.
- Marcar como lida notificação de outro usuário retorna 404.
- Reatribuir a mesma OS ao mesmo técnico não cria alerta novo.
- Reposição acima do mínimo permite um novo alerta caso a peça volte a ficar baixa.
- Cliente inexistente na OS não deve impedir atualização ou criar notificação inválida.

### Task 1: Modelo e serviço de notificações

**Files:** Modify `ordens/models.py`, `ordens/admin.py`, `ordens/tests.py`; Create migration.

**Interfaces:** Produces `Notificacao` and `criar_notificacao(destinatario, tipo, mensagem, ordem=None, peca=None) -> Notificacao | None`.

- [ ] **Step 1: Write failing model/service tests** for notification ownership, status recipient and stock-alert deduplication.
- [ ] **Step 2: Run the focused tests** and confirm they fail because the model/service do not exist.
- [ ] **Step 3: Implement the model, migration and service** with types `status_os`, `atribuicao_tecnico`, `estoque_baixo`; enforce one unread low-stock alert per recipient/piece.
- [ ] **Step 4: Run focused tests and `manage.py makemigrations --check`**; expect pass and no pending migration.
- [ ] **Step 5: Commit** with `feat: add internal notifications`.

### Task 2: Emitir eventos operacionais

**Files:** Modify `ordens/models.py`, `ordens/admin.py`, `ordens/tests.py`.

**Interfaces:** Consumes `criar_notificacao`; produces notifications from OS status/assignment and stock changes.

- [ ] **Step 1: Write failing integration tests** for client status notification, new technician assignment and low-stock/recovery lifecycle.
- [ ] **Step 2: Run the focused tests** and confirm missing event behavior.
- [ ] **Step 3: Implement event calls** after successful persistence, preserving existing history/audit behavior and avoiding events during failed transactions.
- [ ] **Step 4: Run focused tests and full suite**; expect pass.
- [ ] **Step 5: Commit** with `feat: notify service events`.

### Task 3: Central de notificações

**Files:** Modify `ordens/views.py`, `ordens/urls.py`, `ordens/tests.py`; Create `ordens/templates/ordens/notificacoes.html`.

**Interfaces:** Produces `notificacoes` and `marcar_notificacao_lida` authenticated views.

- [ ] **Step 1: Write failing view tests** for own list, unread-to-read transition and foreign notification 404.
- [ ] **Step 2: Run the focused tests** and confirm routes do not exist.
- [ ] **Step 3: Implement paginated own-notification queryset and POST-only read action**; include a portal link for client/technician.
- [ ] **Step 4: Run focused tests and full suite**; expect pass.
- [ ] **Step 5: Commit** with `feat: add notification center`.
