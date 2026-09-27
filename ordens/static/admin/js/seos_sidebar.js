
(function () {
    function normalizar(texto) {
        return (texto || '')
            .toString()
            .trim()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    }

    function encontrarItemPorTexto(textoAlvo) {
        const alvo = normalizar(textoAlvo);
        const links = Array.from(document.querySelectorAll('.main-sidebar a, .sidebar a, .nav-sidebar a'));

        return links.find(function (link) {
            return normalizar(link.textContent).includes(alvo);
        });
    }

    function removerItemPorTexto(textoAlvo) {
        const link = encontrarItemPorTexto(textoAlvo);
        if (!link) return;

        const item = link.closest('li') || link.closest('.nav-item');
        if (item) {
            item.remove();
        }
    }

    function criarSeparador(titulo) {
        const li = document.createElement('li');
        li.className = 'nav-header seos-sidebar-separator';
        li.textContent = titulo;
        return li;
    }

    function inserirSeparadorAntes(textoItem, titulo) {
        const link = encontrarItemPorTexto(textoItem);
        if (!link) return;

        const item = link.closest('li') || link.closest('.nav-item');
        if (!item || !item.parentElement) return;

        const jaExiste = Array.from(item.parentElement.querySelectorAll('.seos-sidebar-separator'))
            .some(function (sep) {
                return normalizar(sep.textContent) === normalizar(titulo);
            });

        if (!jaExiste) {
            item.parentElement.insertBefore(criarSeparador(titulo), item);
        }
    }

    function inserirPainelCliente() {
        if (encontrarItemPorTexto('Painel do Cliente')) return;

        const dashboard = encontrarItemPorTexto('Dashboard');
        if (!dashboard) return;

        const dashboardItem = dashboard.closest('li') || dashboard.closest('.nav-item');
        if (!dashboardItem || !dashboardItem.parentElement) return;

        const novoItem = document.createElement('li');
        novoItem.className = 'nav-item seos-client-panel-item';
        novoItem.innerHTML = '<a href="/" class="nav-link seos-client-panel-link"><i class="nav-icon fas fa-arrow-left"></i><p>Painel do Cliente</p></a>';

        dashboardItem.parentElement.insertBefore(novoItem, dashboardItem.nextSibling);
    }


    function inserirBotaoClienteNoRodape() {
        const sidebar = document.querySelector('.main-sidebar .sidebar') || document.querySelector('.sidebar');
        if (!sidebar || sidebar.querySelector('.seos-sidebar-client-footer')) return;

        const box = document.createElement('div');
        box.className = 'seos-sidebar-client-footer';
        box.innerHTML = '<a href="/" class="seos-sidebar-client-button"><i class="fas fa-arrow-left"></i><span>Voltar ao Painel do Cliente</span></a>';

        sidebar.appendChild(box);
    }

    function organizarSidebar() {
        removerItemPorTexto('Históricos de Serviço');
        removerItemPorTexto('Historicos de Servico');

        inserirPainelCliente();
        inserirBotaoClienteNoRodape();

        inserirSeparadorAntes('Ordens de Serviço', 'ATENDIMENTO');
        inserirSeparadorAntes('Usuários', 'CLIENTES E EQUIPE');
        inserirSeparadorAntes('Usuarios', 'CLIENTES E EQUIPE');
        inserirSeparadorAntes('Peças', 'ESTOQUE');
        inserirSeparadorAntes('Pecas', 'ESTOQUE');
        inserirSeparadorAntes('Entrada e Saída de Peças', 'ESTOQUE');
        inserirSeparadorAntes('Movimentações de Estoque', 'ESTOQUE');
        inserirSeparadorAntes('Auditoria do Sistema', 'AUDITORIA');
        inserirSeparadorAntes('Registros do Sistema', 'AUDITORIA');
        inserirSeparadorAntes('Grupos', 'PERMISSÕES');
    }

    document.addEventListener('DOMContentLoaded', organizarSidebar);
    setTimeout(organizarSidebar, 300);
    setTimeout(organizarSidebar, 900);
})();





(function () {
    function selecionarLinhaCampo(classe) {
        return document.querySelector('.seos-pecas-fieldset .form-row.' + classe);
    }

    function grupoTemConteudo(grupo) {
        if (!grupo) return false;
        return Array.from(grupo.querySelectorAll('input, select, textarea')).some(function (campo) {
            return campo.value && String(campo.value).trim() !== '';
        });
    }

    function limparGrupo(grupo) {
        if (!grupo) return;
        grupo.querySelectorAll('input, select, textarea').forEach(function (campo) {
            if (campo.tagName === 'SELECT') {
                campo.selectedIndex = 0;
                campo.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                campo.value = '';
            }
        });
    }

    function construirCardPeca(idx) {
        const linhaPeca = selecionarLinhaCampo('field-movimentacao_peca_' + idx);
        const linhaPreview = selecionarLinhaCampo('field-visual_detalhes_peca_' + idx);
        const linhaObs = selecionarLinhaCampo('field-movimentacao_observacao_' + idx);
        if (!linhaPeca || !linhaPreview || !linhaObs) return null;

        const card = document.createElement('div');
        card.className = 'seos-peca-item-card';
        card.dataset.idx = String(idx);

        const cabecalho = document.createElement('div');
        cabecalho.className = 'seos-peca-item-header';
        cabecalho.innerHTML = '<div><div class="seos-peca-item-title">Peça ' + idx + '</div><div class="seos-peca-item-subtitle">Selecione a peça, confira os detalhes e informe a quantidade usada.</div></div>';

        if (idx > 1) {
            const remover = document.createElement('button');
            remover.type = 'button';
            remover.className = 'seos-peca-remove-btn';
            remover.textContent = 'Remover esta peça';
            remover.addEventListener('click', function () {
                limparGrupo(card);
                card.classList.add('is-hidden');
                atualizarBotoesAdicionar();
            });
            cabecalho.appendChild(remover);
        }

        card.appendChild(cabecalho);
        card.appendChild(linhaPeca);
        card.appendChild(linhaPreview);
        card.appendChild(linhaObs);
        return card;
    }

    let painel = null;
    let cards = [];
    let botoesAdicionar = null;

    function atualizarBotoesAdicionar() {
        if (!botoesAdicionar || !cards.length) return;
        botoesAdicionar.innerHTML = '';
        const ocultos = cards.filter(function (card, i) { return i > 0 && card.classList.contains('is-hidden'); });
        if (!ocultos.length) return;

        const proximo = ocultos[0];
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'seos-peca-add-btn';
        btn.textContent = '+ Adicionar outra peça';
        btn.addEventListener('click', function () {
            proximo.classList.remove('is-hidden');
            atualizarBotoesAdicionar();
            const select = proximo.querySelector('select');
            if (select) select.focus();
        });
        botoesAdicionar.appendChild(btn);
    }

    function organizarPainelPecasOS() {
        const fieldset = document.querySelector('.seos-pecas-fieldset');
        if (!fieldset || fieldset.dataset.cleanMounted === '1') return;

        const linhaHistorico = selecionarLinhaCampo('field-visual_pecas_movimentadas');
        if (!linhaHistorico) return;

        painel = document.createElement('div');
        painel.className = 'seos-pecas-panel-clean';

        cards = [1,2,3].map(construirCardPeca).filter(Boolean);
        cards.forEach(function (card, index) {
            if (index > 0 && !grupoTemConteudo(card)) card.classList.add('is-hidden');
            painel.appendChild(card);
        });

        botoesAdicionar = document.createElement('div');
        botoesAdicionar.className = 'seos-peca-add-actions';
        painel.appendChild(botoesAdicionar);
        atualizarBotoesAdicionar();

        const caixaRegistros = document.createElement('div');
        caixaRegistros.className = 'seos-pecas-registradas-box';
        caixaRegistros.innerHTML = '<div class="seos-pecas-registradas-title">Peças já lançadas na OS</div><div class="seos-pecas-registradas-note">As peças já registradas aparecem abaixo para você acompanhar o que já foi usado.</div>';
        caixaRegistros.appendChild(linhaHistorico);
        painel.appendChild(caixaRegistros);

        fieldset.appendChild(painel);
        fieldset.dataset.cleanMounted = '1';
    }

    document.addEventListener('DOMContentLoaded', organizarPainelPecasOS);
    setTimeout(organizarPainelPecasOS, 300);
    setTimeout(organizarPainelPecasOS, 900);
})();


