# SEOS — Comunicação, documentos e relatórios

## Objetivo e limites

Complementar o SEOS para a apresentação acadêmica com notificações internas,
anexos protegidos por ordem de serviço e relatórios administrativos visuais,
exportáveis em CSV e PDF. A entrega deve continuar gratuita e compatível com
PythonAnywhere, sem enviar banco de dados, documentos, senhas ou chaves ao
GitHub.

Esta fase amplia o fluxo já existente; não recria o painel administrativo, o
portal do cliente, a fila do técnico, o estoque ou a impressão de OS.

## Perfis e autorização

| Perfil | Notificações | Anexos | Relatórios |
| --- | --- | --- | --- |
| Cliente | Próprias, sobre suas OS | Suas próprias OS | Sem acesso |
| Técnico | Próprias, sobre atribuições | OS atribuídas | Sem acesso |
| Supervisor Técnico | Operacionais e estoque | Todas as OS | Acesso completo |
| Atendente | Notificações operacionais pertinentes | OS permitidas pelo Admin | Sem acesso |
| Almoxarifado | Alertas de estoque pertinentes | Sem acesso pela nova área | Sem acesso |
| Superusuário | Todas | Todas | Acesso completo |

Toda consulta, download e criação de anexo deve validar a regra no servidor.
URLs diretas nunca podem conceder acesso por si só.

## Notificações internas

O modelo `Notificacao` terá destinatário, tipo, texto, referência opcional à
OS/peça, data de criação e data de leitura. Uma pequena central de notificações
mostra não lidas e permite marcar como lidas.

Eventos criadores:

1. alteração de status de OS: notifica o cliente vinculado;
2. atribuição ou troca de técnico: notifica o técnico responsável novo;
3. estoque que passa para abaixo (ou igual) ao mínimo: notifica supervisores
   e o almoxarifado, sem duplicar o mesmo alerta enquanto a peça permanecer em
   estoque baixo.

Notificações são internas, sem e-mail, SMS, tokens ou serviços externos. Os
eventos preservam o histórico e a auditoria que já existem.

## Anexos privados

O modelo `AnexoOrdemServico` guarda a OS, autor, nome original, arquivo,
tipo, tamanho e data. Arquivos ficam em diretório configurado como mídia
privada, fora de `static/` e sem rota pública de arquivos.

Formatos permitidos: PDF, imagens JPEG/PNG/WEBP e documentos Word DOC/DOCX.
O tamanho máximo será 5 MB por arquivo e cada OS aceitará no máximo 10 anexos.
O formulário rejeita extensão não permitida, MIME incompatível, arquivo vazio,
nome inseguro e envio sem autorização. O download usa view autenticada e só
libera o arquivo após verificar a relação do usuário com a OS. A exclusão fica
restrita ao autor, supervisor ou superusuário.

## Relatórios administrativos

Uma página própria no Admin fornecerá filtros por período, status e técnico,
com indicadores de quantidade de OS, distribuição por status, OS finalizadas,
prazo médio quando houver dados e peças em estoque baixo. Dados pessoais não
necessários não entram no resumo nem na exportação.

O mesmo conjunto filtrado é exportado em CSV e PDF. Os arquivos contêm resumo,
filtros aplicados e linhas essenciais das OS, sem CPF, telefone, endereço,
senha, chaves ou anexos. PDF será gerado no servidor a partir de template
controlado; CSV usará codificação adequada para planilhas.

## Fluxo e falhas

- Alterações inválidas mantêm os dados e informam o erro.
- Falhas de armazenamento não criam registro parcial de anexo.
- Tentativas de acessar objeto de outro usuário retornam 404, evitando revelar
  se ele existe.
- Exportações sem resultado produzem arquivo válido com cabeçalhos/resumo, sem
  erro de servidor.
- Diretório de mídia é configurado por variável de ambiente na hospedagem e
  ignorado pelo Git.

## Critérios de aceitação e testes

- Cliente/técnico não acessa notificação, anexo ou OS de outra pessoa por URL.
- Status cria notificação para o cliente correto; atribuição cria para o
  técnico correto; estoque baixo não duplica alerta contínuo.
- Formatos e limites de anexo são validados; download autorizado preserva o
  arquivo e download não autorizado retorna 404.
- Relatório aplica filtros, não expõe dados pessoais e gera CSV/PDF.
- A suíte de testes, checagem do Django e checagem de migrações passam antes
  de integrar e publicar.
