/* SEOS 23.0 - tema claro/escuro central para login e painel do cliente */
(function () {
    const STORAGE_KEY = 'seos_tema';
    const VALIDOS = new Set(['light', 'dark']);

    function valorValido(valor) {
        return VALIDOS.has(valor) ? valor : null;
    }

    function temaInicial() {
        const htmlTema = valorValido(document.documentElement.getAttribute('data-seos-theme'));
        if (htmlTema) return htmlTema;

        try {
            const salvo = valorValido(localStorage.getItem(STORAGE_KEY));
            if (salvo) return salvo;
        } catch (erro) {}

        return 'dark';
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

    function atualizarBotoes(tema) {
        document.querySelectorAll('[data-seos-theme-toggle]').forEach(function (botao) {
            botao.innerHTML = tema === 'light' ? '🌙' : '☀️';
            botao.title = tema === 'light' ? 'Alternar para modo escuro' : 'Alternar para modo claro';
            botao.setAttribute('aria-label', botao.title);
            botao.setAttribute('aria-pressed', tema === 'light' ? 'true' : 'false');
        });
    }

    function aplicarTema(tema, salvarLocal) {
        const finalTema = valorValido(tema) || 'dark';
        document.documentElement.setAttribute('data-seos-theme', finalTema);
        if (document.body) {
            document.body.setAttribute('data-seos-theme', finalTema);
        }

        if (salvarLocal !== false) {
            try {
                localStorage.setItem(STORAGE_KEY, finalTema);
            } catch (erro) {}
        }

        atualizarBotoes(finalTema);
    }

    function salvarNoBanco(tema) {
        const meta = document.querySelector('meta[name="seos-theme-save-url"]');
        const url = meta ? meta.getAttribute('content') : '';
        if (!url) return;

        const dados = new FormData();
        dados.append('tema', tema);

        fetch(url, {
            method: 'POST',
            body: dados,
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(function () {
            // A troca visual não deve quebrar caso a rede falhe.
        });
    }

    function alternarTema(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        const atual = valorValido(document.documentElement.getAttribute('data-seos-theme')) || temaInicial();
        const novo = atual === 'light' ? 'dark' : 'light';
        aplicarTema(novo, true);
        salvarNoBanco(novo);
    }

    function ligar() {
        aplicarTema(temaInicial(), false);

        document.querySelectorAll('[data-seos-theme-toggle]').forEach(function (botao) {
            if (botao.dataset.seosThemeBound === '1') return;
            botao.dataset.seosThemeBound = '1';
            botao.setAttribute('type', 'button');
            botao.addEventListener('click', alternarTema);
        });
    }

    aplicarTema(temaInicial(), false);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', ligar);
    } else {
        ligar();
    }

    window.seosAplicarTema = aplicarTema;
    window.seosAlternarTema = alternarTema;
})();