(function () {
    function parseJsonSeguro(valor) {
        try {
            return JSON.parse(valor || '{}');
        } catch (erro) {
            return {};
        }
    }

    function formatarMoeda(valor) {
        const numero = Number(String(valor || '0').replace(',', '.'));
        if (Number.isNaN(numero)) return 'R$ 0,00';

        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(numero);
    }

    function acharCaixaPreview(select) {
        const alvoDireto = select.dataset.previewTarget;
        if (alvoDireto) {
            const caixa = document.getElementById(alvoDireto);
            if (caixa) return caixa;
        }

        const nome = select.getAttribute('name') || select.getAttribute('id') || '';
        const match = nome.match(/movimentacao_peca_(\d+)/);
        if (match) {
            return document.getElementById('seos-peca-preview-' + match[1]);
        }

        return null;
    }

    function acharDadosPecas(select) {
        if (select.dataset.pecasJson) {
            return parseJsonSeguro(select.dataset.pecasJson);
        }

        const primeiroComDados = document.querySelector('select.seos-peca-select[data-pecas-json]');
        if (primeiroComDados) {
            return parseJsonSeguro(primeiroComDados.dataset.pecasJson);
        }

        return {};
    }

    function renderizarPreviewPeca(select) {
        if (!select || !select.matches('select')) return;

        const caixa = acharCaixaPreview(select);
        if (!caixa) return;

        const dadosPecas = acharDadosPecas(select);
        const dados = dadosPecas[String(select.value)];

        if (!dados) {
            caixa.innerHTML = '<div class="seos-peca-preview-empty">Selecione uma peça para ver os detalhes.</div>';
            return;
        }

        caixa.innerHTML = [
            '<div class="seos-peca-preview-title">' + dados.nome + ' (' + dados.codigo + ')</div>',
            '<div class="seos-peca-preview-grid">',
                '<div class="seos-peca-preview-card"><span class="label">Descrição</span><span class="value">' + (dados.descricao || 'Sem descrição cadastrada.') + '</span></div>',
                '<div class="seos-peca-preview-card"><span class="label">Valor unitário</span><span class="value">' + formatarMoeda(dados.valor_unitario) + '</span></div>',
                '<div class="seos-peca-preview-card"><span class="label">Preço de varejo</span><span class="value">' + formatarMoeda(dados.preco_varejo) + '</span></div>',
                '<div class="seos-peca-preview-card"><span class="label">Estoque</span><span class="value">' + dados.estoque + ' un. | mínimo: ' + dados.estoque_minimo + '</span></div>',
            '</div>'
        ].join('');
    }

    function ativarPreviewPecasOS() {
        const selects = Array.from(document.querySelectorAll(
            'select.seos-peca-select, select[name^="movimentacao_peca_"], select[id^="id_movimentacao_peca_"]'
        ));

        selects.forEach(function (select) {
            renderizarPreviewPeca(select);

            if (select.dataset.seosPreviewLigado === '1') return;
            select.dataset.seosPreviewLigado = '1';

            select.addEventListener('change', function () {
                renderizarPreviewPeca(select);
            });

            select.addEventListener('input', function () {
                renderizarPreviewPeca(select);
            });
        });
    }

    // Jazzmin/AdminLTE pode trocar o select por Select2. Por isso escutamos mudanças no documento inteiro.
    document.addEventListener('change', function (event) {
        const alvo = event.target;
        if (alvo && alvo.matches && alvo.matches('select.seos-peca-select, select[name^="movimentacao_peca_"], select[id^="id_movimentacao_peca_"]')) {
            renderizarPreviewPeca(alvo);
        }
    }, true);

    document.addEventListener('DOMContentLoaded', ativarPreviewPecasOS);
    setTimeout(ativarPreviewPecasOS, 250);
    setTimeout(ativarPreviewPecasOS, 750);
    setTimeout(ativarPreviewPecasOS, 1500);
})();


/* --- SEOS 16.13: botão manual para atualizar detalhes da peça --- */
(function () {
    function dinheiro(valor) {
        const numero = Number(String(valor || '0').replace(',', '.'));
        if (Number.isNaN(numero)) return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numero);
    }

    function lerPecasDoSelect(select) {
        if (!select) return {};

        if (select.dataset && select.dataset.pecasJson) {
            try {
                return JSON.parse(select.dataset.pecasJson || '{}');
            } catch (erro) {
                return {};
            }
        }

        const qualquerSelect = document.querySelector('select[data-pecas-json]');
        if (qualquerSelect && qualquerSelect.dataset && qualquerSelect.dataset.pecasJson) {
            try {
                return JSON.parse(qualquerSelect.dataset.pecasJson || '{}');
            } catch (erro) {
                return {};
            }
        }

        return {};
    }

    function encontrarSelectPorIndice(indice) {
        return (
            document.querySelector('select[name="movimentacao_peca_' + indice + '"]') ||
            document.querySelector('select#id_movimentacao_peca_' + indice) ||
            document.querySelector('select[data-peca-index="' + indice + '"]')
        );
    }

    function atualizarDetalhesPeca(indice) {
        const select = encontrarSelectPorIndice(indice);
        const preview = document.getElementById('seos-peca-preview-' + indice);

        if (!preview || !select) return;

        const pecas = lerPecasDoSelect(select);
        const selecionada = String(select.value || '');
        const dados = pecas[selecionada];

        if (!dados) {
            preview.innerHTML = '<div class="seos-peca-preview-empty">Selecione uma peça e clique em “Atualizar detalhes”.</div>';
            return;
        }

        preview.innerHTML = ''
            + '<div class="seos-peca-preview-title">' + dados.nome + ' (' + dados.codigo + ')</div>'
            + '<div class="seos-peca-preview-grid">'
            + '<div class="seos-peca-preview-card"><span class="label">Descrição</span><span class="value">' + (dados.descricao || 'Sem descrição cadastrada.') + '</span></div>'
            + '<div class="seos-peca-preview-card"><span class="label">Valor unitário</span><span class="value">' + dinheiro(dados.valor_unitario) + '</span></div>'
            + '<div class="seos-peca-preview-card"><span class="label">Preço de varejo</span><span class="value">' + dinheiro(dados.preco_varejo) + '</span></div>'
            + '<div class="seos-peca-preview-card"><span class="label">Estoque</span><span class="value">' + dados.estoque + ' un. | mínimo: ' + dados.estoque_minimo + '</span></div>'
            + '</div>';
    }

    function ligarBotoesDeDetalhes() {
        document.querySelectorAll('.seos-peca-refresh-btn').forEach(function (botao) {
            if (botao.dataset.seosLigado === '1') return;
            botao.dataset.seosLigado = '1';

            botao.addEventListener('click', function () {
                atualizarDetalhesPeca(botao.dataset.pecaIndex || '1');
            });
        });

        document.querySelectorAll('select[name^="movimentacao_peca_"], select[id^="id_movimentacao_peca_"]').forEach(function (select) {
            if (select.dataset.seosAutoPreview === '1') return;
            select.dataset.seosAutoPreview = '1';

            select.addEventListener('change', function () {
                const nome = select.getAttribute('name') || select.getAttribute('id') || '';
                const match = nome.match(/movimentacao_peca_(\d+)/);
                if (match) atualizarDetalhesPeca(match[1]);
            });
        });
    }

    document.addEventListener('click', function (event) {
        const botao = event.target.closest ? event.target.closest('.seos-peca-refresh-btn') : null;
        if (botao) {
            atualizarDetalhesPeca(botao.dataset.pecaIndex || '1');
        }
    }, true);

    document.addEventListener('DOMContentLoaded', ligarBotoesDeDetalhes);
    setTimeout(ligarBotoesDeDetalhes, 250);
    setTimeout(ligarBotoesDeDetalhes, 900);
    setTimeout(ligarBotoesDeDetalhes, 1800);

    window.seosAtualizarDetalhesPeca = atualizarDetalhesPeca;
})();


