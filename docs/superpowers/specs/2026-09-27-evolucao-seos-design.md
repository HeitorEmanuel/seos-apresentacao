# Evolução do SEOS — Design aprovado

O SEOS já possui painel administrativo, busca/filtros, portal do cliente, impressão, estoque baixo e auditoria. Esta fase não os recria.

## Hierarquia

- Superusuário: controle total.
- Técnico/Admin: supervisor com acesso ao Admin.
- Técnico: novo cargo operacional; não é `is_staff`, usa somente “Minha Fila”, vê e atualiza exclusivamente OS atribuídas.
- Atendente: clientes e OS, sem estoque/auditoria/exclusão.
- Almoxarifado: estoque, sem clientes ou OS.
- Cliente: apenas as próprias OS no portal atual.

Somente Técnico, Técnico/Admin ou superusuário pode ser responsável por uma OS. O servidor, não a interface, limita a OS ao seu cliente ou técnico.

## Fase atual

Criar cargo Técnico, fila e detalhe técnico, atualização limitada de status/observações/peças, e linha do tempo paginada para o portal atual do cliente. Cada atualização cria histórico e auditoria. Não incluir nesta fase notificações, anexos ou relatórios.

## Critérios de segurança

- Técnico não acessa Admin nem OS de outro técnico.
- Cliente não acessa OS ou histórico de outro cliente.
- Status inválido e campos fora do formulário técnico não persistem.
- Cliente, atribuição e permissões não podem ser alterados pela rota técnica.

## Testes

Cobrir cargo, redirecionamento, escopo de queryset, atualização autorizada, histórico/auditoria, paginação e acesso direto não autorizado.
