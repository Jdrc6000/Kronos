window.KronosCore = (function () {

    let vault = {}, masterPw = '', activeId = null, editingId = null, pwRevealed = false;

    let ui = {};

    function init(bridge) {
        ui = bridge;
        if (ui.masterPwInput) {
            ui.masterPwInput.addEventListener('keydown', e => { if (e.key === 'Enter') unlock(); });
        }
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') closeModal();
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                if (ui.vaultScreen && ui.vaultScreen.style.display !== 'none') {
                    e.preventDefault(); openAddModal();
                }
            }
        });
    }

    async function unlock() {
        const pw = ui.masterPwInput.value.trim();
        if (!pw) return showStatus('Enter your master passphrase.', 'error');
        setUnlockLoading(true);
        showStatus('', 'info');
        try {
            const res = await fetch('/unlock', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: pw }),
            });
            if (res.status === 404) {
                if (pw.length < 8) { showStatus('No vault yet — choose a passphrase of at least 8 characters.', 'error'); return; }
                masterPw = pw; vault = {}; await persist(); enterVault(); return;
            }
            if (res.status === 401) { showStatus('Incorrect passphrase.', 'error'); ui.masterPwInput.focus(); return; }
            if (!res.ok) throw new Error();
            const { vault: data } = await res.json();
            masterPw = pw; vault = data; enterVault();
        } catch { showStatus('Could not reach vault. Is the server running?', 'error'); }
        finally { setUnlockLoading(false); }
    }

    function lock() {
        vault = {}; masterPw = ''; activeId = null;
        if (ui.masterPwInput) ui.masterPwInput.value = '';
        showStatus('', 'info');
        if (ui.lockScreen) ui.lockScreen.style.display = '';
        if (ui.vaultScreen) ui.vaultScreen.style.display = 'none';
    }

    function enterVault() {
        if (ui.lockScreen) ui.lockScreen.style.display = 'none';
        if (ui.vaultScreen) ui.vaultScreen.style.display = 'flex';
        renderList(); showDetail(null);
    }

    async function persist() {
        setSaveState('saving');
        try {
            const res = await fetch('/save', {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: masterPw, vault }),
            });
            if (!res.ok) throw new Error();
            setSaveState('saved');
        } catch { setSaveState('error'); toast('Failed to save vault.'); }
    }

    function setSaveState(state) {
        if (ui.onSaveState) ui.onSaveState(state);
    }

    function renderList() {
        const q = ui.searchInput ? ui.searchInput.value.toLowerCase() : '';
        const ids = Object.keys(vault);
        const filtered = ids.filter(id => {
            const e = vault[id];
            return !q || e.site.toLowerCase().includes(q) || (e.username || '').toLowerCase().includes(q);
        });
        if (ui.onRenderList) ui.onRenderList(filtered, vault, activeId);
        if (ui.entryCountEl) ui.entryCountEl.textContent = ids.length;
    }

    function showDetail(id) {
        activeId = id; pwRevealed = false;
        if (ui.onShowDetail) ui.onShowDetail(id, vault[id] || null);
    }

    function toggleReveal() {
        if (!activeId) return;
        pwRevealed = !pwRevealed;
        if (ui.onToggleReveal) ui.onToggleReveal(pwRevealed, vault[activeId].password);
    }

    function copyPassword() {
        if (!activeId) return;
        navigator.clipboard.writeText(vault[activeId].password).then(() => toast('Password copied'));
    }

    function copyField(text) {
        navigator.clipboard.writeText(text).then(() => toast('Copied'));
    }

    function openAddModal() {
        editingId = null;
        if (ui.onOpenModal) ui.onOpenModal(null);
    }

    function openEditModal() {
        if (!activeId || !vault[activeId]) return;
        editingId = activeId;
        if (ui.onOpenModal) ui.onOpenModal(vault[activeId]);
    }

    function closeModal() {
        if (ui.onCloseModal) ui.onCloseModal();
    }

    async function saveEntry(fields) {
        const { site, url, username, password, notes } = fields;
        if (!site) { toast('Site name is required.'); return false; }
        if (!password) { toast('Password is required.'); return false; }
        const id = editingId || crypto.randomUUID();
        vault[id] = { site, url: url || '', username: username || '', password, notes: notes || '' };
        closeModal(); renderList(); showDetail(id); await persist();
        return true;
    }

    async function deleteEntry(id) {
        if (!confirm(`Delete "${vault[id]?.site}"? This cannot be undone.`)) return;
        delete vault[id]; if (activeId === id) showDetail(null);
        renderList(); await persist();
    }

    function generatePassword() {
        const chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$%^&*-_+=';
        const arr = new Uint8Array(20); crypto.getRandomValues(arr);
        return Array.from(arr, b => chars[b % chars.length]).join('');
    }

    function strengthScore(pw) {
        if (!pw) return { pct: 0, label: '', color: '' };
        let s = 0;
        if (pw.length >= 8) s++; if (pw.length >= 12) s++; if (pw.length >= 16) s++;
        if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
        if (/[0-9]/.test(pw)) s++;
        if (/[^A-Za-z0-9]/.test(pw)) s++;
        const idx = Math.min(4, Math.floor(s / 1.5));
        const colors = ['#c0392b', '#e67e22', '#c9a420', '#27ae60', '#27ae60'];
        const labels = ['Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'];
        return { pct: Math.min(100, Math.round(s / 6 * 100)), label: labels[idx], color: colors[idx] };
    }

    function showStatus(msg, type) {
        if (ui.onStatus) ui.onStatus(msg, type);
    }

    function setUnlockLoading(loading) {
        if (ui.onUnlockLoading) ui.onUnlockLoading(loading);
    }

    function toast(msg) {
        if (ui.onToast) ui.onToast(msg);
    }

    function esc(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function togglePwVisibility(inputId) {
        const el = document.getElementById(inputId);
        if (el) el.type = el.type === 'password' ? 'text' : 'password';
    }

    return {
        init, unlock, lock, enterVault,
        renderList, showDetail, toggleReveal, copyPassword, copyField,
        openAddModal, openEditModal, closeModal, saveEntry, deleteEntry,
        generatePassword, strengthScore, esc, togglePwVisibility,
        getActiveId: () => activeId,
        getVault: () => vault,
    };
})();