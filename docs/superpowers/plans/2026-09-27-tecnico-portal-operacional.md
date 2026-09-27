# Portal Operacional do Técnico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o cargo Técnico e uma fila segura de OS atribuídas, preservando o portal do cliente e o Admin de supervisão.

**Architecture:** Centralizar regras de cargo e escopo no domínio; as views técnicas só recebem uma OS já autorizada. O Admin preserva seu papel atual e o portal existente do cliente recebe somente linha do tempo/paginação.

**Tech Stack:** Python 3.12, Django 6, SQLite, Django TestCase.

**Spec:** `docs/superpowers/specs/2026-09-27-evolucao-seos-design.md`

## Global Constraints

- Não recriar dashboard, filtros, impressão, estoque ou portal do cliente existentes.
- Técnico não é `is_staff`; Técnico/Admin continua com Admin.
- Proteger todas as consultas no servidor; não confiar em elementos ocultos.
- Não implementar notificações, anexos ou relatórios nesta fase.

## Review Focus

- Técnico não pode obter OS de outro técnico por URL ou POST.
- Cliente não pode obter histórico de outro cliente.
- Atendente/almoxarife não podem entrar na fila técnica.
- Técnico/Admin existente mantém acesso administrativo.
- Status inválido não altera OS nem cria histórico.

### Task 1: Cargo Técnico e elegibilidade de responsável

**Files:** Modify `ordens/models.py`, `ordens/admin.py`, `ordens/tests.py`; Create migration `ordens/migrations/0020_usuario_cargo_tecnico.py`.

**Interfaces:** Produces `Usuario.CARGO_TECNICO`, `eh_tecnico_operacional() -> bool`, `pode_ser_responsavel_tecnico() -> bool`.

- [ ] **Step 1: Write failing tests** — técnico operacional não é staff e atendente/almoxarife não são responsáveis elegíveis.
- [ ] **Step 2: Run red test** — `python manage.py test ordens.tests.CargoTecnicoTests -v 2`; expected failure for missing cargo/methods.
- [ ] **Step 3: Implement minimal model/admin/migration changes** — cargo `tecnico`, `is_staff` somente para cargos administrativos, e seleção explícita de responsáveis.
- [ ] **Step 4: Run green checks** — `python manage.py test ordens.tests.CargoTecnicoTests -v 2 && python manage.py makemigrations --check && python manage.py check`.
- [ ] **Step 5: Commit** — `git commit -am "feat: add operational technician role"`.

### Task 2: Autorização central e rotas do portal

**Files:** Create `ordens/permissions.py`; Modify `ordens/views.py`, `ordens/urls.py`, `ordens/tests.py`.

**Interfaces:** Produces `ordens_do_tecnico(user)`, `ordem_do_tecnico_ou_404(user, ordem_id)` and a redirect to `minha_fila`.

- [ ] **Step 1: Write failing tests** — técnico redireciona à fila e recebe 404 para OS de outro técnico.
- [ ] **Step 2: Run red test** — `python manage.py test ordens.tests.PortalAuthorizationTests -v 2`.
- [ ] **Step 3: Implement scoped query helpers and routes** — use `select_related` and `Http404`; Admin-facing roles keep `/admin/`.
- [ ] **Step 4: Run green test** — `python manage.py test ordens.tests.PortalAuthorizationTests -v 2`.
- [ ] **Step 5: Commit** — `git commit -am "feat: scope portal access by role"`.

### Task 3: Fila e atualização limitada do técnico

**Files:** Modify `ordens/forms.py`, `ordens/views.py`, `ordens/urls.py`, `ordens/tests.py`; Create `ordens/templates/ordens/minha_fila.html`, `ordens/templates/ordens/detalhe_ordem_tecnico.html`, `ordens/static/portal/tecnico.css`.

**Interfaces:** Produces `AtualizacaoTecnicoForm`, `minha_fila`, `detalhe_ordem_tecnico`, and `atualizar_ordem_tecnico`.

- [ ] **Step 1: Write failing tests** — fila contém somente OS atribuídas; POST de status válido gera histórico/auditoria; POST fora do escopo retorna 404.
- [ ] **Step 2: Run red test** — `python manage.py test ordens.tests.FilaTecnicoTests -v 2`.
- [ ] **Step 3: Implement minimal form, views and templates** — permitir somente status, avaliação e serviço planejado; nunca aceitar cliente ou técnico pelo POST.
- [ ] **Step 4: Run green and suite** — `python manage.py test ordens.tests.FilaTecnicoTests -v 2 && python manage.py test -v 2`.
- [ ] **Step 5: Commit** — `git commit -am "feat: add technician work queue"`.

### Task 4: Linha do tempo e paginação do cliente

**Files:** Modify `ordens/views.py`, `ordens/templates/lista_ordens.html`, `ordens/tests.py`.

**Interfaces:** Produces `page_obj` and histories preloaded only for the logged-in client.

- [ ] **Step 1: Write failing tests** — cliente vê histórico próprio e contexto paginado.
- [ ] **Step 2: Run red test** — `python manage.py test ordens.tests.PortalClienteTests -v 2`.
- [ ] **Step 3: Implement paginated restricted queryset and timeline in the existing modal**.
- [ ] **Step 4: Run green and suite** — `python manage.py test ordens.tests.PortalClienteTests -v 2 && python manage.py test -v 2`.
- [ ] **Step 5: Commit** — `git commit -am "feat: add customer order timeline"`.

### Task 5: Documentar e validar

**Files:** Modify `README.md`, `docs/pythonanywhere.md`, `ordens/tests.py`.

- [ ] **Step 1: Write failing regression test** — técnico não recebe Admin; supervisor recebe.
- [ ] **Step 2: Run red/green verification** — `python manage.py test -v 2 && python manage.py check && python manage.py makemigrations --check`.
- [ ] **Step 3: Document role matrix and deploy order without credentials/secrets**.
- [ ] **Step 4: Commit** — `git commit -am "docs: document technician portal workflow"`.
