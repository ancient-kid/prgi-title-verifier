/**
 * PRGI Title Verification Web Application Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // DOM Elements
    const navTabs = document.querySelectorAll(".nav-tab");
    const tabContents = document.querySelectorAll(".tab-content");

    const titleInput = document.getElementById("title-input");
    const clearBtn = document.getElementById("clear-btn");
    const languageSelect = document.getElementById("language-select");
    const periodicitySelect = document.getElementById("periodicity-select");
    const stateSelect = document.getElementById("state-select");
    const verifyBtn = document.getElementById("verify-btn");
    const applyBtn = document.getElementById("apply-btn");
    const chips = document.querySelectorAll(".chip");

    const probCircle = document.getElementById("prob-circle");
    const probPercentage = document.getElementById("prob-percentage");
    const verdictBadge = document.getElementById("verdict-badge");
    const verdictTitle = document.getElementById("verdict-title");
    const verdictSummary = document.getElementById("verdict-summary");
    const executionTime = document.getElementById("execution-time");

    // Steppers
    const step1 = document.getElementById("step-1");
    const step1Sub = document.getElementById("step-1-sub");
    const step1Status = document.getElementById("step-1-status");

    const step2 = document.getElementById("step-2");
    const step2Sub = document.getElementById("step-2-sub");
    const step2Status = document.getElementById("step-2-status");

    const step3 = document.getElementById("step-3");
    const step3Sub = document.getElementById("step-3-sub");
    const step3Status = document.getElementById("step-3-status");

    const step4 = document.getElementById("step-4");
    const step4Sub = document.getElementById("step-4-sub");
    const step4Status = document.getElementById("step-4-status");

    // Stage 4 Vectors
    const vectorScoresCard = document.getElementById("vector-scores-card");
    const phoneticScoreVal = document.getElementById("phonetic-score-val");
    const phoneticBar = document.getElementById("phonetic-bar");
    const orthoScoreVal = document.getElementById("ortho-score-val");
    const orthoBar = document.getElementById("ortho-bar");
    const semanticScoreVal = document.getElementById("semantic-score-val");
    const semanticBar = document.getElementById("semantic-bar");

    // Detailed Sections
    const reasonsContainer = document.getElementById("reasons-container");
    const reasonsList = document.getElementById("reasons-list");
    const matchesContainer = document.getElementById("matches-container");
    const matchesTbody = document.getElementById("matches-tbody");
    const suggestionsContainer = document.getElementById("suggestions-container");
    const suggestionsList = document.getElementById("suggestions-list");

    // Batch Elements
    const batchTextarea = document.getElementById("batch-textarea");
    const batchRunBtn = document.getElementById("batch-run-btn");
    const batchSampleBtn = document.getElementById("batch-sample-btn");
    const batchExportBtn = document.getElementById("batch-export-btn");
    const statTotal = document.getElementById("stat-total");
    const statApproved = document.getElementById("stat-approved");
    const statRejected = document.getElementById("stat-rejected");
    const statReview = document.getElementById("stat-review");
    const batchResultsTbody = document.getElementById("batch-results-tbody");
    let batchDataCache = [];

    // Lock Simulator Elements
    const simTitleA = document.getElementById("sim-title-a");
    const simUserABtn = document.getElementById("sim-user-a-btn");
    const simResA = document.getElementById("sim-res-a");
    const simTitleB = document.getElementById("sim-title-b");
    const simUserBBtn = document.getElementById("sim-user-b-btn");
    const simResB = document.getElementById("sim-res-b");
    const refreshLocksBtn = document.getElementById("refresh-locks-btn");
    const locksTbody = document.getElementById("locks-tbody");

    // DB Elements
    const dbSearchInput = document.getElementById("db-search-input");
    const dbSearchBtn = document.getElementById("db-search-btn");
    const registryTbody = document.getElementById("registry-tbody");

    // Circumference for 54px radius circle = 2 * PI * 54 ≈ 339.292
    const CIRCLE_CIRCUMFERENCE = 339.292;

    // Set Circle Gauge
    function setGaugePercentage(percent, status) {
        const offset = CIRCLE_CIRCUMFERENCE - (percent / 100) * CIRCLE_CIRCUMFERENCE;
        probCircle.style.strokeDashoffset = offset;
        probPercentage.textContent = `${Math.round(percent)}%`;

        if (status === "Approved") {
            probCircle.style.stroke = "#10B981"; // Emerald
            probPercentage.style.color = "#10B981";
        } else if (status === "Rejected") {
            probCircle.style.stroke = "#EF4444"; // Crimson
            probPercentage.style.color = "#EF4444";
        } else if (status === "Review Needed") {
            probCircle.style.stroke = "#F59E0B"; // Amber
            probPercentage.style.color = "#F59E0B";
        } else {
            probCircle.style.stroke = "#64748B";
            probPercentage.style.color = "#F8FAFC";
        }
    }

    // Reset UI State
    function resetUI() {
        setGaugePercentage(0, "neutral");
        probPercentage.textContent = "--%";
        verdictBadge.className = "verdict-pill neutral";
        verdictBadge.textContent = "Ready to Verify";
        verdictTitle.textContent = "Enter a title to begin verification";
        verdictSummary.textContent = "The multi-stage pipeline tests anchor distinctiveness, PRGI guideline blacklists, Frankentitle combinations, and tri-vector similarity.";
        executionTime.textContent = "Latency: 0 ms";

        [step1, step2, step3, step4].forEach(step => {
            step.className = "funnel-step";
        });
        step1Status.innerHTML = '<i data-lucide="circle-dashed"></i>';
        step2Status.innerHTML = '<i data-lucide="circle-dashed"></i>';
        step3Status.innerHTML = '<i data-lucide="circle-dashed"></i>';
        step4Status.innerHTML = '<i data-lucide="circle-dashed"></i>';
        step1Sub.textContent = "Extracts anchor and strips generic modifiers";
        step2Sub.textContent = "Disallowed words, Emblems Act, Police/CBI terms";
        step3Sub.textContent = "Aho-Corasick compound title detection";
        step4Sub.textContent = "Phonetic, Orthographic & Cross-Lingual Semantic";

        vectorScoresCard.classList.add("hidden");
        reasonsContainer.classList.add("hidden");
        matchesContainer.classList.add("hidden");
        suggestionsContainer.classList.add("hidden");
        applyBtn.disabled = true;
        lucide.createIcons();
    }

    // Navigation Tab Switching
    navTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            navTabs.forEach(t => t.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            tab.classList.add("active");
            const targetId = tab.getAttribute("data-tab");
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add("active");

            if (targetId === "rules-tab") loadGuidelines();
            if (targetId === "db-tab") searchRegistry("");
            if (targetId === "lock-tab") loadActiveLocks();
            lucide.createIcons();
        });
    });

    // Preset Chips Click
    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            const title = chip.getAttribute("data-title");
            titleInput.value = title;
            runVerification();
        });
    });

    clearBtn.addEventListener("click", () => {
        titleInput.value = "";
        resetUI();
    });

    verifyBtn.addEventListener("click", () => {
        runVerification();
    });

    titleInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            runVerification();
        }
    });

    // Verification Logic
    async function runVerification() {
        const title = titleInput.value.trim();
        if (!title) {
            alert("Please enter a title to verify.");
            return;
        }

        verifyBtn.disabled = true;
        verifyBtn.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Processing...';
        lucide.createIcons();

        try {
            const payload = {
                title: title,
                language: languageSelect.value,
                state: stateSelect.value,
                periodicity: periodicitySelect.value,
                applicant_id: "USER_WEB_ACTIVE"
            };

            const response = await fetch("/api/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Server returned status: ${response.status}`);
            }

            const data = await response.json();
            renderVerificationResults(data);
        } catch (err) {
            console.error("Verification error:", err);
            alert("Failed to complete verification. Please verify backend service status.");
        } finally {
            verifyBtn.disabled = false;
            verifyBtn.innerHTML = '<i data-lucide="scan"></i> Verify Title Now';
            lucide.createIcons();
        }
    }

    // Render Verification Results
    function renderVerificationResults(data) {
        const prob = data.verification_probability;
        const status = data.status;

        // 1. Gauge & Hero Update
        setGaugePercentage(prob, status);
        executionTime.textContent = `Latency: ${data.execution_time_ms} ms`;
        verdictTitle.textContent = `"${data.raw_title}"`;

        if (status === "Approved") {
            verdictBadge.className = "verdict-pill approved";
            verdictBadge.textContent = "Approved / High Distinctiveness";
            verdictSummary.textContent = "Title passed all guideline, phonetic, orthographic, and cross-lingual checks. No conflicting registration found.";
            applyBtn.disabled = false;
        } else if (status === "Rejected") {
            verdictBadge.className = "verdict-pill rejected";
            verdictBadge.textContent = "Rejected / Guideline Conflict";
            verdictSummary.textContent = data.reasons.length > 0 ? data.reasons[0].explanation : "High similarity with registered titles.";
            applyBtn.disabled = true;
        } else {
            verdictBadge.className = "verdict-pill review";
            verdictBadge.textContent = "Officer Review Needed";
            verdictSummary.textContent = "Moderate similarity detected. Further manual verification by PRGI officer is recommended.";
            applyBtn.disabled = false;
        }

        // 2. Multi-Stage Funnel Stepper Updates
        const s1 = data.stage_results?.stage1;
        const s2 = data.stage_results?.stage2;
        const s3 = data.stage_results?.stage3;
        const s4 = data.stage_results?.stage4;

        // Stage 1
        if (s1) {
            if (s1.is_purely_generic) {
                step1.className = "funnel-step failed";
                step1Status.innerHTML = '<i data-lucide="x-circle"></i>';
                step1Sub.textContent = "Failed: Purely generic modifiers without distinctive anchor word.";
            } else {
                step1.className = "funnel-step passed";
                step1Status.innerHTML = '<i data-lucide="check-circle-2"></i>';
                step1Sub.textContent = `Extracted Anchor: "${s1.anchor_words}" (Stripped: ${s1.stripped_prefixes.concat(s1.stripped_suffixes).join(", ") || "None"})`;
            }
        }

        // Stage 2
        if (s2) {
            if (!s2.passed) {
                step2.className = "funnel-step failed";
                step2Status.innerHTML = '<i data-lucide="x-circle"></i>';
                step2Sub.textContent = `Failed: Violated PRGI blacklist (${s2.violations.map(v => v.term).join(", ")})`;
            } else {
                step2.className = "funnel-step passed";
                step2Status.innerHTML = '<i data-lucide="check-circle-2"></i>';
                step2Sub.textContent = "Passed: No prohibited security or law-enforcement terms detected.";
            }
        } else {
            step2.className = "funnel-step";
            step2Status.innerHTML = '<i data-lucide="minus-circle"></i>';
            step2Sub.textContent = "Skipped due to prior stage rejection.";
        }

        // Stage 3
        if (s3) {
            if (s3.is_frankentitle) {
                step3.className = "funnel-step failed";
                step3Status.innerHTML = '<i data-lucide="x-circle"></i>';
                step3Sub.textContent = `Failed: Compound title formed from '${s3.components.join("' + '")}'`;
            } else {
                step3.className = "funnel-step passed";
                step3Status.innerHTML = '<i data-lucide="check-circle-2"></i>';
                step3Sub.textContent = "Passed: Not a combination of existing registered titles.";
            }
        } else {
            step3.className = "funnel-step";
            step3Status.innerHTML = '<i data-lucide="minus-circle"></i>';
            step3Sub.textContent = "Skipped due to prior stage rejection.";
        }

        // Stage 4
        if (s4) {
            const highestSim = data.highest_similarity_score || 0;
            if (highestSim >= 70) {
                step4.className = "funnel-step failed";
                step4Status.innerHTML = '<i data-lucide="x-circle"></i>';
                step4Sub.textContent = `Failed: High similarity score (${highestSim}%) against existing database titles.`;
            } else if (highestSim >= 40) {
                step4.className = "funnel-step passed";
                step4Status.innerHTML = '<i data-lucide="alert-circle"></i>';
                step4Sub.textContent = `Review: Moderate similarity (${highestSim}%).`;
            } else {
                step4.className = "funnel-step passed";
                step4Status.innerHTML = '<i data-lucide="check-circle-2"></i>';
                step4Sub.textContent = `Passed: Distinctive title (Highest similarity: ${highestSim}%).`;
            }

            // Vector Scores Breakdown
            if (data.max_scores) {
                vectorScoresCard.classList.remove("hidden");
                phoneticScoreVal.textContent = `${data.max_scores.phonetic}%`;
                phoneticBar.style.width = `${data.max_scores.phonetic}%`;

                orthoScoreVal.textContent = `${data.max_scores.orthographic}%`;
                orthoBar.style.width = `${data.max_scores.orthographic}%`;

                semanticScoreVal.textContent = `${data.max_scores.semantic}%`;
                semanticBar.style.width = `${data.max_scores.semantic}%`;
            }
        } else {
            step4.className = "funnel-step";
            step4Status.innerHTML = '<i data-lucide="minus-circle"></i>';
            step4Sub.textContent = "Skipped due to prior stage rejection.";
            vectorScoresCard.classList.add("hidden");
        }

        // 3. Reasons List
        if (data.reasons && data.reasons.length > 0) {
            reasonsContainer.classList.remove("hidden");
            reasonsList.innerHTML = data.reasons.map(r => `
                <div class="reason-item ${status === 'Approved' ? 'safe' : ''}">
                    <div class="reason-rule">${r.stage} &bull; ${r.rule} (${r.guideline_ref})</div>
                    <div>${r.explanation}</div>
                </div>
            `).join("");
        } else {
            reasonsContainer.classList.add("hidden");
        }

        // 4. Matches Table
        if (data.top_matches && data.top_matches.length > 0) {
            matchesContainer.classList.remove("hidden");
            matchesTbody.innerHTML = data.top_matches.map(m => {
                const simPct = Math.round(m.highest_similarity * 100);
                const badgeClass = simPct >= 70 ? 'high' : (simPct >= 40 ? 'med' : 'low');
                return `
                    <tr>
                        <td><strong>${m.title}</strong></td>
                        <td><span class="sim-badge ${badgeClass}">${simPct}%</span></td>
                        <td>${Math.round(m.phonetic_similarity * 100)}%</td>
                        <td>${Math.round(m.orthographic_similarity * 100)}%</td>
                        <td>${Math.round(m.semantic_similarity * 100)}%</td>
                        <td><span class="text-muted">${m.registration_no} &bull; ${m.state}</span></td>
                    </tr>
                `;
            }).join("");
        } else {
            matchesContainer.classList.add("hidden");
        }

        // 5. Suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            suggestionsContainer.classList.remove("hidden");
            suggestionsList.innerHTML = data.suggestions.map(s => `<li>${s}</li>`).join("");
        } else {
            suggestionsContainer.classList.add("hidden");
        }

        lucide.createIcons();
    }

    // Submit Application & Acquire Lock
    applyBtn.addEventListener("click", async () => {
        const title = titleInput.value.trim();
        if (!title) return;

        const applicantName = prompt("Enter Applicant / Publishing Company Name:", "Times Group Media");
        if (!applicantName) return;

        applyBtn.disabled = true;
        try {
            const res = await fetch("/api/apply", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: title,
                    applicant_id: `APP_${Math.floor(1000 + Math.random() * 9000)}`,
                    applicant_name: applicantName,
                    language: languageSelect.value,
                    state: stateSelect.value,
                    periodicity: periodicitySelect.value,
                    ttl_seconds: 600
                })
            });
            const data = await res.json();
            if (data.success) {
                alert(`Application Success!\nApplication No: ${data.application_no}\n${data.message}`);
                loadActiveLocks();
            } else {
                alert(`Application Error:\n${data.message}`);
            }
        } catch (e) {
            alert("Failed to submit application.");
        } finally {
            applyBtn.disabled = false;
        }
    });

    // =========================================================
    // TAB 2: Batch Verification
    // =========================================================
    batchSampleBtn.addEventListener("click", () => {
        batchTextarea.value = [
            "The Crime Investigation Daily",
            "The Daily Mumbai Express",
            "The Daily News",
            "Hindu Indian Express",
            "Namascar India",
            "Daily Evening",
            "Daineq Bhaskar",
            "The Tymes of India",
            "Morning News",
            "Astra Quantum Aerospace Journal",
            "Himachal Alpine Flora Gazette"
        ].join("\n");
    });

    batchRunBtn.addEventListener("click", async () => {
        const lines = batchTextarea.value.split("\n").map(l => l.trim()).filter(l => l.length > 0);
        if (lines.length === 0) {
            alert("Please enter one or more titles in the textarea.");
            return;
        }

        batchRunBtn.disabled = true;
        batchRunBtn.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Screening...';
        lucide.createIcons();

        try {
            const response = await fetch("/api/batch-verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ titles: lines })
            });
            const data = await response.json();
            batchDataCache = data.results;

            statTotal.textContent = data.total_processed;
            statApproved.textContent = data.approved_count;
            statRejected.textContent = data.rejected_count;
            statReview.textContent = data.review_needed_count;

            batchResultsTbody.innerHTML = data.results.map((r, idx) => {
                const statusClass = r.status === 'Approved' ? 'approved' : (r.status === 'Rejected' ? 'rejected' : 'review');
                const triggerStage = r.reasons && r.reasons.length > 0 ? r.reasons[0].stage : 'Stage 4';
                const mainReason = r.reasons && r.reasons.length > 0 ? r.reasons[0].explanation : 'Distinctive title';
                return `
                    <tr>
                        <td>${idx + 1}</td>
                        <td><strong>${r.raw_title}</strong></td>
                        <td><span class="sim-badge ${r.verification_probability >= 70 ? 'low' : 'high'}">${r.verification_probability}%</span></td>
                        <td><span class="verdict-pill ${statusClass}">${r.status}</span></td>
                        <td><span class="text-muted">${triggerStage}</span></td>
                        <td><small>${mainReason}</small></td>
                    </tr>
                `;
            }).join("");

            batchExportBtn.disabled = false;
        } catch (e) {
            console.error("Batch error:", e);
            alert("Batch processing failed.");
        } finally {
            batchRunBtn.disabled = false;
            batchRunBtn.innerHTML = '<i data-lucide="play"></i> Run Batch Screen';
            lucide.createIcons();
        }
    });

    batchExportBtn.addEventListener("click", () => {
        if (!batchDataCache.length) return;
        let csv = "Index,Title,Verification Probability,Status,Decision,Execution Time (ms),Primary Reason\n";
        batchDataCache.forEach((r, i) => {
            const reason = r.reasons && r.reasons.length > 0 ? r.reasons[0].explanation.replace(/"/g, '""') : "";
            csv += `${i + 1},"${r.raw_title}",${r.verification_probability}%,${r.status},${r.decision},${r.execution_time_ms},"${reason}"\n`;
        });
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `prgi_title_verification_report_${Date.now()}.csv`;
        a.click();
    });

    // =========================================================
    // TAB 3: Lock Simulator
    // =========================================================
    simUserABtn.addEventListener("click", async () => {
        const title = simTitleA.value.trim();
        if (!title) return;

        simUserABtn.disabled = true;
        simResA.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Submitting User A application...';
        lucide.createIcons();

        try {
            const res = await fetch("/api/apply", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: title,
                    applicant_id: "USER_A_ALPHA",
                    applicant_name: "Applicant Alpha",
                    ttl_seconds: 600
                })
            });
            const data = await res.json();
            if (data.success) {
                simResA.className = "sim-result-box success";
                simResA.innerHTML = `<strong>LOCK ACQUIRED (200 OK)</strong><br>Application No: ${data.application_no}<br>Title is now locked for 600s in Redis.`;
            } else {
                simResA.className = "sim-result-box error";
                simResA.innerHTML = `<strong>REJECTED</strong><br>${data.message}`;
            }
            loadActiveLocks();
        } catch (e) {
            simResA.className = "sim-result-box error";
            simResA.textContent = "Simulation network error.";
        } finally {
            simUserABtn.disabled = false;
        }
    });

    simUserBBtn.addEventListener("click", async () => {
        const title = simTitleB.value.trim();
        if (!title) return;

        simUserBBtn.disabled = true;
        simResB.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> User B attempting verification 5 mins later...';
        lucide.createIcons();

        try {
            const res = await fetch("/api/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: title,
                    applicant_id: "USER_B_BETA"
                })
            });
            const data = await res.json();
            if (data.status === "Rejected" && data.decision === "REJECTED_PENDING_COLLISION") {
                simResB.className = "sim-result-box error";
                simResB.innerHTML = `<strong>COLLISION DETECTED (0% Probability)</strong><br>${data.reasons[0].explanation}`;
            } else if (data.status === "Approved") {
                simResB.className = "sim-result-box success";
                simResB.innerHTML = `<strong>No Collision</strong>: Title verification probability is ${data.verification_probability}%.`;
            } else {
                simResB.className = "sim-result-box error";
                simResB.innerHTML = `<strong>Rejected</strong>: ${data.reasons[0].explanation}`;
            }
        } catch (e) {
            simResB.className = "sim-result-box error";
            simResB.textContent = "Simulation network error.";
        } finally {
            simUserBBtn.disabled = false;
        }
    });

    async function loadActiveLocks() {
        try {
            const res = await fetch("/api/locks");
            const data = await res.json();
            if (data.length === 0) {
                locksTbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No active locks in cache.</td></tr>';
                return;
            }
            locksTbody.innerHTML = data.map(lock => `
                <tr>
                    <td><strong>${lock.title}</strong></td>
                    <td><code>${lock.applicant_id}</code></td>
                    <td>${lock.applicant_name}</td>
                    <td><span class="sim-badge med">${lock.ttl_remaining}s</span></td>
                    <td>
                        <button class="btn btn-sm btn-secondary release-lock-btn" data-title="${lock.title}" data-applicant="${lock.applicant_id}">
                            Release
                        </button>
                    </td>
                </tr>
            `).join("");

            document.querySelectorAll(".release-lock-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const t = btn.getAttribute("data-title");
                    const a = btn.getAttribute("data-applicant");
                    await fetch(`/api/locks/release?title=${encodeURIComponent(t)}&applicant_id=${encodeURIComponent(a)}`, { method: "POST" });
                    loadActiveLocks();
                });
            });
        } catch (e) {
            console.error("Lock load error:", e);
        }
    }

    refreshLocksBtn.addEventListener("click", loadActiveLocks);

    // =========================================================
    // TAB 4: PRGI Rulebook
    // =========================================================
    async function loadGuidelines() {
        const container = document.getElementById("rules-cards-container");
        try {
            const res = await fetch("/api/guidelines");
            const data = await res.json();
            container.innerHTML = data.guidelines.map(g => `
                <div class="rule-card">
                    <span class="rule-badge">${g.guideline_ref}</span>
                    <div class="rule-title">${g.title}</div>
                    <div class="rule-desc">${g.description}</div>
                    <div class="rule-examples">
                        ${g.examples.map(ex => `<span class="ex-tag">${ex}</span>`).join("")}
                    </div>
                </div>
            `).join("");
        } catch (e) {
            console.error("Guidelines load error:", e);
        }
    }

    // =========================================================
    // TAB 5: Registry Browser
    // =========================================================
    async function searchRegistry(query) {
        registryTbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Searching database...</td></tr>';
        try {
            const res = await fetch(`/api/titles/search?query=${encodeURIComponent(query)}&limit=30`);
            const data = await res.json();
            if (!data.titles || data.titles.length === 0) {
                registryTbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No matching titles found in registry.</td></tr>';
                return;
            }
            registryTbody.innerHTML = data.titles.map(t => `
                <tr>
                    <td><code>#${t.id + 1}</code></td>
                    <td><strong>${t.title}</strong></td>
                    <td><span class="text-muted">${t.anchor_words || "N/A"}</span></td>
                    <td><code>${t.registration_no}</code></td>
                    <td>${t.language}</td>
                    <td>${t.state}</td>
                    <td>${t.periodicity}</td>
                </tr>
            `).join("");
        } catch (e) {
            console.error("Registry search error:", e);
        }
    }

    dbSearchBtn.addEventListener("click", () => {
        searchRegistry(dbSearchInput.value.trim());
    });

    dbSearchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            searchRegistry(dbSearchInput.value.trim());
        }
    });

    // Check system status initially
    fetch("/api/health")
        .then(r => r.json())
        .then(d => {
            const label = document.getElementById("system-status-label");
            if (label) label.textContent = `${d.total_registered_titles.toLocaleString()}+ Titles Indexed`;
        })
        .catch(e => console.log("Health check note:", e));
});
