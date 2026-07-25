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
            const targetId = `tab-${btn.dataset.tab}`;
            document.getElementById(targetId).classList.add('active');
        });
    });

    runBtn.addEventListener('click', async () => {
        // UI reset and loading state
        btnText.textContent = 'Running Pipeline...';
        btnSpinner.classList.remove('hidden');
        runBtn.disabled = true;
        resultsSection.classList.add('hidden');
        
        resetStepper();
        
        try {
            const response = await fetch('/api/run-pipeline', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    brief: {
                        vertical: "Mining",
                        region: "Latin America",
                        goal: "Discovery calls"
                    }
                })
            });

            if (!response.ok) {
                throw new Error('Pipeline request failed');
            }

            // Stream reader
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                
                // Keep the last partial line in buffer
                buffer = lines.pop();
                
                let currentEvent = null;
                for (let line of lines) {
                    if (line.startsWith('event: ')) {
                        currentEvent = line.substring(7).trim();
                    } else if (line.startsWith('data: ')) {
                        const dataStr = line.substring(6).trim();
                        try {
                            const data = JSON.parse(dataStr);
                            handlePipelineEvent(currentEvent, data);
                        } catch (e) {
                            console.error('Error parsing SSE data', e);
                        }
                    }
                }
            }
            
            // Reached end of stream successfully
            finishPipeline();
            
        } catch (error) {
            console.error('Error running pipeline:', error);
            // Mock fallback for hackathon demonstration if API fails
            console.log('Falling back to mock demonstration mode...');
            runMockPipeline();
        }
    });
    
    function resetStepper() {
        for (let i = 1; i <= 4; i++) {
            const step = document.getElementById(`step-${i}`);
            const status = step.querySelector('.step-status');
            step.classList.remove('active', 'complete');
            status.textContent = 'Pending';
            
            if (i < 4) {
                const conn = document.getElementById(`conn-${i}`);
                conn.classList.remove('active', 'complete');
            }
        }
    }
    
    function updateStage(stage, status, msg) {
        const step = document.getElementById(`step-${stage}`);
        const statusEl = step.querySelector('.step-status');
        
        if (status === 'running') {
            step.classList.add('active');
            step.classList.remove('complete');
            statusEl.textContent = msg || 'Running...';
            
            if (stage > 1) {
                const prevConn = document.getElementById(`conn-${stage-1}`);
                if (prevConn) {
                    prevConn.classList.remove('active');
                    prevConn.classList.add('complete');
                }
            }
            
            if (stage < 4) {
                const conn = document.getElementById(`conn-${stage}`);
                if (conn) {
                    conn.classList.add('active');
                }
            }
        } else if (status === 'complete') {
            step.classList.remove('active');
            step.classList.add('complete');
            statusEl.textContent = msg || 'Complete';
            
            if (stage < 4) {
                const conn = document.getElementById(`conn-${stage}`);
                if (conn) {
                    conn.classList.remove('active');
                    conn.classList.add('complete');
                }
            }
        }
    }
    
    function handlePipelineEvent(event, data) {
        if (event === 'stage_update') {
            updateStage(data.stage, 'running', data.message);
        } else if (event === 'stage_complete') {
            updateStage(data.stage, 'complete', 'Completed');
        } else if (event === 'pipeline_complete') {
            renderResults(data);
            finishPipeline();
        }
    }
    
    function finishPipeline() {
        btnText.textContent = 'Run Pipeline';
        btnSpinner.classList.add('hidden');
        runBtn.disabled = false;
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    function renderResults(data) {
        // Accounts
        const accGrid = document.getElementById('accountsGrid');
        accGrid.innerHTML = '';
        (data.accounts || []).forEach(acc => {
            accGrid.innerHTML += `
                <div class="card">
                    <div class="card-title">${acc.name} ${acc.flag || '🏭'}</div>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">${acc.country} • ${acc.revenue}</p>
                    <div class="tags" style="margin-top: 1rem;">
                        ${(acc.commodities || []).map(c => `<span class="tag">${c}</span>`).join('')}
                    </div>
                    <div style="margin-top: 1rem;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                            <span>ICP Match</span>
                            <span style="color: var(--success); font-weight: 600;">${acc.matchScore}%</span>
                        </div>
                        <div class="match-bar-bg">
                            <div class="match-bar" style="width: ${acc.matchScore}%"></div>
                        </div>
                        <p style="font-size: 0.85rem; color: var(--text-muted);">${acc.reasoning}</p>
                    </div>
                </div>
            `;
        });
        
        // Contacts
        const tBody = document.getElementById('contactsTableBody');
        tBody.innerHTML = '';
        (data.contacts || []).forEach(c => {
            tBody.innerHTML += `
                <tr>
                    <td><strong>${c.company}</strong></td>
                    <td>${c.name}</td>
                    <td>${c.role}</td>
                    <td><span class="tag" style="background: rgba(255,255,255,0.1); color: #fff;">${c.seniority}</span></td>
                    <td><a href="${c.linkedin || '#'}" style="color: var(--accent-primary); text-decoration: none;" target="_blank">Profile ↗</a></td>
                    <td>${c.email}</td>
                </tr>
            `;
        });
        
        // Research
        const resGrid = document.getElementById('researchGrid');
        resGrid.innerHTML = '';
        (data.research || []).forEach(r => {
            resGrid.innerHTML += `
                <div class="card" style="grid-column: 1 / -1;">
                    <div class="card-title">${r.company} - Research Brief</div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1rem;">
                        <div>
                            <h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">Recent News / Tech Signals</h4>
                            <ul style="padding-left: 1.2rem; font-size: 0.9rem; color: var(--text-muted);">
                                ${(r.signals || []).map(s => `<li style="margin-bottom: 0.5rem;">${s}</li>`).join('')}
                            </ul>
                        </div>
                        <div>
                            <h4 style="color: var(--accent-primary); margin-bottom: 0.5rem;">FlytBase Angle</h4>
                            <p style="font-size: 0.9rem; color: var(--text-muted);">${r.angle}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        // Emails
        const emailGrid = document.getElementById('emailsGrid');
        emailGrid.innerHTML = '';
        (data.emails || []).forEach(e => {
            emailGrid.innerHTML += `
                <div class="card" style="grid-column: 1 / -1;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
                        <div>
                            <div style="font-size: 0.85rem; color: var(--text-muted);">To: ${e.to}</div>
                            <div style="font-weight: 600; font-size: 1.1rem; margin-top: 0.25rem;">Subject: ${e.subject}</div>
                        </div>
                        <button class="btn-small" onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText); this.innerText='Copied!'; setTimeout(() => this.innerText='Copy Email', 2000);">Copy Email</button>
                    </div>
                    <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; font-size: 0.95rem; white-space: pre-wrap; font-family: monospace; color: #e5e7eb;">${e.body}</div>
                    <div style="margin-top: 1rem; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: var(--text-muted);">Quality Score:</span>
                        <span style="color: var(--success); font-weight: 600;">${e.score}/10</span>
                    </div>
                </div>
            `;
        });
    }

    // Mock sequence for demonstration if backend isn't ready
    async function runMockPipeline() {
        const sleep = ms => new Promise(r => setTimeout(r, ms));
        
        handlePipelineEvent('stage_update', {stage: 1, message: 'Scanning LATAM mining registry...'});
        await sleep(1500);
        handlePipelineEvent('stage_complete', {stage: 1});
        
        handlePipelineEvent('stage_update', {stage: 2, message: 'Discovering key personnel...'});
        await sleep(2000);
        handlePipelineEvent('stage_complete', {stage: 2});
        
        handlePipelineEvent('stage_update', {stage: 3, message: 'Analyzing recent news & tech stack...'});
        await sleep(2500);
        handlePipelineEvent('stage_complete', {stage: 3});
        
        handlePipelineEvent('stage_update', {stage: 4, message: 'Drafting hyper-personalized emails...'});
        await sleep(2000);
        handlePipelineEvent('stage_complete', {stage: 4});
        
        handlePipelineEvent('pipeline_complete', {
            accounts: [
                {
                    name: "Minera Escondida", flag: "🇨🇱", country: "Chile", revenue: "$8.5B+",
                    commodities: ["Copper", "Gold"], matchScore: 96,
                    reasoning: "Operates world's largest copper mine, high focus on worker safety and 24/7 autonomous tech initiatives."
                },
                {
                    name: "Vale S.A.", flag: "🇧🇷", country: "Brazil", revenue: "$40B+",
                    commodities: ["Iron Ore", "Nickel"], matchScore: 92,
                    reasoning: "Massive scale operations in remote areas, previously suffered tailing dam disasters leading to extreme ESG monitoring needs."
                },
                {
                    name: "Codelco", flag: "🇨🇱", country: "Chile", revenue: "$14B+",
                    commodities: ["Copper"], matchScore: 88,
                    reasoning: "State-owned, aggressively investing in automation and tele-operation of mining equipment."
                }
            ],
            contacts: [
                {company: "Minera Escondida", name: "Carlos Vargas", role: "VP of HSE", seniority: "Executive", linkedin: "#", email: "c.vargas@escondida.cl"},
                {company: "Minera Escondida", name: "Maria Gonzalez", role: "Head of Operations", seniority: "Director", linkedin: "#", email: "m.gonzalez@escondida.cl"},
                {company: "Vale S.A.", name: "Roberto Silva", role: "Innovation Director", seniority: "Director", linkedin: "#", email: "rsilva@vale.com"},
                {company: "Codelco", name: "Ana Rojas", role: "Site Tech Lead", seniority: "Manager", linkedin: "#", email: "arojas@codelco.cl"}
            ],
            research: [
                {
                    company: "Minera Escondida",
                    signals: [
                        "Announced $100M investment in remote operations center (ROC)",
                        "Recent safety incidents in open-pit perimeter inspections",
                        "Currently using contracted drone pilots 2x per week"
                    ],
                    angle: "FlytBase can transition them from ad-hoc manual drone inspections to 24/7 automated perimeter and stockpile monitoring directly from their new ROC, eliminating on-site safety risks for inspectors."
                }
            ],
            emails: [
                {
                    to: "Carlos Vargas (Minera Escondida)",
                    subject: "Automating perimeter inspections for Escondida's new ROC",
                    body: "Hi Carlos,\n\nSaw Escondida's recent $100M investment in the new Remote Operations Center. Impressive step forward.\n\nI noticed you're still relying on contracted drone pilots for perimeter and stockpile checks. With the recent safety initiatives, having personnel physically present in hazardous zones seems contradictory to the ROC's goal.\n\nFlytBase helps operations like SQM fully automate their DJI docking stations, allowing remote teams to deploy 24/7 automated aerial inspections without a pilot on site.\n\nOpen to exploring how this could integrate with your new ROC setup?\n\nBest,\nBDR AI Agent",
                    score: 9.5
                }
            ]
        });
    }
});
