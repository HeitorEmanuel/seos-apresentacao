(function () {
    function isDashboard() {
        const path = window.location.pathname.replace(/\/+$/, '/');
        return path.endsWith('/admin/');
    }

    function buildUrl(path) {
        return window.location.origin + path;
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (!isDashboard()) return;

        document.body.classList.add('seos-dashboard-page');

        const container =
            document.querySelector('.content-wrapper .content .container-fluid') ||
            document.querySelector('.content .container-fluid') ||
            document.querySelector('.content');

        if (!container || document.querySelector('.seos-dashboard-shell')) return;

        const dashboard = document.createElement('section');
        dashboard.className = 'seos-dashboard-shell';
        dashboard.innerHTML = `
            <div class="seos-dashboard-hero">
                <div>
                    <span class="seos-dashboard-kicker">Painel SEOS</span>
                    <h2>Controle rápido da assistência</h2>
                    <p>Crie ordens, consulte clientes e acompanhe movimentações sem garimpar menu igual quem procura parafuso 1.5 no chão.</p>
                </div>
                <form class="seos-dashboard-search" action="${buildUrl('/admin/ordens/ordemservico/')}" method="get">
                    <label for="seos-dashboard-q">Buscar OS</label>
                    <div>
                        <input id="seos-dashboard-q" type="search" name="q" placeholder="Cliente, equipamento, nº série..." autocomplete="off">
                        <button type="submit">Buscar</button>
                    </div>
                </form>
            </div>

            <div class="seos-dashboard-grid">
                <a class="seos-dashboard-card primary" href="${buildUrl('/admin/ordens/ordemservico/add/')}">
                    <span class="seos-dashboard-icon">＋</span>
                    <strong>Nova Ordem</strong>
                    <small>Cadastrar novo serviço</small>
                </a>
                <a class="seos-dashboard-card" href="${buildUrl('/admin/ordens/ordemservico/')}">
                    <span class="seos-dashboard-icon">🛠️</span>
                    <strong>Ordens</strong>
                    <small>Ver, editar e imprimir</small>
                </a>
                <a class="seos-dashboard-card" href="${buildUrl('/admin/ordens/historicoordemservico/')}">
                    <span class="seos-dashboard-icon">🕘</span>
                    <strong>Histórico</strong>
                    <small>Monitorar movimentações</small>
                </a>
                <a class="seos-dashboard-card" href="${buildUrl('/admin/ordens/usuario/add/')}">
                    <span class="seos-dashboard-icon">👤</span>
                    <strong>Novo Cliente</strong>
                    <small>Cadastrar acesso por CPF</small>
                </a>
            </div>

            <div class="seos-dashboard-tips">
                <button type="button" data-seos-toggle-tips>
                    <span>💡 Fluxo recomendado para apresentação</span>
                    <b>mostrar/ocultar</b>
                </button>
                <ol>
                    <li>Cadastre um cliente.</li>
                    <li>Abra uma nova OS e vincule esse cliente.</li>
                    <li>Preencha equipamento, número de série, status e técnico.</li>
                    <li>Use Ver, Imprimir OS e Etiqueta para demonstrar o fluxo completo.</li>
                </ol>
            </div>
        `;

        container.prepend(dashboard);

        const toggle = dashboard.querySelector('[data-seos-toggle-tips]');
        const tipsList = dashboard.querySelector('.seos-dashboard-tips ol');

        if (toggle && tipsList) {
            toggle.addEventListener('click', function () {
                tipsList.classList.toggle('is-hidden');
            });
        }
    });
})();
