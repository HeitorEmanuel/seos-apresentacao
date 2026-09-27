# Relatórios administrativos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Oferecer painel administrativo filtrável e exportação CSV/PDF sem dados pessoais desnecessários.

**Architecture:** Um módulo de consulta cria um queryset filtrado e um resumo reutilizado pela tela, CSV e PDF. Uma view administrativa aplica a mesma regra de acesso em todas as saídas.

**Tech Stack:** Python 3.12, Django 6, CSV padrão, biblioteca PDF compatível com PythonAnywhere, Django TestCase.

**Spec:** `docs/superpowers/specs/2026-09-27-comunicacao-documentos-relatorios-design.md`

## Global Constraints

- Supervisor Técnico e superusuário podem acessar; demais perfis recebem 404.
- Filtros: período, status e técnico.
- Não incluir CPF, telefone, endereço, senha, chaves, anexos ou conteúdo de anexo.
- CSV e PDF vazios permanecem arquivos válidos com cabeçalho/resumo.

## Review Focus

- Datas inválidas não produzem erro 500 nem ignoram filtros silenciosamente.
- Filtro de técnico inexistente não amplia a consulta.
- Valores de status inválidos são rejeitados/normalizados de modo explícito.
- CSV é legível no Excel em português.
- PDF e CSV aplicam exatamente os mesmos filtros exibidos na tela.

### Task 1: Consulta e métricas reutilizáveis

**Files:** Create `ordens/reporting.py`; Modify `ordens/tests.py`.

**Interfaces:** Produces `consultar_ordens_relatorio(params) -> QuerySet` and `resumo_relatorio(queryset) -> dict`.

- [ ] **Step 1: Write failing tests** for date/status/technician filtering, invalid inputs and private-field exclusion.
- [ ] **Step 2: Run focused tests** and confirm reporting helpers do not exist.
- [ ] **Step 3: Implement validated queryset and aggregate summary** with explicit selected filters.
- [ ] **Step 4: Run focused tests**; expect pass.
- [ ] **Step 5: Commit** with `feat: add reporting queries`.

### Task 2: Painel e exportação CSV

**Files:** Modify `ordens/admin.py`, `ordens/tests.py`; Create `ordens/templates/admin/ordens/relatorios.html`.

**Interfaces:** Produces admin URLs `relatorios/` and `relatorios/csv/` consuming reporting helpers.

- [ ] **Step 1: Write failing tests** for supervisor access, forbidden profile 404, applied filters and CSV headers/content.
- [ ] **Step 2: Run focused tests** and confirm URLs are missing.
- [ ] **Step 3: Implement admin view, summary cards, filter form and UTF-8 BOM CSV response**; include no personal fields.
- [ ] **Step 4: Run focused tests and full suite**; expect pass.
- [ ] **Step 5: Commit** with `feat: add administrative reports`.

### Task 3: Exportação PDF e documentação

**Files:** Modify `requirements.txt`, `ordens/admin.py`, `ordens/tests.py`, `README.md`, `docs/pythonanywhere.md`; Create a PDF template/helper.

**Interfaces:** Produces `relatorios/pdf/` response generated from the same reporting summary/queryset.

- [ ] **Step 1: Write failing test** asserting PDF content type, attachment filename and applied filter label.
- [ ] **Step 2: Run focused test** and confirm PDF endpoint is missing.
- [ ] **Step 3: Add a pinned PDF dependency compatible with Python 3.12 and implement the endpoint**; preserve no-result export behavior.
- [ ] **Step 4: Run focused tests, full suite, check and migration check**; expect pass.
- [ ] **Step 5: Commit** with `feat: export administrative report pdf`.
