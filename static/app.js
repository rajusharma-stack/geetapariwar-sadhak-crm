(function() {
    'use strict';

    let selectedSadhakId = null;
    let zoomLinkCache = {};
    let editingId = null;

    // ── DOM refs ─────────────────────────────────────────────────

    const $ = id => document.getElementById(id);
    const nameInput = $('name');
    const phoneInput = $('phone');
    const emailInput = $('email');
    const prnInput = $('prn');
    const groupSelect = $('groupSelect');
    const countrySelect = $('countryCodeSelect');
    const editingIdInput = $('editingId');
    const saveBtn = $('saveBtn');
    const clearBtn = $('clearBtn');
    const formStatus = $('formStatus');
    const sadhakForm = $('sadhakForm');
    const searchInput = $('searchInput');
    const filterGroup = $('filterGroup');
    const clearFilterBtn = $('clearFilterBtn');
    const sadhakTbody = $('sadhakTableBody');
    const totalLabel = $('totalLabel');
    const editBtn = $('editBtn');
    const deleteBtn = $('deleteBtn');
    const whatsappBtn = $('whatsappBtn');
    const historyBtn = $('historyBtn');
    const refreshBtn = $('refreshBtn');
    const bcDisplay = $('bcDisplay');
    const gcDisplay = $('gcDisplay');
    const ctDisplay = $('ctDisplay');
    const taDisplay = $('taDisplay');
    const zoomLinkRow = $('zoomLinkRow');
    const zoomLink = $('zoomLink');
    const levelDisplay = $('levelDisplay');
    const batchDisplay = $('batchDisplay');

    // Group modal
    const groupModal = $('groupModal');
    const groupModalClose = $('groupModalClose');
    const manageGroupsBtn = $('manageGroupsBtn');
    const groupTbody = $('groupTableBody');
    const addGroupBtn = $('addGroupBtn');
    const editGroupBtn = $('editGroupBtn');
    const deleteGroupBtn = $('deleteGroupBtn');
    const openGroupZoomBtn = $('openGroupZoomBtn');

    // Group edit modal
    const groupEditModal = $('groupEditModal');
    const groupEditModalClose = $('groupEditModalClose');
    const groupEditTitle = $('groupEditTitle');
    const groupEditId = $('groupEditId');
    const groupName = $('groupName');
    const groupBc = $('groupBc');
    const groupGc = $('groupGc');
    const groupCt = $('groupCt');
    const groupTa = $('groupTa');
    const groupTiming = $('groupTiming');
    const groupZoom = $('groupZoom');
    const groupLevel = $('groupLevel');
    const groupBatch = $('groupBatch');
    const groupForm = $('groupForm');

    // History modal
    const historyModal = $('historyModal');
    const historyModalClose = $('historyModalClose');
    const historyModalTitle = $('historyModalTitle');
    const historyTbody = $('historyTableBody');

    // ── Debounce helper ──────────────────────────────────────────

    function debounce(fn, ms) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), ms);
        };
    }

    // ── Toast / Alert ────────────────────────────────────────────

    function showError(msg) {
        formStatus.textContent = 'Error: ' + msg;
        formStatus.style.color = 'var(--danger)';
    }

    function showSuccess(msg) {
        formStatus.textContent = msg;
        formStatus.style.color = 'var(--success)';
    }

    function showStatus(msg) {
        formStatus.textContent = msg;
        formStatus.style.color = 'var(--text-muted)';
    }

    function alertError(msg) {
        alert(msg);
    }

    function confirmAction(msg) {
        return confirm(msg);
    }

    // ── Sadhak API calls ─────────────────────────────────────────

    async function loadSadhaks() {
        const search = searchInput.value.trim();
        const groupId = filterGroup.value;
        const params = new URLSearchParams();
        if (search) params.set('search', search);
        if (groupId) params.set('group_id', groupId);
        try {
            const res = await fetch('/api/sadhaks?' + params.toString());
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.error || 'Failed to load sadhaks (status ' + res.status + ')');
            }
            const data = await res.json();
            sadhakTbody.innerHTML = '';
            data.records.forEach(r => {
                const tr = document.createElement('tr');
                tr.dataset.id = r.id;
                tr.innerHTML = `
                    <td>${esc(r.name)}</td>
                    <td>${esc(r.phone)}</td>
                    <td>${esc(r.email)}</td>
                    <td>${esc(r.prn)}</td>
                    <td>${esc(r.group_name)}</td>
                    <td>${esc(r.level)}</td>
                    <td>${esc(r.batch)}</td>
                    <td>${esc(r.bc_name)}</td>
                    <td>${esc(r.gc_name)}</td>
                    <td>${esc(r.ct_name)}</td>
                    <td>${esc(r.ta_name)}</td>
                    <td>${esc(r.created_at)}</td>
                    <td>${esc(r.updated_at)}</td>
                    <td>${esc(r.created_by_name)}</td>
                    <td>${esc(r.updated_by_name)}</td>
                `;
                tr.addEventListener('click', () => selectRow(tr));
                tr.addEventListener('dblclick', () => loadSadhakForEdit(r.id));
                sadhakTbody.appendChild(tr);
            });
            const showing = data.showing;
            const total = data.total;
            totalLabel.textContent = search || groupId ? `(${showing} of ${total})` : `(${total})`;
        } catch (err) {
            console.error(err);
            sadhakTbody.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--danger);padding:40px">Error loading data: ' + esc(err.message) + '</td></tr>';
        }
    }

    function selectRow(tr) {
        sadhakTbody.querySelectorAll('tr.selected').forEach(r => r.classList.remove('selected'));
        tr.classList.add('selected');
        selectedSadhakId = parseInt(tr.dataset.id);
    }

    function esc(s) {
        if (!s) return '—';
        const div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    // ── Edit sadhak ──────────────────────────────────────────────

    async function loadSadhakForEdit(id) {
        try {
            const res = await fetch('/api/sadhak/' + id);
            if (!res.ok) return;
            const data = await res.json();
            editingId = data.id;
            editingIdInput.value = data.id;
            nameInput.value = data.name || '';

            let displayPhone = data.phone || '';
            let matchedCode = '+977';
            const codes = document.querySelectorAll('#countryCodeSelect option');
            for (const opt of codes) {
                if (displayPhone.startsWith(opt.value)) {
                    displayPhone = displayPhone.slice(opt.value.length);
                    matchedCode = opt.value;
                    break;
                }
            }
            countrySelect.value = matchedCode;
            phoneInput.value = displayPhone;
            emailInput.value = data.email || '';
            prnInput.value = data.prn || '';

            if (data.group_id) {
                groupSelect.value = data.group_id;
                groupSelect.dispatchEvent(new Event('change'));
            } else {
                groupSelect.value = '';
                groupSelect.dispatchEvent(new Event('change'));
            }

            saveBtn.textContent = 'Update Sadhak';
            showStatus('Editing…');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (err) {
            console.error(err);
        }
    }

    // ── Group selection display ──────────────────────────────────

    groupSelect.addEventListener('change', async function() {
        const gid = this.value;
        if (!gid) {
            bcDisplay.textContent = '—';
            gcDisplay.textContent = '—';
            ctDisplay.textContent = '—';
            taDisplay.textContent = '—';
            zoomLinkRow.style.display = 'none';
            levelDisplay.style.display = 'none';
            batchDisplay.style.display = 'none';
            return;
        }
        const opt = this.options[this.selectedIndex];
        const level = opt && opt.dataset.level ? opt.dataset.level : '';
        const batch = opt && opt.dataset.batch ? opt.dataset.batch : '';
        levelDisplay.textContent = level ? '[' + level + ']' : '';
        levelDisplay.style.display = level ? 'inline' : 'none';
        batchDisplay.textContent = batch ? '[' + batch + ']' : '';
        batchDisplay.style.display = batch ? 'inline' : 'none';
        try {
            const res = await fetch('/api/group/' + gid);
            if (!res.ok) return;
            const data = await res.json();
            bcDisplay.textContent = data.bc_name || '—';
            gcDisplay.textContent = data.gc_name || '—';
            ctDisplay.textContent = data.ct_name || '—';
            taDisplay.textContent = data.ta_name || '—';
            if (data.zoom_link) {
                zoomLink.href = data.zoom_link;
                zoomLinkRow.style.display = 'block';
            } else {
                zoomLinkRow.style.display = 'none';
            }
        } catch (err) {
            console.error(err);
        }
    });

    // ── Client-side LearnGeeta search (browser bypasses PythonAnywhere's outbound block) ──

    function parsePrnTable(html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const rows = doc.querySelectorAll('.table-striped tbody tr');
        const results = [];
        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');
            if (cells.length >= 3) {
                results.push({
                    prn: cells[1].textContent.trim(),
                    name: cells[2].textContent.trim(),
                });
            }
        });
        return results;
    }

    async function searchRemotePrn(phone) {
        const formData = new URLSearchParams();
        formData.append('email', phone);
        formData.append('mobile', phone);
        formData.append('phone', phone);
        formData.append('Submit', 'Search');

        const targetUrl = 'https://online.learngeeta.com/participant/searchparticipant.php';

        // Try direct fetch first (in case LearnGeeta allows CORS)
        try {
            const res = await fetch(targetUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });
            if (res.ok) {
                const results = parsePrnTable(await res.text());
                if (results.length > 0) return results;
            }
        } catch (_) { /* CORS blocked */ }

        // Fallback: CORS proxies
        const proxies = [
            'https://corsproxy.io/?url=',
            'https://api.allorigins.win/raw?url=',
        ];
        for (const proxy of proxies) {
            try {
                const res = await fetch(proxy + encodeURIComponent(targetUrl), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData,
                });
                if (!res.ok) {
                    console.warn('searchRemotePrn proxy', proxy, 'returned', res.status);
                    continue;
                }
                const text = await res.text();
                console.log('searchRemotePrn proxy', proxy, 'response length:', text.length);
                const results = parsePrnTable(text);
                if (results.length > 0) return results;
            } catch (err) {
                console.warn('searchRemotePrn proxy error:', proxy, err);
                continue;
            }
        }
        return [];
    }

    // ── PRN auto-lookup ──────────────────────────────────────────

    // Known country code digit prefixes (without +) sorted longest first
    const COUNTRY_CODE_DIGITS = [
        '1684','1264','1268','1242','1246','1284','1345','1441','1473',
        '1664','1670','1671','1721','1758','1767','1784','1809','1868',
        '1869','1876','1939','1264','1268','1242','1246','1284','1345',
        '1441','1473','1664','1670','1671','1721','1758','1767','1784',
        '1809','1868','1869','1876','1939','93','355','213','376','244',
        '54','374','297','61','43','994','973','880','375','32','501',
        '229','975','591','387','267','55','673','359','226','257','855',
        '237','1','238','236','235','56','86','57','269','682','506',
        '225','385','53','357','420','243','45','253','670','593','20',
        '503','240','291','372','251','500','298','679','358','33','594',
        '689','241','220','995','49','233','350','30','590','502','224',
        '245','592','509','504','852','36','354','91','62','98','964',
        '353','972','39','81','962','7','254','686','383','965','996',
        '856','371','961','266','231','218','423','370','352','853','261',
        '265','60','960','223','356','692','222','230','262','52','691',
        '373','377','976','382','212','258','95','264','674','977','31',
        '599','687','64','505','227','234','683','672','389','47','968',
        '92','680','970','507','675','595','51','63','48','351','974',
        '242','40','250','290','685','378','239','966','221','381','248',
        '232','65','421','386','677','252','27','82','211','34','94',
        '249','597','268','46','41','963','886','992','255','66','228',
        '690','676','216','90','993','688','256','380','971','44','598',
        '998','678','379','58','84','681','967','260','263'
    ];

    function stripCountryCode(phone) {
        // Only strip a country code when the number begins with an explicit
        // international prefix (+ or 00) or with the selected country code itself.
        if (phone.startsWith('+') || phone.startsWith('00')) {
            let normalized = phone.startsWith('00') ? phone.slice(2) : phone.slice(1);
            const selectedCc = countrySelect.value.replace(/\D/g, '');
            if (selectedCc && normalized.startsWith(selectedCc) && normalized.length > selectedCc.length) {
                return normalized.slice(selectedCc.length);
            }
            for (const cc of COUNTRY_CODE_DIGITS) {
                if (normalized.startsWith(cc) && normalized.length > cc.length) {
                    return normalized.slice(cc.length);
                }
            }
            return normalized;
        }

        const selectedCc = countrySelect.value.replace(/\D/g, '');
        if (selectedCc && phone.startsWith(selectedCc) && phone.length > selectedCc.length) {
            return phone.slice(selectedCc.length);
        }
        return phone;
    }

    let prnTimer;
    phoneInput.addEventListener('input', function() {
        clearTimeout(prnTimer);
        let phone = this.value.trim();
        // Strip any country code prefix the user may have typed
        phone = stripCountryCode(phone);
        if (phone.length < 7 || !/^\d+$/.test(phone)) {
            prnInput.value = '';
            showStatus('Ready');
            return;
        }
        showStatus('Searching PRN…');
        prnTimer = setTimeout(async () => {
            try {
                const res = await fetch('/api/prn/' + encodeURIComponent(phone));
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    console.error('PRN lookup error:', res.status, errData);
                    prnInput.value = '';
                    showStatus('PRN lookup failed (server error)');
                    return;
                }
                const localData = await res.json();
                if (localData && localData.length > 0) {
                    prnInput.value = localData[0].prn;
                    if (!nameInput.value.trim()) {
                        nameInput.value = localData[0].name;
                    }
                    const extra = localData.length > 1 ? ` (${localData.length} matches, showing first)` : '';
                    showStatus('Found: ' + localData[0].name + extra);
                    return;
                }
                // No local result — try remote search from browser
                showStatus('Searching LearnGeeta…');
                const remoteData = await searchRemotePrn(phone);
                if (remoteData && remoteData.length > 0) {
                    prnInput.value = remoteData[0].prn;
                    if (!nameInput.value.trim()) {
                        nameInput.value = remoteData[0].name;
                    }
                    showStatus('Found via LearnGeeta: ' + remoteData[0].name);
                } else {
                    prnInput.value = '';
                    showStatus('No PRN found');
                }
            } catch (err) {
                console.error('PRN lookup network error:', err);
                showStatus('PRN lookup failed');
            }
        }, 600);
    });

    // ── Email → PRN auto-lookup ──────────────────────────────────

    let emailTimer;
    emailInput.addEventListener('input', function() {
        clearTimeout(emailTimer);
        const email = this.value.trim();
        if (email.length < 5 || !email.includes('@')) {
            return;
        }
        emailTimer = setTimeout(async () => {
            try {
                const res = await fetch('/api/prn/' + encodeURIComponent(email));
                if (!res.ok) {
                    console.error('Email PRN lookup error:', res.status);
                    return;
                }
                const localData = await res.json();
                if (localData && localData.length > 0) {
                    prnInput.value = localData[0].prn;
                    if (!nameInput.value.trim()) {
                        nameInput.value = localData[0].name;
                    }
                    const extra = localData.length > 1 ? ` (${localData.length} matches, showing first)` : '';
                    showStatus('Found via email: ' + localData[0].name + extra);
                    return;
                }
                // No local result — try remote from browser
                const remoteData = await searchRemotePrn(email);
                if (remoteData && remoteData.length > 0) {
                    prnInput.value = remoteData[0].prn;
                    if (!nameInput.value.trim()) {
                        nameInput.value = remoteData[0].name;
                    }
                    showStatus('Found via LearnGeeta: ' + remoteData[0].name);
                }
            } catch (err) {
                console.error('Email PRN lookup error:', err);
            }
        }, 800);
    });

    // ── PRN → Name auto-lookup (local DB) ────────────────────────

    let prnNameTimer;
    prnInput.addEventListener('input', function() {
        clearTimeout(prnNameTimer);
        const prn = this.value.trim();
        if (prn.length < 2) {
            return;
        }
        prnNameTimer = setTimeout(async () => {
            try {
                const res = await fetch('/api/prn-by-prn/' + encodeURIComponent(prn));
                if (!res.ok) {
                    console.error('PRN-by-PRN lookup error:', res.status);
                    return;
                }
                const data = await res.json();
                if (data && data.length > 0 && !nameInput.value.trim()) {
                    nameInput.value = data[0].name;
                    showStatus('Found: ' + data[0].name);
                }
            } catch (err) {
                console.error('PRN-by-PRN lookup error:', err);
            }
        }, 600);
    });

    // ── Save / Update sadhak ─────────────────────────────────────

    sadhakForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const name = nameInput.value.trim();
        const phone = phoneInput.value.trim();
        const email = emailInput.value.trim();
        const prn = prnInput.value.trim();
        const groupId = groupSelect.value || null;

        if (!name || !phone) {
            showError('Name and Mobile Number are required.');
            return;
        }

        const payload = {
            name,
            phone,
            email,
            prn,
            group_id: groupId,
            country_code: countrySelect.value,
            editing_id: editingId,
        };

        try {
            const res = await fetch('/api/sadhak', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (!res.ok) {
                showError(data.error);
                return;
            }
            showSuccess(data.message);
            clearForm();
            await loadSadhaks();
        } catch (err) {
            showError('Failed to save.');
        }
    });

    function clearForm() {
        editingId = null;
        editingIdInput.value = '';
        nameInput.value = '';
        countrySelect.value = '+977';
        phoneInput.value = '';
        emailInput.value = '';
        prnInput.value = '';
        groupSelect.value = '';
        bcDisplay.textContent = '—';
        gcDisplay.textContent = '—';
        ctDisplay.textContent = '—';
        taDisplay.textContent = '—';
        zoomLinkRow.style.display = 'none';
        levelDisplay.style.display = 'none';
        batchDisplay.style.display = 'none';
        saveBtn.textContent = 'Save Sadhak';
        showStatus('Ready');
        nameInput.focus();
    }

    clearBtn.addEventListener('click', clearForm);

    // ── CRUD buttons ─────────────────────────────────────────────

    editBtn.addEventListener('click', () => {
        if (!selectedSadhakId) { alertError('Please select a record first.'); return; }
        loadSadhakForEdit(selectedSadhakId);
    });

    deleteBtn.addEventListener('click', async () => {
        if (!selectedSadhakId) { alertError('Please select a record first.'); return; }
        const ok = confirmAction('Delete this sadhak record?');
        if (!ok) return;
        try {
            const res = await fetch('/api/sadhak/' + selectedSadhakId, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) { alertError(data.error); return; }
            selectedSadhakId = null;
            await loadSadhaks();
        } catch (err) {
            alertError('Failed to delete.');
        }
    });

    whatsappBtn.addEventListener('click', () => {
        if (!selectedSadhakId) { alertError('Please select a record first.'); return; }
        const tr = sadhakTbody.querySelector('tr.selected');
        if (!tr) return;
        const cells = tr.querySelectorAll('td');
        const phone = cells[1].textContent;
        if (!phone || phone === '—') { alertError('No phone number.'); return; }
        const clean = phone.replace(/\D/g, '');
        if (!clean) { alertError('Invalid phone.'); return; }
        window.open('https://wa.me/' + clean, '_blank');
    });

    refreshBtn.addEventListener('click', loadSadhaks);

    // ── History ──────────────────────────────────────────────────

    historyBtn.addEventListener('click', async () => {
        if (!selectedSadhakId) { alertError('Please select a record first.'); return; }
        const tr = sadhakTbody.querySelector('tr.selected');
        const name = tr ? tr.querySelectorAll('td')[0].textContent : '';
        historyModalTitle.textContent = 'History – ' + name;
        try {
            const res = await fetch('/api/sadhak/' + selectedSadhakId + '/history');
            const data = await res.json();
            historyTbody.innerHTML = '';
            if (data.length === 0) {
                alertError('No history yet.');
                return;
            }
            data.forEach((r, i) => {
                const tr2 = document.createElement('tr');
                tr2.innerHTML = `
                    <td>${i + 1}</td>
                    <td>${esc(r.group_name)}</td>
                    <td>${esc(r.level)}</td>
                    <td>${esc(r.batch)}</td>
                    <td>${esc(r.bc_name)}</td>
                    <td>${esc(r.gc_name)}</td>
                    <td>${esc(r.ct_name)}</td>
                    <td>${esc(r.ta_name)}</td>
                    <td>${esc(r.changed_by)}</td>
                    <td>${esc(r.changed_at)}</td>
                `;
                historyTbody.appendChild(tr2);
            });
            historyModal.classList.add('active');
        } catch (err) {
            alertError('Failed to load history.');
        }
    });

    historyModalClose.addEventListener('click', () => {
        historyModal.classList.remove('active');
    });

    // ── Filters ──────────────────────────────────────────────────

    searchInput.addEventListener('input', debounce(loadSadhaks, 300));
    filterGroup.addEventListener('change', loadSadhaks);

    clearFilterBtn.addEventListener('click', () => {
        searchInput.value = '';
        filterGroup.value = '';
        loadSadhaks();
    });

    // ── Group Management ─────────────────────────────────────────

    manageGroupsBtn.addEventListener('click', () => {
        loadGroups();
        groupModal.classList.add('active');
    });

    groupModalClose.addEventListener('click', () => {
        groupModal.classList.remove('active');
    });

    function closeGroupModal() {
        groupModal.classList.remove('active');
    }

    async function loadGroups() {
        try {
            const res = await fetch('/api/groups');
            const data = await res.json();
            groupTbody.innerHTML = '';
            data.forEach(g => {
                const tr = document.createElement('tr');
                tr.dataset.id = g.id;
                tr.innerHTML = `
                    <td>${esc(g.name)}</td>
                    <td>${esc(g.level)}</td>
                    <td>${esc(g.batch)}</td>
                    <td>${esc(g.timing)}</td>
                    <td>${esc(g.bc_name)}</td>
                    <td>${esc(g.gc_name)}</td>
                    <td>${esc(g.ct_name)}</td>
                    <td>${esc(g.ta_name)}</td>
                    <td>${esc(g.zoom_link)}</td>
                `;
                tr.addEventListener('click', () => {
                    groupTbody.querySelectorAll('tr.selected').forEach(r => r.classList.remove('selected'));
                    tr.classList.add('selected');
                });
                groupTbody.appendChild(tr);
            });
        } catch (err) {
            console.error(err);
        }
    }

    function getSelectedGroup() {
        const sel = groupTbody.querySelector('tr.selected');
        if (!sel) { alertError('Select a group first.'); return null; }
        return parseInt(sel.dataset.id);
    }

    addGroupBtn.addEventListener('click', () => {
        groupEditTitle.textContent = 'New Group';
        groupEditId.value = '';
        groupName.value = '';
        groupLevel.value = 'Level 1';
        groupBatch.value = 'Regular';
        groupBc.value = '';
        groupGc.value = '';
        groupCt.value = '';
        groupTa.value = '';
        groupTiming.value = '';
        groupZoom.value = '';
        groupEditModal.classList.add('active');
    });

    editGroupBtn.addEventListener('click', async () => {
        const gid = getSelectedGroup();
        if (!gid) return;
        try {
            const res = await fetch('/api/group/' + gid);
            const data = await res.json();
            if (!res.ok) { alertError(data.error); return; }
            groupEditTitle.textContent = 'Edit Group';
            groupEditId.value = data.id;
            groupName.value = data.name || '';
            groupLevel.value = data.level || 'Level 1';
            groupBatch.value = data.batch || 'Regular';
            groupBc.value = data.bc_name || '';
            groupGc.value = data.gc_name || '';
            groupCt.value = data.ct_name || '';
            groupTa.value = data.ta_name || '';
            groupTiming.value = data.timing || '';
            groupZoom.value = data.zoom_link || '';
            groupEditModal.classList.add('active');
        } catch (err) {
            alertError('Failed to load group.');
        }
    });

    deleteGroupBtn.addEventListener('click', async () => {
        const gid = getSelectedGroup();
        if (!gid) return;
        const ok = confirmAction('Delete this group?');
        if (!ok) return;
        try {
            const res = await fetch('/api/group/' + gid, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) { alertError(data.error); return; }
            await loadGroups();
            await reloadGroupDropdowns();
            await loadSadhaks();
        } catch (err) {
            alertError('Failed to delete.');
        }
    });

    openGroupZoomBtn.addEventListener('click', () => {
        const sel = groupTbody.querySelector('tr.selected');
        if (!sel) { alertError('Select a group first.'); return; }
        const cells = sel.querySelectorAll('td');
        const link = cells[8].textContent;
        if (!link || link === '—' || link === '') {
            alertError('No Zoom link set for this group.');
            return;
        }
        window.open(link, '_blank');
    });

    groupEditModalClose.addEventListener('click', () => {
        groupEditModal.classList.remove('active');
    });

    groupForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            id: groupEditId.value ? parseInt(groupEditId.value) : null,
            name: groupName.value.trim(),
            level: groupLevel.value,
            batch: groupBatch.value,
            bc_name: groupBc.value.trim(),
            gc_name: groupGc.value.trim(),
            ct_name: groupCt.value.trim(),
            ta_name: groupTa.value.trim(),
            timing: groupTiming.value.trim(),
            zoom_link: groupZoom.value.trim(),
        };
        if (!payload.name) { alertError('Group name is required.'); return; }
        try {
            const res = await fetch('/api/group', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (!res.ok) { alertError(data.error); return; }
            groupEditModal.classList.remove('active');
            await loadGroups();
            await reloadGroupDropdowns();
            await loadSadhaks();
        } catch (err) {
            alertError('Failed to save group.');
        }
    });

    async function reloadGroupDropdowns() {
        try {
            const res = await fetch('/api/groups');
            const data = await res.json();
            [groupSelect, filterGroup].forEach(sel => {
                const current = sel.value;
                sel.innerHTML = '<option value="">-- Select --</option>';
                if (sel.id === 'filterGroup') {
                    sel.innerHTML = '<option value="">All Groups</option>';
                }
                data.forEach(g => {
                    const opt = document.createElement('option');
                    opt.value = g.id;
                    opt.textContent = g.name;
                    opt.dataset.level = g.level || 'Level 1';
                    opt.dataset.batch = g.batch || 'Regular';
                    sel.appendChild(opt);
                });
                if (current) sel.value = current;
            });
        } catch (err) {
            console.error(err);
        }
    }

    // ── Close modals on overlay click ────────────────────────────

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });

    // ── Init ─────────────────────────────────────────────────────

    loadSadhaks();
})();
