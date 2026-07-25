document.addEventListener('DOMContentLoaded', function() {
    var runBtn = document.getElementById('runPipelineBtn');
    var btnText = runBtn.querySelector('.btn-text');
    var btnSpinner = document.getElementById('btnSpinner');
    var resultsSection = document.getElementById('resultsSection');
    
    // Tab Switching Logic
    var tabBtns = document.querySelectorAll('.tab-btn');
    var tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            tabBtns.forEach(function(b) { b.classList.remove('active'); });
            tabPanes.forEach(function(p) { p.classList.remove('active'); });
            btn.classList.add('active');
            document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
        });
    });

    // Auto-load cached results on page load
    loadCachedResults();
    
    function loadCachedResults() {
        return fetch('/api/results')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data && !data.error) {
                    renderResultsFromAPI(data);
                    resultsSection.classList.remove('hidden');
                    for (var i = 1; i <= 4; i++) {
                        updateStage(i, 'complete', 'Complete');
                    }
                    btnText.textContent = 'Re-run Pipeline';
                    return true;
                }
                return false;
            })
            .catch(function(e) {
                console.log('No cached results:', e);
                return false;
            });
    }

    runBtn.addEventListener('click', function() {
        btnText.textContent = 'Running Pipeline...';
        btnSpinner.classList.remove('hidden');
        runBtn.disabled = true;
        resultsSection.classList.add('hidden');
        resetStepper();
        
        fetch('/api/run-pipeline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        })
        .then(function(response) {
            if (!response.ok) throw new Error('Failed');
            // Start polling for status
            pollForResults();
        })
        .catch(function(error) {
            console.error('Error:', error);
            pollForResults();
        });
    });
    
    function pollForResults() {
        var poll = setInterval(function() {
            fetch('/api/status')
                .then(function(r) { return r.json(); })
                .then(function(status) {
                    for (var i = 1; i <= 4; i++) {
                        var s = status.stages[String(i)];
                        if (s && s.status === 'running') {
                            updateStage(i, 'running', s.name + '...');
                        } else if (s && s.status === 'complete') {
                            updateStage(i, 'complete', 'Complete');
                        }
                    }
                    
                    if (status.status === 'complete') {
                        clearInterval(poll);
                        fetch('/api/results')
                            .then(function(r) { return r.json(); })
                            .then(function(results) {
                                renderResultsFromAPI(results);
                                finishPipeline();
                            });
                    } else if (status.status === 'error') {
                        clearInterval(poll);
                        loadCachedResults().then(function(loaded) {
                            btnText.textContent = loaded ? 'Re-run Pipeline' : 'Error - Retry';
                            btnSpinner.classList.add('hidden');
                            runBtn.disabled = false;
                        });
                    }
                })
                .catch(function(e) { console.error('Poll error:', e); });
        }, 3000);
    }
    
    function resetStepper() {
        for (var i = 1; i <= 4; i++) {
            var step = document.getElementById('step-' + i);
            var status = step.querySelector('.step-status');
            step.classList.remove('active', 'complete');
            status.textContent = 'Pending';
            if (i < 4) {
                var conn = document.getElementById('conn-' + i);
                if (conn) conn.classList.remove('active', 'complete');
            }
        }
    }
    
    function updateStage(stage, status, msg) {
        var step = document.getElementById('step-' + stage);
        if (!step) return;
        var statusEl = step.querySelector('.step-status');
        
        if (status === 'running') {
            step.classList.add('active');
            step.classList.remove('complete');
            statusEl.textContent = msg || 'Running...';
            if (stage > 1) {
                var prevConn = document.getElementById('conn-' + (stage-1));
                if (prevConn) { prevConn.classList.remove('active'); prevConn.classList.add('complete'); }
            }
            if (stage < 4) {
                var conn = document.getElementById('conn-' + stage);
                if (conn) conn.classList.add('active');
            }
        } else if (status === 'complete') {
            step.classList.remove('active');
            step.classList.add('complete');
            statusEl.textContent = msg || 'Complete';
            if (stage < 4) {
                var conn = document.getElementById('conn-' + stage);
                if (conn) { conn.classList.remove('active'); conn.classList.add('complete'); }
            }
        }
    }
    
    function finishPipeline() {
        btnText.textContent = 'Run Pipeline';
        btnSpinner.classList.add('hidden');
        runBtn.disabled = false;
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    function esc(str) {
        if (!str) return '';
        return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    
    function renderResultsFromAPI(data) {
        console.log('Rendering data with keys:', Object.keys(data));
        
        // === ACCOUNTS ===
        try {
            var accGrid = document.getElementById('accountsGrid');
            accGrid.innerHTML = '';
            var accounts = [];
            if (data.accounts && data.accounts.accounts) accounts = data.accounts.accounts;
            else if (Array.isArray(data.accounts)) accounts = data.accounts;
            console.log('Accounts:', accounts.length);
            
            accounts.forEach(function(acc) {
                var name = acc.company_name || acc.name || 'Unknown';
                var country = acc.country || '';
                var revenue = acc.revenue_usd || acc.revenue || '';
                var commodities = acc.commodities || [];
                var score = acc.icp_match_score || acc.matchScore || 0;
                var reasoning = acc.icp_match_reasoning || acc.reasoning || '';
                
                var tagsHTML = commodities.map(function(c) { return '<span class="tag">' + esc(c) + '</span>'; }).join('');
                
                accGrid.innerHTML += '<div class="card">' +
                    '<div class="card-title">' + esc(name) + '</div>' +
                    '<p style="color: var(--text-muted); font-size: 0.9rem;">' + esc(country) + ' &bull; ' + esc(revenue) + '</p>' +
                    '<div class="tags" style="margin-top: 1rem;">' + tagsHTML + '</div>' +
                    '<div style="margin-top: 1rem;">' +
                        '<div style="display: flex; justify-content: space-between; font-size: 0.85rem;">' +
                            '<span>ICP Match</span>' +
                            '<span style="color: var(--success); font-weight: 600;">' + score + '%</span>' +
                        '</div>' +
                        '<div class="match-bar-bg"><div class="match-bar" style="width: ' + score + '%"></div></div>' +
                        '<p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem;">' + esc(reasoning) + '</p>' +
                    '</div>' +
                '</div>';
            });
        } catch(e) { console.error('Accounts render error:', e); }
        
        // === CONTACTS ===
        try {
            var tBody = document.getElementById('contactsTableBody');
            tBody.innerHTML = '';
            var contacts = [];
            if (data.contacts && data.contacts.contacts) contacts = data.contacts.contacts;
            else if (Array.isArray(data.contacts)) contacts = data.contacts;
            console.log('Contacts:', contacts.length);
            
            contacts.forEach(function(c) {
                var company = c.company || '';
                var name = c.name || '';
                var title = c.title || c.role || '';
                var seniority = c.seniority || '';
                var linkedin = c.linkedin_url || c.linkedin || '#';
                var email = c.email || 'Not publicly available';
                var linkText = (linkedin !== '#' && linkedin !== 'Not publicly available') ? 'Profile' : 'N/A';
                
                tBody.innerHTML += '<tr>' +
                    '<td><strong>' + esc(company) + '</strong></td>' +
                    '<td>' + esc(name) + '</td>' +
                    '<td>' + esc(title) + '</td>' +
                    '<td><span class="tag" style="background: rgba(255,255,255,0.1); color: #fff;">' + esc(seniority) + '</span></td>' +
                    '<td><a href="' + esc(linkedin) + '" style="color: var(--accent-primary); text-decoration: none;" target="_blank">' + linkText + '</a></td>' +
                    '<td style="font-size: 0.85rem;">' + esc(email) + '</td>' +
                '</tr>';
            });
        } catch(e) { console.error('Contacts render error:', e); }
        
        // === RESEARCH ===
        try {
            var resGrid = document.getElementById('researchGrid');
            resGrid.innerHTML = '';
            var briefs = [];
            if (data.research && data.research.research_briefs) briefs = data.research.research_briefs;
            else if (Array.isArray(data.research)) briefs = data.research;
            console.log('Research briefs:', briefs.length);
            
            briefs.forEach(function(r) {
                var company = r.company_name || r.company || '';
                var summary = r.executive_summary || '';
                var news = r.recent_news || [];
                var techSignals = r.technology_signals || [];
                var angle = r.flytbase_angle || {};
                
                var newsHTML = '';
                news.slice(0, 3).forEach(function(n) {
                    if (typeof n === 'string') { newsHTML += '<li>' + esc(n) + '</li>'; }
                    else { newsHTML += '<li><strong>' + esc(n.headline || '') + '</strong>: ' + esc(n.detail || '') + '</li>'; }
                });
                if (!newsHTML) newsHTML = '<li>No recent news found</li>';
                
                var techHTML = '';
                techSignals.slice(0, 3).forEach(function(t) {
                    if (typeof t === 'string') { techHTML += '<li>' + esc(t) + '</li>'; }
                    else { techHTML += '<li><strong>' + esc(t.signal || '') + '</strong>: ' + esc(t.detail || '') + '</li>'; }
                });
                if (!techHTML) techHTML = '<li>No tech signals found</li>';
                
                var angleText = '';
                if (typeof angle === 'string') { angleText = angle; }
                else { angleText = (angle.primary_use_case || '') + ' ' + (Array.isArray(angle.pain_points_addressed) ? angle.pain_points_addressed.join(', ') : ''); }
                if (!angleText.trim()) angleText = 'Autonomous drone inspection for hazardous site monitoring';
                
                resGrid.innerHTML += '<div class="card" style="grid-column: 1 / -1;">' +
                    '<div class="card-title">' + esc(company) + ' - Research Brief</div>' +
                    '<p style="color: var(--text-muted); font-size: 0.9rem; margin: 0.5rem 0 1rem;">' + esc(summary) + '</p>' +
                    '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">' +
                        '<div><h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">Recent News</h4>' +
                            '<ul style="padding-left: 1.2rem; font-size: 0.9rem; color: var(--text-muted);">' + newsHTML + '</ul></div>' +
                        '<div><h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">Technology Signals</h4>' +
                            '<ul style="padding-left: 1.2rem; font-size: 0.9rem; color: var(--text-muted);">' + techHTML + '</ul></div>' +
                        '<div><h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">FlytBase Angle</h4>' +
                            '<p style="font-size: 0.9rem; color: var(--text-muted);">' + esc(angleText) + '</p></div>' +
                    '</div>' +
                '</div>';
            });
        } catch(e) { console.error('Research render error:', e); }
        
        // === EMAILS ===
        try {
            var emailGrid = document.getElementById('emailsGrid');
            emailGrid.innerHTML = '';
            var emails = [];
            if (data.emails && data.emails.emails) emails = data.emails.emails;
            else if (Array.isArray(data.emails)) emails = data.emails;
            console.log('Emails:', emails.length);
            
            emails.forEach(function(e) {
                var contactName = e.contact_name || e.to || '';
                var company = e.company || '';
                var subject = e.subject || '';
                var body = e.body || '';
                var score = e.quality_score || e.score || 0;
                var notes = e.personalization_notes || '';
                
                emailGrid.innerHTML += '<div class="card" style="grid-column: 1 / -1;">' +
                    '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">' +
                        '<div>' +
                            '<div style="font-size: 0.85rem; color: var(--text-muted);">To: ' + esc(contactName) + ' (' + esc(company) + ')</div>' +
                            '<div style="font-weight: 600; font-size: 1.1rem; margin-top: 0.25rem;">Subject: ' + esc(subject) + '</div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="email-body" style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; font-size: 0.95rem; white-space: pre-wrap; color: #e5e7eb; line-height: 1.6;">' + esc(body) + '</div>' +
                    '<div style="margin-top: 1rem; font-size: 0.85rem;">' +
                        '<span style="color: var(--text-muted);">Quality Score:</span>' +
                        '<span style="color: var(--success); font-weight: 600;"> ' + score + '/100</span>' +
                    '</div>' +
                '</div>';
            });
        } catch(e) { console.error('Emails render error:', e); }
    }
});
