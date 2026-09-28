# Anexos privados Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir anexos de OS sem tornar arquivos públicos.

**Architecture:** Armazenar metadados e arquivo privado por OS; centralizar autorização de leitura/escrita; servir arquivos por view autenticada. O portal reutiliza os escopos já definidos para cliente e técnico.

**Tech Stack:** Python 3.12, Django 6, SQLite, Django TestCase.

**Spec:** `docs/superpowers/specs/2026-09-27-comunicacao-documentos-relatorios-design.md`

## Global Constraints

- Permitir PDF, JPEG, PNG, WEBP, DOC e DOCX; máximo de 5 MB e 10 anexos por OS.
- Mídia privada configurada por ambiente, fora de `static/` e ignorada pelo Git.
- Cliente/técnico só acessa OS próprias/atribuídas; tentativa externa retorna 404.
- Exclusão é autor, supervisor ou superusuário.

## Review Focus

- Arquivo com extensão permitida mas conteúdo incompatível é rejeitado.
- Upload vazio ou acima de 5 MB não cria arquivo nem registro.
- Décimo primeiro anexo é rejeitado sem apagar anexos existentes.
- Nome fornecido pelo usuário nunca controla o caminho do arquivo.
- Remoção não autorizada deixa o registro e arquivo intactos.

### Task 1: Configuração e modelo privado

**Files:** Modify `sistema_os/settings.py`, `.gitignore`, `ordens/models.py`, `ordens/admin.py`, `ordens/tests.py`; Create migration.

**Interfaces:** Produces `AnexoOrdemServico`, `MEDIA_ROOT` private and `arquivo_eh_permitido(upload) -> bool`.

- [ ] **Step 1: Write failing tests** for accepted/rejected extension/content, size limit and per-OS limit.
- [ ] **Step 2: Run focused tests** and confirm validation/model is absent.
- [ ] **Step 3: Implement media configuration, validation, metadata and migration**; use generated upload names rather than user path fragments.
- [ ] **Step 4: Run focused tests and migration check**; expect pass.
- [ ] **Step 5: Commit** with `feat: add private service attachments`.

### Task 2: Autorizações e operações de arquivo

**Files:** Modify `ordens/permissions.py`, `ordens/forms.py`, `ordens/views.py`, `ordens/urls.py`, `ordens/tests.py`.

**Interfaces:** Produces `ordem_acessivel_ou_404(user, ordem_id)`, upload, download and delete views.

- [ ] **Step 1: Write failing tests** for customer/technician own access, foreign URL 404 and delete authorization.
- [ ] **Step 2: Run focused tests** and confirm the routes are missing.
- [ ] **Step 3: Implement server-side authorization and atomic upload/delete flows**; download uses `FileResponse` only after authorization.
- [ ] **Step 4: Run focused tests and full suite**; expect pass.
- [ ] **Step 5: Commit** with `feat: secure attachment access`.

### Task 3: Interface e documentação de hospedagem

**Files:** Modify customer/technician order templates, `docs/pythonanywhere.md`, `README.md`, `ordens/tests.py`.

**Interfaces:** Uses upload/download routes; presents allowed formats, size limit and attachment list.

- [ ] **Step 1: Write failing template/view tests** for attachment section visibility and foreign file absence.
- [ ] **Step 2: Run focused tests** and confirm expected UI is absent.
- [ ] **Step 3: Add responsive attachment sections and deployment instructions** for a private `SEOS_MEDIA_ROOT` path, with no actual paths/secrets committed.
- [ ] **Step 4: Run full suite, check and migration check**; expect pass.
- [ ] **Step 5: Commit** with `docs: document private attachment storage`.