/* --- SEOS 17.0: lista temporária ilimitada de peças da OS --- */
(function () {
    function moeda(valor) {
        const numero = Number(String(valor || '0').replace(',', '.'));
        if (Number.isNaN(numero)) return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numero);
    }

    function htmlSeguro(valor) {
        return String(valor ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function campo(seletor) {
        return document.querySelector(seletor);
    }

    function selectPeca() {
        return campo('#id_movimentacao_peca_temp') || campo('select[name="movimentacao_peca_temp"]');
    }

    function inputQtd() {
        return campo('#id_movimentacao_quantidade_temp') || campo('input[name="movimentacao_quantidade_temp"]');
    }

    function inputObs() {
        return campo('#id_movimentacao_observacao_temp') || campo('input[name="movimentacao_observacao_temp"]');
    }

    function hiddenJson() {
        return campo('#id_pecas_usadas_json') || campo('input[name="pecas_usadas_json"]');
    }

    function previewBox() {
        return campo('#seos-peca-preview-temp');
    }

    function painelLista() {
        return campo('#seos-pecas-temp-list');
    }

    function statusLista() {
        return campo('#seos-pecas-temp-status');
    }

    function dadosPecas() {
        const select = selectPeca();
        if (!select) return {};
        try {
            return JSON.parse(select.dataset.pecasJson || '{}');
        } catch (erro) {
            return {};
        }
    }

    function getLista() {
        const hidden = hiddenJson();
        if (!hidden || !hidden.value) return [];
        try {
            const lista = JSON.parse(hidden.value);
            return Array.isArray(lista) ? lista : [];
        } catch (erro) {
            return [];
        }
    }

    function setLista(lista) {
        const hidden = hiddenJson();
        if (hidden) {
            hidden.value = JSON.stringify(lista);
            hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
        renderLista();
    }

    function limparCamposTemporarios() {
        const select = selectPeca();
        const qtd = inputQtd();
        const obs = inputObs();

        if (select) {
            select.value = '';
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }
        if (qtd) qtd.value = '';
        if (obs) obs.value = '';
        atualizarPreview();
    }

    function atualizarPreview() {
        const select = selectPeca();
        const box = previewBox();
        if (!select || !box) return;

        const dados = dadosPecas()[String(select.value || '')];

        if (!dados) {
            box.innerHTML = '<div class="seos-peca-preview-empty">Selecione uma peça para ver os detalhes.</div>';
            return;
        }

        box.innerHTML =
            '<div class="seos-peca-preview-title">' + htmlSeguro(dados.nome) + ' (' + htmlSeguro(dados.codigo) + ')</div>' +
            '<div class="seos-peca-preview-grid">' +
                '<div class="seos-peca-preview-card"><span class="label">Descrição</span><span class="value">' + htmlSeguro(dados.descricao || 'Sem descrição cadastrada.') + '</span></div>' +
                '<div class="seos-peca-preview-card"><span class="label">Valor unitário</span><span class="value">' + moeda(dados.valor_unitario) + '</span></div>' +
                '<div class="seos-peca-preview-card"><span class="label">Preço de varejo</span><span class="value">' + moeda(dados.preco_varejo) + '</span></div>' +
                '<div class="seos-peca-preview-card"><span class="label">Estoque</span><span class="value">' + htmlSeguro(dados.estoque) + ' un. | mínimo: ' + htmlSeguro(dados.estoque_minimo) + '</span></div>' +
            '</div>';
    }

    function adicionarAtualNaLista() {
        const select = selectPeca();
        const qtd = inputQtd();
        const obs = inputObs();
        const status = statusLista();

        if (!select || !qtd) return false;

        const pecaId = String(select.value || '');
        const quantidade = parseInt(qtd.value || '0', 10);
        const pecas = dadosPecas();
        const dados = pecas[pecaId];

        if (!dados) {
            if (status) status.textContent = 'Selecione uma peça antes de adicionar.';
            return false;
        }

        if (!quantidade || quantidade <= 0) {
            if (status) status.textContent = 'Informe uma quantidade maior que zero.';
            qtd.focus();
            return false;
        }

        const lista = getLista();
        lista.push({
            peca_id: Number(pecaId),
            nome: dados.nome,
            codigo: dados.codigo,
            quantidade: quantidade,
            observacao: obs ? obs.value : '',
            valor_unitario: dados.valor_unitario,
            preco_varejo: dados.preco_varejo,
            estoque: dados.estoque
        });

        setLista(lista);
        limparCamposTemporarios();

        if (status) {
            status.textContent = 'Peça adicionada à lista temporária. Continue adicionando ou clique em Pronto.';
        }

        return true;
    }

    function removerDaLista(indice) {
        const lista = getLista();
        lista.splice(indice, 1);
        setLista(lista);
        const status = statusLista();
        if (status) {
            status.textContent = lista.length ? 'Lista atualizada.' : 'Nenhuma peça adicionada ainda.';
        }
    }

    function renderLista() {
        const container = painelLista();
        const status = statusLista();
        if (!container) return;

        const lista = getLista();

        if (!lista.length) {
            container.innerHTML = '<div class="seos-pecas-temp-empty">A lista temporária está vazia.</div>';
            if (status) status.textContent = 'Nenhuma peça adicionada ainda.';
            return;
        }

        const total = lista.reduce(function (soma, item) {
            const valor = Number(String(item.preco_varejo || item.valor_unitario || '0').replace(',', '.'));
            return soma + (Number.isNaN(valor) ? 0 : valor * Number(item.quantidade || 0));
        }, 0);

        container.innerHTML =
            '<div class="seos-pecas-temp-table-wrap">' +
                '<table class="seos-pecas-temp-table">' +
                    '<thead><tr><th>Peça</th><th>Qtd.</th><th>Observação</th><th>Subtotal</th><th></th></tr></thead>' +
                    '<tbody>' +
                    lista.map(function (item, idx) {
                        const valor = Number(String(item.preco_varejo || item.valor_unitario || '0').replace(',', '.'));
                        const subtotal = Number.isNaN(valor) ? 0 : valor * Number(item.quantidade || 0);
                        return '<tr>' +
                            '<td><strong>' + htmlSeguro(item.nome) + '</strong><br><span>' + htmlSeguro(item.codigo) + '</span></td>' +
                            '<td>' + htmlSeguro(item.quantidade) + ' un.</td>' +
                            '<td>' + htmlSeguro(item.observacao || '—') + '</td>' +
                            '<td>' + moeda(subtotal) + '</td>' +
                            '<td><button type="button" class="seos-peca-remove-temp" data-index="' + idx + '">Remover</button></td>' +
                        '</tr>';
                    }).join('') +
                    '</tbody>' +
                '</table>' +
            '</div>' +
            '<div class="seos-pecas-temp-total">Total estimado: <strong>' + moeda(total) + '</strong></div>';

        if (status) {
            status.textContent = lista.length + ' peça(s) na lista temporária. Clique em Pronto e depois salve a OS.';
        }
    }

    function marcarPronto() {
        const status = statusLista();
        if (selectPeca() && selectPeca().value && inputQtd() && inputQtd().value) {
            adicionarAtualNaLista();
        }
        const lista = getLista();
        if (status) {
            status.textContent = lista.length
                ? 'Lista pronta. Agora clique em Salvar para registrar as peças na OS.'
                : 'Nenhuma peça na lista. Você pode salvar a OS sem peças.';
        }
    }

    function ligarListaTemporaria() {
        const select = selectPeca();
        if (!select || select.dataset.seosListaTempLigada === '1') {
            renderLista();
            return;
        }

        select.dataset.seosListaTempLigada = '1';

        select.addEventListener('change', atualizarPreview);
        select.addEventListener('input', atualizarPreview);

        const btnAdd = campo('#seos-add-peca-temp');
        if (btnAdd && btnAdd.dataset.seosLigado !== '1') {
            btnAdd.dataset.seosLigado = '1';
            btnAdd.addEventListener('click', adicionarAtualNaLista);
        }

        const btnPronto = campo('#seos-pronto-pecas');
        if (btnPronto && btnPronto.dataset.seosLigado !== '1') {
            btnPronto.dataset.seosLigado = '1';
            btnPronto.addEventListener('click', marcarPronto);
        }

        const btnPreview = document.querySelector('.seos-peca-refresh-btn');
        if (btnPreview && btnPreview.dataset.seosLigado !== '1') {
            btnPreview.dataset.seosLigado = '1';
            btnPreview.addEventListener('click', atualizarPreview);
        }

        document.addEventListener('click', function (event) {
            const remover = event.target.closest ? event.target.closest('.seos-peca-remove-temp') : null;
            if (remover) {
                removerDaLista(Number(remover.dataset.index || 0));
            }
        });

        atualizarPreview();
        renderLista();
    }

    document.addEventListener('DOMContentLoaded', ligarListaTemporaria);
    setTimeout(ligarListaTemporaria, 250);
    setTimeout(ligarListaTemporaria, 800);
    setTimeout(ligarListaTemporaria, 1600);

    window.seosAtualizarListaTemporariaPecas = renderLista;
})();


/* --- SEOS 17.1: correção direta do botão Atualizar detalhes da peça --- */
(function () {
    function dinheiro(valor) {
        const numero = Number(String(valor || '0').replace(',', '.'));
        if (Number.isNaN(numero)) return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numero);
    }

    function seguro(valor) {
        return String(valor ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function selectTemp() {
        return (
            document.getElementById('id_movimentacao_peca_temp') ||
            document.querySelector('select[name="movimentacao_peca_temp"]')
        );
    }

    function caixaPreviewTemp() {
        return document.getElementById('seos-peca-preview-temp');
    }

    function lerMapaPecas() {
        const select = selectTemp();
        if (!select) return {};
        try {
            return JSON.parse(select.dataset.pecasJson || '{}');
        } catch (erro) {
            return {};
        }
    }

    function atualizarPreviewTemp() {
        const select = selectTemp();
        const caixa = caixaPreviewTemp();

        if (!select || !caixa) return false;

        const mapa = lerMapaPecas();
        const id = String(select.value || '');
        const dados = mapa[id];

        if (!dados) {
            caixa.innerHTML = '<div class="seos-peca-preview-empty">Selecione uma peça para ver os detalhes.</div>';
            return false;
        }

        caixa.innerHTML =
            '<div class="seos-peca-preview-title">' + seguro(dados.nome) + ' (' + seguro(dados.codigo) + ')</div>' +
            '<div class="seos-peca-preview-grid">' +
                '<div class="seos-peca-preview-card"><span class="label">Descrição</span><span class="value">' + seguro(dados.descricao || 'Sem descrição cadastrada.') + '</span></div>' +
                '<div class="seos-peca-preview-card"><span class="label">Valor unitário</span><span class="value">' + dinheiro(dados.valor_unitario) + '</span></div>' +
                '<div class="seos-peca-preview-card"><span class="label">Preço de varejo</span><span class="value">' + dinheiro(dados.preco_varejo) + '</span></div>' +
                '<div class="seos-peca-preview-card"><span class="label">Estoque</span><span class="value">' + seguro(dados.estoque) + ' un. | mínimo: ' + seguro(dados.estoque_minimo) + '</span></div>' +
            '</div>';

        return true;
    }

    function ligarCorrecaoPreviewTemp() {
        const select = selectTemp();
        if (select && select.dataset.seosPreviewTemp171 !== '1') {
            select.dataset.seosPreviewTemp171 = '1';
            select.addEventListener('change', atualizarPreviewTemp);
            select.addEventListener('input', atualizarPreviewTemp);
        }

        document.querySelectorAll('.seos-peca-refresh-btn').forEach(function (botao) {
            if (botao.dataset.seosPreviewTemp171 === '1') return;
            botao.dataset.seosPreviewTemp171 = '1';

            botao.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation();
                atualizarPreviewTemp();
                return false;
            }, true);
        });
    }

    window.seosAtualizarPreviewPecaTemp = atualizarPreviewTemp;

    document.addEventListener('DOMContentLoaded', ligarCorrecaoPreviewTemp);
    setTimeout(ligarCorrecaoPreviewTemp, 250);
    setTimeout(ligarCorrecaoPreviewTemp, 900);
    setTimeout(ligarCorrecaoPreviewTemp, 1600);
})();


/* --- SEOS 19.3: cadastro rápido de cliente em modal dentro da OS --- */
(function () {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function isOrdemServicoForm() {
        return /\/admin\/ordens\/ordemservico\/(add\/|\d+\/change\/?)/.test(window.location.pathname);
    }

    function normalizarCpf(valor) {
        return (valor || '').replace(/\D/g, '');
    }

    function criarModalClienteRapido() {
        if (document.getElementById('seos-cliente-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'seos-cliente-modal';
        modal.className = 'seos-cliente-modal';
        modal.setAttribute('aria-hidden', 'true');

        modal.innerHTML = `
            <div class="seos-cliente-modal-backdrop" data-seos-close-cliente></div>
            <section class="seos-cliente-modal-card" role="dialog" aria-modal="true" aria-labelledby="seos-cliente-modal-title">
                <button type="button" class="seos-cliente-modal-close" data-seos-close-cliente aria-label="Fechar">×</button>

                <header class="seos-cliente-modal-header">
                    <span class="seos-cliente-modal-icon">👤</span>
                    <div>
                        <h2 id="seos-cliente-modal-title">Novo cliente</h2>
                        <p>Cadastre o cliente sem sair da Ordem de Serviço.</p>
                    </div>
                </header>

                <form id="seos-cliente-modal-form" class="seos-cliente-modal-body">
                    <div class="seos-cliente-modal-error" hidden></div>

                    <label>
                        <span>CPF</span>
                        <input type="text" name="cpf" required autocomplete="off" placeholder="Somente números ou CPF completo">
                    </label>

                    <label>
                        <span>Nome completo</span>
                        <input type="text" name="nome_completo" required autocomplete="off" placeholder="Nome do cliente">
                    </label>

                    <label>
                        <span>Telefone</span>
                        <input type="text" name="telefone" required autocomplete="off" placeholder="Telefone ou WhatsApp">
                    </label>

                    <label>
                        <span>Senha</span>
                        <input type="password" name="password" autocomplete="new-password" placeholder="Opcional">
                        <small>Se ficar em branco, o sistema gera uma senha temporária aleatória.</small>
                    </label>

                    <footer class="seos-cliente-modal-actions">
                        <button type="button" class="seos-cliente-cancel" data-seos-close-cliente>Cancelar</button>
                        <button type="submit" class="seos-cliente-save">Salvar cliente</button>
                    </footer>
                </form>
            </section>
        `;

        document.body.appendChild(modal);
    }

    function abrirModalClienteRapido() {
        criarModalClienteRapido();

        const modal = document.getElementById('seos-cliente-modal');
        const form = document.getElementById('seos-cliente-modal-form');
        const errorBox = modal.querySelector('.seos-cliente-modal-error');

        if (form) form.reset();
        if (errorBox) {
            errorBox.hidden = true;
            errorBox.textContent = '';
        }

        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('seos-modal-open');

        setTimeout(function () {
            const cpf = modal.querySelector('input[name="cpf"]');
            if (cpf) cpf.focus();
        }, 80);
    }

    function fecharModalClienteRapido() {
        const modal = document.getElementById('seos-cliente-modal');
        if (!modal) return;

        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('seos-modal-open');
    }

    function selecionarClienteCriado(dados) {
        const select =
            document.getElementById('id_cliente_usuario') ||
            document.querySelector('select[name="cliente_usuario"]');

        if (!select) return;

        let option = select.querySelector(`option[value="${dados.id}"]`);
        if (!option) {
            option = document.createElement('option');
            option.value = dados.id;
            option.textContent = dados.label;
            select.appendChild(option);
        } else {
            option.textContent = dados.label;
        }

        select.value = String(dados.id);
        select.dispatchEvent(new Event('change', { bubbles: true }));

        if (window.jQuery) {
            window.jQuery(select).trigger('change');
        }

        const nomeExibicao = document.getElementById('id_cliente_nome_exibicao');
        if (nomeExibicao && !nomeExibicao.value) {
            nomeExibicao.value = dados.label || '';
            nomeExibicao.dispatchEvent(new Event('input', { bubbles: true }));
        }

        const numeroSerie = document.getElementById('id_numero_serie');
        if (numeroSerie && dados.numero_serie_cliente) {
            numeroSerie.value = dados.numero_serie_cliente;
            numeroSerie.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    function ligarModalClienteRapido() {
        if (!isOrdemServicoForm()) return;

        criarModalClienteRapido();

        document.addEventListener('click', function (event) {
            const addCliente = event.target.closest('a.add-related, a.related-widget-wrapper-link');
            if (!addCliente) return;

            const href = addCliente.getAttribute('href') || '';
            const isClienteUsuario =
                href.includes('/admin/ordens/usuario/add/') &&
                (
                    href.includes('_popup=1') ||
                    addCliente.id === 'add_id_cliente_usuario' ||
                    addCliente.getAttribute('data-popup') === 'yes'
                );

            if (!isClienteUsuario) return;

            event.preventDefault();
            event.stopPropagation();
            abrirModalClienteRapido();
        }, true);

        document.addEventListener('click', function (event) {
            if (event.target.closest('[data-seos-close-cliente]')) {
                event.preventDefault();
                fecharModalClienteRapido();
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                fecharModalClienteRapido();
            }
        });

        const form = document.getElementById('seos-cliente-modal-form');
        if (!form || form.dataset.seosBound === '1') return;

        form.dataset.seosBound = '1';
        form.addEventListener('submit', async function (event) {
            event.preventDefault();

            const modal = document.getElementById('seos-cliente-modal');
            const errorBox = modal.querySelector('.seos-cliente-modal-error');
            const saveBtn = modal.querySelector('.seos-cliente-save');

            if (errorBox) {
                errorBox.hidden = true;
                errorBox.textContent = '';
            }

            const formData = new FormData(form);
            formData.set('cpf', normalizarCpf(formData.get('cpf')));

            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.textContent = 'Salvando...';
            }

            try {
                const response = await fetch('/admin/ordens/ordemservico/cliente-rapido/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData,
                });

                const data = await response.json();

                if (!response.ok || !data.ok) {
                    throw new Error(data.erro || 'Não foi possível cadastrar o cliente.');
                }

                selecionarClienteCriado(data);
                fecharModalClienteRapido();

                if (data.senha_temporaria) {
                    window.alert(`Cliente cadastrado. Senha temporária: ${data.senha_temporaria}`);
                }
            } catch (error) {
                if (errorBox) {
                    errorBox.hidden = false;
                    errorBox.textContent = error.message || 'Erro ao cadastrar cliente.';
                }
            } finally {
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = 'Salvar cliente';
                }
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', ligarModalClienteRapido);
    } else {
        ligarModalClienteRapido();
    }
})();


/* --- SEOS 19.3: remover ícones relacionados na movimentação de estoque --- */
(function () {
    function limparBotoesRelacionadosMovimentacao() {
        if (!/\/admin\/ordens\/movimentacaoestoque\//.test(window.location.pathname)) return;

        document.querySelectorAll(
            '.related-widget-wrapper-link, ' +
            'a.change-related, a.add-related, a.delete-related, a.view-related, ' +
            '.change-related, .add-related, .delete-related, .view-related'
        ).forEach(function (el) {
            el.remove();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', limparBotoesRelacionadosMovimentacao);
    } else {
        limparBotoesRelacionadosMovimentacao();
    }

    setTimeout(limparBotoesRelacionadosMovimentacao, 250);
    setTimeout(limparBotoesRelacionadosMovimentacao, 900);
})();



/* --- SEOS 20.1: organizar sidebar em Atendimento e Estoque --- */
(function () {
    function textoItemSidebar(elemento) {
        return (elemento.textContent || '')
            .replace(/\s+/g, ' ')
            .trim()
            .toLowerCase();
    }

    function criarCabecalhoSidebar(titulo) {
        const li = document.createElement('li');
        li.className = 'nav-header seos-sidebar-category';
        li.textContent = titulo;
        return li;
    }

    function encaixaEmAtendimento(texto) {
        return (
            texto.includes('dashboard') ||
            texto.includes('painel') ||
            texto.includes('início') ||
            texto.includes('inicio') ||
            texto.includes('ordem') ||
            texto.includes('serviço') ||
            texto.includes('servico') ||
            texto.includes('usuário') ||
            texto.includes('usuario') ||
            texto.includes('cliente') ||
            texto.includes('registro') ||
            texto.includes('auditoria')
        );
    }

    function encaixaEmEstoque(texto) {
        return (
            texto.includes('peça') ||
            texto.includes('peca') ||
            texto.includes('estoque') ||
            texto.includes('movimenta')
        );
    }

    function organizarSidebarCategorias() {
        const nav = document.querySelector('.main-sidebar .nav-sidebar, .sidebar .nav-sidebar, ul.nav-sidebar');
        if (!nav || nav.dataset.seosCategoriasAplicadas === '1') {
            return;
        }

        const itens = Array.from(nav.children).filter((item) => item && item.tagName === 'LI');

        if (!itens.length) {
            return;
        }

        const atendimento = [];
        const estoque = [];
        const outros = [];

        itens.forEach((item) => {
            if (item.classList.contains('seos-sidebar-category')) {
                return;
            }

            // Remove cabeçalhos antigos/genéricos do Jazzmin/Django.
            if (item.classList.contains('nav-header')) {
                return;
            }

            const texto = textoItemSidebar(item);

            if (!texto) {
                outros.push(item);
                return;
            }

            if (encaixaEmEstoque(texto)) {
                estoque.push(item);
                return;
            }

            if (encaixaEmAtendimento(texto)) {
                atendimento.push(item);
                return;
            }

            outros.push(item);
        });

        if (!atendimento.length && !estoque.length) {
            return;
        }

        nav.innerHTML = '';

        if (atendimento.length) {
            nav.appendChild(criarCabecalhoSidebar('ATENDIMENTO'));
            atendimento.forEach((item) => nav.appendChild(item));
        }

        if (estoque.length) {
            nav.appendChild(criarCabecalhoSidebar('ESTOQUE'));
            estoque.forEach((item) => nav.appendChild(item));
        }

        if (outros.length) {
            outros.forEach((item) => nav.appendChild(item));
        }

        nav.dataset.seosCategoriasAplicadas = '1';
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', organizarSidebarCategorias);
    } else {
        organizarSidebarCategorias();
    }

    setTimeout(organizarSidebarCategorias, 250);
    setTimeout(organizarSidebarCategorias, 900);
})();


/* --- SEOS 20.2: correção forte das categorias da sidebar --- */
(function () {
    function normalizarSeosSidebar(texto) {
        return (texto || '')
            .toString()
            .trim()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/\s+/g, ' ');
    }

    function criarCabecalhoSeos(titulo) {
        const li = document.createElement('li');
        li.className = 'nav-header seos-sidebar-category seos-sidebar-category-v20';
        li.textContent = titulo;
        return li;
    }

    function itemTexto(item) {
        return normalizarSeosSidebar(item ? item.textContent : '');
    }

    function ehHeader(item) {
        return item && item.classList && item.classList.contains('nav-header');
    }

    function ehItemAtendimento(texto) {
        return (
            texto.includes('dashboard') ||
            texto.includes('ordens de servico') ||
            texto.includes('ordem de servico') ||
            texto.includes('usuarios') ||
            texto.includes('usuario') ||
            texto.includes('painel do cliente') ||
            texto.includes('auditoria') ||
            texto.includes('registro')
        );
    }

    function ehItemEstoque(texto) {
        return (
            texto.includes('pecas') ||
            texto.includes('peca') ||
            texto.includes('estoque') ||
            texto.includes('entrada e saida') ||
            texto.includes('movimentacao') ||
            texto.includes('movimentacoes')
        );
    }

    function limparCategoriasAntigas(nav) {
        Array.from(nav.children).forEach(function (item) {
            const texto = itemTexto(item);

            if (
                item.classList.contains('seos-sidebar-category') ||
                texto === 'modulos do seos' ||
                texto === 'autenticacao e autorizacao' ||
                texto === 'clientes e equipe' ||
                texto === 'auditoria' ||
                texto === 'permissoes'
            ) {
                item.remove();
            }
        });
    }

    function organizarSidebarSeos20() {
        const nav =
            document.querySelector('.main-sidebar .nav-sidebar') ||
            document.querySelector('.sidebar .nav-sidebar') ||
            document.querySelector('ul.nav-sidebar');

        if (!nav) return;

        limparCategoriasAntigas(nav);

        const itens = Array.from(nav.children).filter(function (item) {
            return item && item.tagName === 'LI' && !ehHeader(item);
        });

        if (!itens.length) return;

        const atendimento = [];
        const estoque = [];
        const outros = [];

        itens.forEach(function (item) {
            const texto = itemTexto(item);

            if (ehItemEstoque(texto)) {
                estoque.push(item);
            } else if (ehItemAtendimento(texto)) {
                atendimento.push(item);
            } else {
                outros.push(item);
            }
        });

        nav.innerHTML = '';

        if (atendimento.length) {
            nav.appendChild(criarCabecalhoSeos('ATENDIMENTO'));
            atendimento.forEach(function (item) {
                nav.appendChild(item);
            });
        }

        if (estoque.length) {
            nav.appendChild(criarCabecalhoSeos('ESTOQUE'));
            estoque.forEach(function (item) {
                nav.appendChild(item);
            });
        }

        outros.forEach(function (item) {
            nav.appendChild(item);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', organizarSidebarSeos20);
    } else {
        organizarSidebarSeos20();
    }

    // Jazzmin às vezes remonta a lateral depois do carregamento inicial.
    [100, 350, 900, 1600, 2500].forEach(function (tempo) {
        setTimeout(organizarSidebarSeos20, tempo);
    });
})();


/* --- SEOS 20.8: total simples das peças da OS, sem mudar fluxo --- */
(function () {
    function moeda(valor) {
        const numero = Number(String(valor || '0').replace(',', '.'));
        if (Number.isNaN(numero)) return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numero);
    }

    function seguro(valor) {
        return String(valor ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function selectPeca() {
        return document.getElementById('id_movimentacao_peca_temp') || document.querySelector('select[name="movimentacao_peca_temp"]');
    }

    function inputQtd() {
        return document.getElementById('id_movimentacao_quantidade_temp') || document.querySelector('input[name="movimentacao_quantidade_temp"]');
    }

    function hiddenJson() {
        return document.getElementById('id_pecas_usadas_json') || document.querySelector('input[name="pecas_usadas_json"]');
    }

    function previewBox() {
        return document.getElementById('seos-peca-preview-temp');
    }

    function statusLista() {
        return document.getElementById('seos-pecas-temp-status');
    }

    function dadosPecas() {
        const select = selectPeca();
        if (!select) return {};
        try {
            return JSON.parse(select.dataset.pecasJson || '{}');
        } catch (erro) {
            return {};
        }
    }

    function listaAtual() {
        const hidden = hiddenJson();
        if (!hidden || !hidden.value) return [];
        try {
            const lista = JSON.parse(hidden.value);
            return Array.isArray(lista) ? lista : [];
        } catch (erro) {
            return [];
        }
    }

    function valorVenda(item) {
        const valor = Number(String(item.preco_varejo || item.valor_unitario || '0').replace(',', '.'));
        return Number.isNaN(valor) ? 0 : valor;
    }

    function atualizarPreviewPeca() {
        const select = selectPeca();
        const qtd = inputQtd();
        const box = previewBox();

        if (!select || !box) return;

        const dados = dadosPecas()[String(select.value || '')];

        if (!dados) {
            box.innerHTML = '<span>Selecione uma peça para calcular o valor.</span>';
            return;
        }

        const quantidade = Math.max(1, Number(qtd && qtd.value ? qtd.value : 1));
        const venda = valorVenda(dados);
        const custo = Number(String(dados.valor_unitario || '0').replace(',', '.')) || 0;
        box.innerHTML =
            '<div class="seos-pecas-os-valores seos-pecas-os-valores-limpo">' +
                '<div><span>Peça trocada</span><strong>' + seguro(dados.nome) + '</strong><small>' + seguro(dados.codigo) + '</small></div>' +
                '<div><span>Quantidade</span><strong>' + seguro(quantidade) + ' un.</strong><small>Estoque: ' + seguro(dados.estoque) + '</small></div>' +
                '<div><span>Preço da peça</span><strong>' + moeda(venda) + '</strong><small>Custo: ' + moeda(custo) + '</small></div>' +
            '</div>';
    }

    function atualizarTotalPecas() {
        const status = statusLista();
        if (!status) return;

        const lista = listaAtual();

        const total = lista.reduce(function (soma, item) {
            return soma + (valorVenda(item) * Number(item.quantidade || 0));
        }, 0);

        status.innerHTML = '<strong>Total das peças adicionadas:</strong> ' + moeda(total) + ' <span>Some com a mão de obra no valor estimado da OS.</span>';
    }

    function ligarMelhoriaPecasOS() {
        const select = selectPeca();
        const qtd = inputQtd();

        if (select && select.dataset.seosValorLigado !== '1') {
            select.dataset.seosValorLigado = '1';
            select.addEventListener('change', function () {
                setTimeout(function () {
                    atualizarPreviewPeca();
                    atualizarTotalPecas();
                }, 60);
            });
        }

        if (qtd && qtd.dataset.seosValorLigado !== '1') {
            qtd.dataset.seosValorLigado = '1';
            qtd.addEventListener('input', atualizarPreviewPeca);
            qtd.addEventListener('change', atualizarPreviewPeca);
        }

        document.addEventListener('click', function (event) {
            if (
                event.target.closest('#seos-add-peca-temp') ||
                event.target.closest('.seos-peca-remove-temp')
            ) {
                setTimeout(function () {
                    atualizarPreviewPeca();
                    atualizarTotalPecas();
                }, 120);
            }
        });

        atualizarPreviewPeca();
        atualizarTotalPecas();
        setTimeout(atualizarTotalPecas, 300);
        setTimeout(atualizarTotalPecas, 900);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', ligarMelhoriaPecasOS);
    } else {
        ligarMelhoriaPecasOS();
    }
})();



/* --- SEOS 20.9: forçar link Reconfigurar senha como botão --- */
(function () {
    function normalizar(texto) {
        return (texto || '')
            .toString()
            .trim()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    }

    function aplicarBotaoSenha() {
        document.querySelectorAll('a').forEach(function (link) {
            const texto = normalizar(link.textContent);
            const href = link.getAttribute('href') || '';

            if (texto.includes('reconfigurar senha') || href.includes('/password/')) {
                link.classList.add('seos-password-reset-button');
                link.textContent = 'Reconfigurar senha';
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', aplicarBotaoSenha);
    } else {
        aplicarBotaoSenha();
    }

    setTimeout(aplicarBotaoSenha, 200);
    setTimeout(aplicarBotaoSenha, 800);
})();



/* --- SEOS 20.10: conferir peças antes de salvar OS --- */
(function () {
    function moeda(valor) {
        const numero = Number(String(valor || '0').replace(',', '.'));
        if (Number.isNaN(numero)) return 'R$ 0,00';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numero);
    }

    function campo(seletor) {
        return document.querySelector(seletor);
    }

    function hiddenJson() {
        return campo('#id_pecas_usadas_json') || campo('input[name="pecas_usadas_json"]');
    }

    function statusLista() {
        return campo('#seos-pecas-temp-status');
    }

    function listaAtual() {
        const hidden = hiddenJson();
        if (!hidden || !hidden.value) return [];

        try {
            const lista = JSON.parse(hidden.value);
            return Array.isArray(lista) ? lista : [];
        } catch (erro) {
            return [];
        }
    }

    function valorVenda(item) {
        const valor = Number(String(item.preco_varejo || item.valor_unitario || '0').replace(',', '.'));
        return Number.isNaN(valor) ? 0 : valor;
    }

    function atualizarStatusConfirmacao(confirmado) {
        const status = statusLista();
        if (!status) return;

        const lista = listaAtual();
        const total = lista.reduce(function (soma, item) {
            return soma + (valorVenda(item) * Number(item.quantidade || 0));
        }, 0);

        if (!lista.length) {
            status.innerHTML = '<strong>Total das peças adicionadas:</strong> ' + moeda(0) + ' <span>Nenhuma peça adicionada à lista.</span>';
            status.classList.remove('is-confirmed');
            return;
        }

        status.innerHTML =
            '<strong>Total das peças adicionadas:</strong> ' + moeda(total) +
            '<span>' + (confirmado ? 'Lista de peças salva. Agora clique em Salvar para gravar na OS.' : 'Salve a lista de peças antes de salvar a OS.') + '</span>';

        status.classList.toggle('is-confirmed', Boolean(confirmado));
    }

    function ligarConfirmacaoPecas() {
        const btn = campo('#seos-confirmar-pecas');

        if (btn && btn.dataset.seosConfirmarLigado !== '1') {
            btn.dataset.seosConfirmarLigado = '1';
            btn.addEventListener('click', function () {
                atualizarStatusConfirmacao(true);
            });
        }

        document.addEventListener('click', function (event) {
            if (
                event.target.closest('#seos-add-peca-temp') ||
                event.target.closest('.seos-peca-remove-temp')
            ) {
                setTimeout(function () {
                    atualizarStatusConfirmacao(false);
                }, 160);
            }
        });

        setTimeout(function () {
            atualizarStatusConfirmacao(false);
        }, 250);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', ligarConfirmacaoPecas);
    } else {
        ligarConfirmacaoPecas();
    }
})();


/* --- SEOS 23.1: tema claro/escuro salvo por usuário no banco, sem troca dinâmica de Bootswatch --- */
(function () {
    const STORAGE_KEY = 'seos_tema';
    const BTN_ID = 'seos-theme-admin-toggle';
    const ITEM_ID = 'seos-theme-admin-item';
    const SAVE_URL = '/salvar-tema/';
    const CURRENT_URL = '/tema-atual/';
    const VALIDOS = new Set(['light', 'dark']);
    const BOOTSWATCH_THEMES = /(cerulean|cosmo|cyborg|darkly|flatly|journal|litera|lumen|lux|materia|minty|morph|pulse|quartz|sandstone|simplex|sketchy|slate|solar|spacelab|superhero|united|vapor|yeti|zephyr)/i;

    function temaValido(valor) {
        return VALIDOS.has(valor) ? valor : null;
    }

    function getCookie(nome) {
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (const cookie of cookies) {
            const item = cookie.trim();
            if (item.startsWith(nome + '=')) {
                return decodeURIComponent(item.slice(nome.length + 1));
            }
        }
        return '';
    }

    function temaLocal() {
        try {
            return temaValido(localStorage.getItem(STORAGE_KEY));
        } catch (erro) {
            return null;
        }
    }

    function trocarBootswatch(tema) {
        // SEOS 23.1:
        // Não trocamos mais o arquivo Bootswatch em tempo real.
        // Essa troca gerava conflito de cascata e fazia botões/letras sumirem.
        // O tema agora é controlado somente por data-seos-theme + custom_admin.css.
        return;
    }

    function atualizarBotao(tema) {
        const botao = document.getElementById(BTN_ID);
        if (!botao) return;

        botao.textContent = tema === 'light' ? '🌙' : '☀️';
        botao.title = tema === 'light' ? 'Alternar para modo escuro' : 'Alternar para modo claro';
        botao.setAttribute('aria-label', botao.title);
        botao.setAttribute('aria-pressed', tema === 'light' ? 'true' : 'false');
    }

    function aplicarTema(tema, salvarLocal) {
        const finalTema = temaValido(tema) || 'dark';
        document.documentElement.setAttribute('data-seos-theme', finalTema);
        if (document.body) {
            document.body.setAttribute('data-seos-theme', finalTema);
            document.body.classList.toggle('seos-theme-light', finalTema === 'light');
            document.body.classList.toggle('seos-theme-dark', finalTema === 'dark');
        }

        trocarBootswatch(finalTema);
        atualizarBotao(finalTema);

        if (salvarLocal !== false) {
            try {
                localStorage.setItem(STORAGE_KEY, finalTema);
            } catch (erro) {}
        }
    }

    function buscarNavbarDireita() {
        const seletores = [
            '.main-header .navbar-nav.ml-auto',
            '.main-header .navbar-nav.ms-auto',
            '.main-header .navbar-nav.navbar-right',
            '.main-header ul.navbar-nav:last-of-type',
            'nav.main-header ul.navbar-nav:last-of-type',
            '.navbar ul.navbar-nav:last-of-type'
        ];

        for (const seletor of seletores) {
            const elemento = document.querySelector(seletor);
            if (elemento) return elemento;
        }

        const navs = Array.from(document.querySelectorAll('.main-header .navbar-nav, nav .navbar-nav, .navbar-nav'));
        return navs.length ? navs[navs.length - 1] : null;
    }

    function buscarItemPerfil(nav) {
        if (!nav) return null;
        const itens = Array.from(nav.children).filter(function (item) {
            return item && item.nodeType === 1 && item.id !== ITEM_ID;
        });

        const comIconeUsuario = itens.find(function (item) {
            return item.querySelector('.fa-user, .far.fa-user, .fas.fa-user, [class*="fa-user"], .user-image, img');
        });

        return comIconeUsuario || itens[itens.length - 1] || null;
    }

    function criarBotao() {
        let item = document.getElementById(ITEM_ID);
        if (!item) {
            item = document.createElement('li');
            item.id = ITEM_ID;
            item.className = 'nav-item seos-theme-admin-item';
        }

        let botao = document.getElementById(BTN_ID);
        if (!botao) {
            botao = document.createElement('button');
            botao.id = BTN_ID;
            botao.type = 'button';
            botao.className = 'seos-theme-admin-toggle';
            botao.setAttribute('data-seos-theme-toggle-admin', '1');
        }

        if (!item.contains(botao)) {
            item.innerHTML = '';
            item.appendChild(botao);
        }

        if (botao.dataset.seosThemeBound !== '1') {
            botao.dataset.seosThemeBound = '1';
            botao.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation();
                const atual = temaValido(document.documentElement.getAttribute('data-seos-theme')) || 'dark';
                const novo = atual === 'light' ? 'dark' : 'light';
                aplicarTema(novo, true);
                salvarTema(novo);
            }, true);
        }

        return item;
    }

    function posicionarBotao() {
        const nav = buscarNavbarDireita();
        const item = criarBotao();

        if (nav) {
            const perfil = buscarItemPerfil(nav);
            if (item.parentNode !== nav) {
                if (perfil) nav.insertBefore(item, perfil);
                else nav.appendChild(item);
            } else if (perfil && item.nextElementSibling !== perfil) {
                nav.insertBefore(item, perfil);
            }
        } else if (document.body && item.parentNode !== document.body) {
            item.style.position = 'fixed';
            item.style.right = '64px';
            item.style.top = '12px';
            item.style.zIndex = '9999';
            document.body.appendChild(item);
        }

        atualizarBotao(temaValido(document.documentElement.getAttribute('data-seos-theme')) || 'dark');
    }

    function salvarTema(tema) {
        const dados = new FormData();
        dados.append('tema', tema);

        fetch(SAVE_URL, {
            method: 'POST',
            body: dados,
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(function () {
            // A troca visual permanece mesmo se a gravação falhar momentaneamente.
        });
    }

    function carregarTemaDoBanco() {
        fetch(CURRENT_URL, {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(function (resposta) {
                if (!resposta.ok) throw new Error('tema não disponível');
                return resposta.json();
            })
            .then(function (dados) {
                const tema = temaValido(dados && dados.tema);
                if (tema) aplicarTema(tema, true);
            })
            .catch(function () {
                aplicarTema(temaLocal() || 'dark', false);
            });
    }

    function iniciar() {
        aplicarTema(temaLocal() || 'dark', false);
        posicionarBotao();
        carregarTemaDoBanco();
    }

    aplicarTema(temaLocal() || 'dark', false);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }

    [100, 300, 700, 1500].forEach(function (tempo) {
        setTimeout(posicionarBotao, tempo);
    });
})();

// SEOS 23.9 - remove visualmente o filtro duplicado de mês da lista de OS.
(function () {
  function hideDuplicateOrderMonthFilter() {
    var selects = document.querySelectorAll('body.model-ordemservico.change-list #changelist-search select[data-name="mes_entrada"]');
    selects.forEach(function (select) {
      var parent = select.closest('.form-group') || select.parentElement;
      if (parent) {
        parent.style.display = 'none';
        parent.style.width = '0';
        parent.style.minWidth = '0';
        parent.style.maxWidth = '0';
        parent.style.margin = '0';
        parent.style.padding = '0';
      }
    });
  }
  document.addEventListener('DOMContentLoaded', hideDuplicateOrderMonthFilter);
  setTimeout(hideDuplicateOrderMonthFilter, 250);
})();
