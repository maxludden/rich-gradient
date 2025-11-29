(function () {
    function showToast(message) {
        var toast = document.createElement('div');
        toast.className = 'rg-toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        // Force reflow to apply transition
        void toast.offsetWidth;
        toast.classList.add('visible');
        setTimeout(function () {
            toast.classList.remove('visible');
            toast.addEventListener('transitionend', function () {
                toast.remove();
            }, { once: true });
        }, 2000);
    }

    function copyText(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }
        // Fallback for older browsers
        return new Promise(function (resolve, reject) {
            try {
                var ta = document.createElement('textarea');
                ta.value = text;
                ta.setAttribute('readonly', '');
                ta.style.position = 'fixed';
                ta.style.top = '-1000px';
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                resolve();
            } catch (err) {
                reject(err);
            }
        });
    }

    function bindCopyLinks() {
        var links = document.querySelectorAll('a.copy-install');
        links.forEach(function (el) {
            el.addEventListener('click', function (ev) {
                ev.preventDefault();
                var text = el.getAttribute('data-copy') || 'uv add rich-gradient';
                copyText(text)
                    .then(function () { showToast('Copied: ' + text); })
                    .catch(function () { showToast('Copy failed'); });
            });
        });
    }

    // Re-bind on page load and after MkDocs Material instant navigation
    document.addEventListener('DOMContentLoaded', bindCopyLinks);
    if (window.document$) {
        window.document$.subscribe(bindCopyLinks);
    }
})();
