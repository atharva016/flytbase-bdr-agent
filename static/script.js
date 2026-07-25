document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('runPipelineBtn');
    const btnText = runBtn.querySelector('.btn-text');
    const btnSpinner = document.getElementById('btnSpinner');
    const resultsSection = document.getElementById('resultsSection');
    
    // Tab Switching Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });

    runBtn.addEventListener('click', async () => {
        btnText.textContent = 'Running Pipeline...';
        btnSpinner.classList.remove('hidden');
        runBtn.disabled = true;
        resultsSection.classList.add('hidden');
        resetStepper();
        
        try {
            // Step 1: Start the pipeline
            const response = await fetch('/api/run-pipeline', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            if (!response.ok) {
                throw new Error('Pipeline request failed');
            }

            // Step 2: Connect to SSE stream for real-time updates
            const evtSource = new EventSource('/api/stream');
            
            evtSource.addEventListener('stage_update', (e) => {
                const data = JSON.parse(e.data);
                updateStage(data.stage, 'running', data.message);
            });
            
            evtSource.addEventListener('stage_complete', (e) => {
                const data = JSON.parse(e.data);
                updateStage(data.stage, 'complete', 'Complete');
            });
            
            evtSource.addEventListener('pipeline_complete', (e) => {
                const data = JSON.parse(e.data);
                evtSource.close();
                renderResultsFromAPI(data);
                finishPipeline();
            });
            
            evtSource.addEventListener('pipeline_error', (e) => {
                const data = JSON.parse(e.data);
                evtSource.close();
                console.error('Pipeline error:', data.error);
                btnText.textContent = 'Error - Retry';
                btnSpinner.classList.add('hidden');
                runBtn.disabled = false;
            });
            
            evtSource.onerror = () => {
                evtSource.close();
                // Fallback: poll for results
                pollForResults();
            };
            
        } catch (error) {
            console.error('Error:', error);
            // Fallback: poll status endpoint
            pollForResults();
        }
    });
    
    // Poll /api/status as fallback when SSE doesn't work
    async function pollForResults() {
        const poll = setInterval(async () => {
            try {
                const r = await fetch('/api/status');
                const status = await r.json();
                
                // Update stages
                for (let i = 1; i <= 4; i++) {
                    const stageStatus = status.stages[String(i)]?.status;
                    if (stageStatus === 'running') {
                        updateStage(i, 'running', status.stages[String(i)].name + '...');
                    } else if (stageStatus === 'complete') {
                        updateStage(i, 'complete', 'Complete');
                    }
                }
                
                if (status.status === 'complete') {
                    clearInterval(poll);
                    // Fetch full results
                    const resultsResp = await fetch('/api/results');
                    const results = await resultsResp.json();
                    renderResultsFromAPI(results);
                    finishPipeline();
                } else if (status.status === 'error') {
                    clearInterval(poll);
                    btnText.textContent = 'Error - Retry';
                    btnSpinner.classList.add('hidden');
                    runBtn.disabled = false;
                }
            } catch (e) {
                console.error('Poll error:', e);
            }
        }, 3000); // Poll every 3 seconds
    }
    
    function resetStepper() {
        for (let i = 1; i <= 4; i++) {
            const step = document.getElementById(`step-${i}`);
            const status = step.querySelector('.step-status');
            step.classList.remove('active', 'complete');
            status.textContent = 'Pending';
            if (i < 4) {
                const conn = document.getElementById(`conn-${i}`);
                if (conn) conn.classList.remove('active', 'complete');
            }
        }
    }
    
    function updateStage(stage, status, msg) {
        const step = document.getElementById(`step-${stage}`);
        if (!step) return;
        const statusEl = step.querySelector('.step-status');
        
        if (status === 'running') {
            step.classList.add('active');
            step.classList.remove('complete');
            statusEl.textContent = msg || 'Running...';
            if (stage > 1) {
                const prevConn = document.getElementById(`conn-${stage-1}`);
                if (prevConn) { prevConn.classList.remove('active'); prevConn.classList.add('complete'); }
            }
            if (stage < 4) {
                const conn = document.getElementById(`conn-${stage}`);
                if (conn) conn.classList.add('active');
            }
        } else if (status === 'complete') {
            step.classList.remove('active');
            step.classList.add('complete');
            statusEl.textContent = msg || 'Complete';
            if (stage < 4) {
                const conn = document.getElementById(`conn-${stage}`);
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
    
    // Render results from the actual API response format
    function renderResultsFromAPI(data) {
        // === ACCOUNTS ===
        const accGrid = document.getElementById('accountsGrid');
        accGrid.innerHTML = '';
        const accounts = data.accounts?.accounts || data.accounts || [];
        accounts.forEach(acc => {
            const name = acc.company_name || acc.name || 'Unknown';
            const country = acc.country || '';
            const revenue = acc.revenue_usd || acc.revenue || '';
            const commodities = acc.commodities || [];
            const score = acc.icp_match_score || acc.matchScore || 0;
            const reasoning = acc.icp_match_reasoning || acc.reasoning || '';
            
            accGrid.innerHTML += `
                <div class="card">
                    <div class="card-title">${name}</div>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">${country} • ${revenue}</p>
                    <div class="tags" style="margin-top: 1rem;">
                        ${commodities.map(c => `<span class="tag">${c}</span>`).join('')}
                    </div>
                    <div style="margin-top: 1rem;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                            <span>ICP Match</span>
                            <span style="color: var(--success); font-weight: 600;">${score}%</span>
                        </div>
                        <div class="match-bar-bg">
                            <div class="match-bar" style="width: ${score}%"></div>
                        </div>
                        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem;">${reasoning}</p>
                    </div>
                </div>
            `;
        });
        
        // === CONTACTS ===
        const tBody = document.getElementById('contactsTableBody');
        tBody.innerHTML = '';
        const contacts = data.contacts?.contacts || data.contacts || [];
        contacts.forEach(c => {
            const company = c.company || '';
            const name = c.name || '';
            const title = c.title || c.role || '';
            const seniority = c.seniority || '';
            const linkedin = c.linkedin_url || c.linkedin || '#';
            const email = c.email || 'Not publicly available';
            
            tBody.innerHTML += `
                <tr>
                    <td><strong>${company}</strong></td>
                    <td>${name}</td>
                    <td>${title}</td>
                    <td><span class="tag" style="background: rgba(255,255,255,0.1); color: #fff;">${seniority}</span></td>
                    <td><a href="${linkedin}" style="color: var(--accent-primary); text-decoration: none;" target="_blank">${linkedin !== '#' && linkedin !== 'Not publicly available' ? 'Profile ↗' : 'N/A'}</a></td>
                    <td style="font-size: 0.85rem;">${email}</td>
                </tr>
            `;
        });
        
        // === RESEARCH ===
        const resGrid = document.getElementById('researchGrid');
        resGrid.innerHTML = '';
        const briefs = data.research?.research_briefs || data.research || [];
        briefs.forEach(r => {
            const company = r.company_name || r.company || '';
            const summary = r.executive_summary || '';
            const news = r.recent_news || [];
            const techSignals = r.technology_signals || [];
            const angle = r.flytbase_angle || {};
            
            const newsHTML = news.slice(0, 3).map(n => {
                if (typeof n === 'string') return `<li>${n}</li>`;
                return `<li><strong>${n.headline || ''}</strong>: ${n.detail || ''}</li>`;
            }).join('');
            
            const techHTML = techSignals.slice(0, 3).map(t => {
                if (typeof t === 'string') return `<li>${t}</li>`;
                return `<li><strong>${t.signal || ''}</strong>: ${t.detail || ''} <em style="color:var(--accent-primary);">${t.relevance_to_flytbase || ''}</em></li>`;
            }).join('');
            
            const angleText = typeof angle === 'string' ? angle : 
                (angle.primary_use_case || '') + ' ' + (angle.pain_points_addressed || []).join(', ');
            
            resGrid.innerHTML += `
                <div class="card" style="grid-column: 1 / -1;">
                    <div class="card-title">${company} - Research Brief</div>
                    <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0.5rem 0 1rem;">${summary}</p>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
                        <div>
                            <h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">Recent News</h4>
                            <ul style="padding-left: 1.2rem; font-size: 0.9rem; color: var(--text-muted);">${newsHTML || '<li>No recent news found</li>'}</ul>
                        </div>
                        <div>
                            <h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">Technology Signals</h4>
                            <ul style="padding-left: 1.2rem; font-size: 0.9rem; color: var(--text-muted);">${techHTML || '<li>No tech signals found</li>'}</ul>
                        </div>
                        <div>
                            <h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">FlytBase Angle</h4>
                            <p style="font-size: 0.9rem; color: var(--text-muted);">${angleText || 'Autonomous drone inspection for hazardous site monitoring'}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // === EMAILS ===
        const emailGrid = document.getElementById('emailsGrid');
        emailGrid.innerHTML = '';
        const emails = data.emails?.emails || data.emails || [];
        emails.forEach(e => {
            const contactName = e.contact_name || e.to || '';
            const company = e.company || '';
            const subject = e.subject || '';
            const body = e.body || '';
            const score = e.quality_score || e.score || 0;
            const notes = e.personalization_notes || '';
            
            emailGrid.innerHTML += `
                <div class="card" style="grid-column: 1 / -1;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
                        <div>
                            <div style="font-size: 0.85rem; color: var(--text-muted);">To: ${contactName} (${company})</div>
                            <div style="font-weight: 600; font-size: 1.1rem; margin-top: 0.25rem;">Subject: ${subject}</div>
                        </div>
                        <button class="btn-small" onclick="navigator.clipboard.writeText(this.closest('.card').querySelector('.email-body').innerText); this.innerText='Copied!'; setTimeout(() => this.innerText='Copy Email', 2000);">Copy Email</button>
                    </div>
                    <div class="email-body" style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; font-size: 0.95rem; white-space: pre-wrap; color: #e5e7eb; line-height: 1.6;">${body}</div>
                    <div style="margin-top: 1rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                        <div style="font-size: 0.85rem;">
                            <span style="color: var(--text-muted);">Quality Score:</span>
                            <span style="color: var(--success); font-weight: 600;"> ${score}/100</span>
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">${notes}</div>
                    </div>
                </div>
            `;
        });
    }
});
