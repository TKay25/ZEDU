(function() {
    function ensureModalShell() {
        let modalElement = document.getElementById('appModal');
        if (modalElement) {
            return modalElement;
        }

        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div class="modal fade" id="appModal" tabindex="-1" aria-labelledby="appModalTitle" aria-hidden="true">
                <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="appModalTitle">ZEDU</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="appModalBody">
                            <div class="text-center py-5">
                                <div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(wrapper.firstElementChild);
        return document.getElementById('appModal');
    }

    function isBootstrapAvailable() {
        return window.bootstrap && typeof window.bootstrap.Modal === 'function';
    }

    if (typeof window.loadModalPath !== 'function') {
        window.loadModalPath = async function(path) {
            if (!isBootstrapAvailable()) {
                window.location.href = path;
                return;
            }

            const modalElement = ensureModalShell();
            const modalBody = modalElement.querySelector('#appModalBody');
            const modalTitle = modalElement.querySelector('#appModalTitle');
            const appModal = new bootstrap.Modal(modalElement, {
                backdrop: 'static',
                keyboard: true
            });

            modalTitle.textContent = 'Loading...';
            modalBody.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            appModal.show();

            try {
                const response = await fetch('/api/page-fragment?path=' + encodeURIComponent(path));
                const data = await response.json();
                if (data.success) {
                    modalTitle.textContent = data.title || 'ZEDU';
                    modalBody.innerHTML = data.html || '<p>No content available.</p>';
                    if (typeof window.initAppModal === 'function') {
                        window.initAppModal(path);
                    }
                } else {
                    modalTitle.textContent = 'Error';
                    modalBody.innerHTML = '<div class="alert alert-danger">Unable to load content: ' + (data.message || 'Unknown error') + '</div>';
                }
            } catch (error) {
                console.error('Modal load error:', error);
                modalTitle.textContent = 'Error';
                modalBody.innerHTML = '<div class="alert alert-danger">Error loading content. Please try again.</div>';
            }
        };
    }

    window.navigateToModal = function(path) {
        if (typeof window.loadModalPath === 'function') {
            window.loadModalPath(path);
            return;
        }
        window.location.href = path;
    };
})();
