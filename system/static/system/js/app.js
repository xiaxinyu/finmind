/* FinMind main app */
(function(){
  const { createApp } = window.Vue;
  const appDef = {
    data() {
      return {
        tab: 'dashboard',
        form: { description: '', money: '' },
        result: null,
        sampleLines: [],
        insights: null,
        distribution: [],
        palette: ['#22c55e','#60a5fa','#f59e0b','#ef4444','#a78bfa','#10b981','#f472b6'],
        donutStyle: '',
        health: { score: 0, spendControl: 0, savingsRate: 0 },
        coverageResult: null,
        coverageLoading: false,
        modelMetrics: null,
        modelMetricsLoading: false,
        modelMetricsLastUpdated: '',
        lifestyleResult: null,
        lifestyleLoading: false,
        unmatchedRows: [],
        unmatchedLoading: false,
        unmatchedSummary: null,
        unmatchedFilter: '',
        unmatchedTopN: 50,
        unmatchedPage: 1,
        unmatchedPageSize: 10,
        unmatchedDefaultPriority: 80,
        unmatchedMinCount: 1,
        unmatchedIgnoreKeywords: '',
        unmatchedAbortRequested: false,
        unmatchedBulkProgress: { action: '', done: 0, total: 0 },
        toastMessage: '',
        toastKind: '', // 'success', 'error', 'info'
        toastTimer: null,
        confirmVisible: false,
        confirmMessage: '',
        confirmCallback: null,
        confirmTitle: 'Confirm',
        recommendModalVisible: false,
        recommendRow: null,
        recommendCategoryId: '',
        recommendKeywords: '',
        recommendTags: '',
        recommendPatternType: 'contains',
        recommendPriority: 80,
        unmatchedStartDate: '',
        unmatchedEndDate: '',
        unmatchedBank: '',
        unmatchedCardType: '',
        unmatchedBankOptions: [],
        unmatchedCardTypeOptions: [],
        unmatchedBulkLoading: false,
        selectedUnmatchedCategory: '',
        selectedRuleIdForTag: '',
        createModalVisible: false,
        createModalRow: null,
        createModalCategoryId: '',
        createModalPattern: '',
        createModalPatternType: 'contains',
        createModalPriority: 80,
        createModalTags: '',
        createModalTokens: [],
        modalExpanded: {},
        modalCategoryQuery: '',
        coverageCategoryQuery: '',
        coverageCatOpen: false,
        coverageCatHoverIdx: 0,
        createModalFullscreen: false,
        recentCategoryIds: [],
        coverageExpanded: {},
        coveragePickerOpen: false,
        coverageAdvancedOpen: false,
        categories: [],
        ruleSearch: '',
        selectedCategoryId: '',
        selectedCategoryCode: '',
        selectedCategoryName: '',
        rules: [],
        rulesLoading: false,
        errorMsg: '',
        ruleForm: { pattern:'', patternType:'contains', priority:100, active:1, remark:'', minAmount:null, maxAmount:null, startDate:null, endDate:null },
        newRule: { pattern:'', patternType:'contains', priority:100 },
        onlyLeaves: false,
        onlyBranch: false,
        ruleFilter: '',
        activeOnly: false,
        selectedRuleIds: {},
        selectAllChecked: false,
        selectedBank: '',
        selectedCardType: '',
        bulkWeight: 100,
        selectedTxnType: 'all',
        expandedIds: {},
        chatMessages: [{ role: 'assistant', content: 'Hello! I am FinMind AI. How can I help you today?' }],
        chatInput: '',
        chatLoading: false,
        chatStatus: 'idle',
        chatRespStatus: null,
        chatError: '',
        busyMode: '',
        chatTimestamp: '',
        unmatchedDetailVisible: false,
        unmatchedDetailRows: [],
        unmatchedDetailLoading: false,
        unmatchedDetailDesc: '',
        unmatchedDetailSelection: [],
        batchAssignModalVisible: false,
        batchAssignCategoryId: ''
      };
    },
    created() {
      this.categoryQuery = '';
      this.catOpen = false;
      this.catHoverIdx = 0;
    },
    computed: {
      recommendedUnmatched() {
        const rows = Array.isArray(this.unmatchedRows) ? this.unmatchedRows : [];
        return rows.filter(r => r && r._reco);
      },
      pendingRecommendationsCount() {
        const rows = Array.isArray(this.unmatchedRows) ? this.unmatchedRows : [];
        return rows.filter(r => r && r._reco).length;
      },
      filteredUnmatchedRows() {
        const rows = Array.isArray(this.unmatchedRows) ? this.unmatchedRows.slice() : [];
        const q = (this.unmatchedFilter || '').trim().toLowerCase();
        let vis = rows;
        if (q) vis = vis.filter(x => (x.desc||'').toLowerCase().includes(q));
        const minc = Math.max(1, parseInt(this.unmatchedMinCount || 1, 10));
        vis = vis.filter(x => Number(x.count || 0) >= minc);
        const ignores = (this.unmatchedIgnoreKeywords || '').split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
        if (ignores.length) {
          vis = vis.filter(x => {
            const d = (x.desc || '').toLowerCase();
            for (let t of ignores) { if (t && d.includes(t)) return false; }
            return true;
          });
        }
        const n = parseInt(this.unmatchedTopN || 50, 10);
        vis = vis.slice(0, Math.max(1, n));
        return vis;
      },
      unmatchedTotalPages() {
        const total = (this.filteredUnmatchedRows || []).length;
        const size = Math.max(1, parseInt(this.unmatchedPageSize || 10, 10));
        return Math.max(1, Math.ceil(total / size));
      },
      paginatedUnmatchedRows() {
        const list = this.filteredUnmatchedRows || [];
        const size = Math.max(1, parseInt(this.unmatchedPageSize || 10, 10));
        const page = Math.min(Math.max(1, parseInt(this.unmatchedPage || 1, 10)), Math.max(1, Math.ceil(list.length / size)));
        const start = (page - 1) * size;
        return list.slice(start, start + size);
      },
      categoryOptions() {
        const rows = (this.categories || []).slice().sort((a,b)=>{
          if (a.sortNo !== b.sortNo) return a.sortNo - b.sortNo;
          return (a.code||'').localeCompare(b.code||'');
        });
        return rows.map(c => ({
          id: c.id,
          label: `${c.code || ''} ${c.name || ''}`.trim()
        }));
      },
      filteredCategoryOptions() {
        const q = (this.categoryQuery || '').trim().toLowerCase();
        const opts = this.categoryOptions;
        if (!q) return opts;
        return opts.filter(o => o.label.toLowerCase().includes(q));
      },
      filteredCategories() {
        const q = (this.ruleSearch || '').trim().toLowerCase();
        const all = (this.categories || []).slice();
        const byParent = {};
        all.forEach(c => {
          const pid = c.parentId || '';
          if (!byParent[pid]) byParent[pid] = [];
          byParent[pid].push(c);
        });
        Object.keys(byParent).forEach(pid => {
          byParent[pid].sort((a,b) => {
            if (a.sortNo !== b.sortNo) return a.sortNo - b.sortNo;
            return (a.code||'').localeCompare(b.code||'');
          });
        });
        const roots = (byParent[''] || all.filter(c => !c.parentId)).sort((a,b)=>{
          if (a.sortNo !== b.sortNo) return a.sortNo - b.sortNo;
          return (a.code||'').localeCompare(b.code||'');
        });
        const out = [];
        const pushNode = (node) => {
          out.push(node);
          const seen = {};
          const children = [].concat(byParent[node.id] || [], byParent[node.code] || []).filter(ch=>{
            const k = String(ch.code || ch.id || '');
            if (!k) return false;
            if (seen[k]) return false;
            seen[k] = true;
            return true;
          });
          if (this.expandedIds[node.id]) {
            children.forEach(ch => pushNode(ch));
          }
        };
        roots.forEach(r => pushNode(r));
        let vis = out;
        if (q) {
          vis = vis.filter(c => (c.name||'').toLowerCase().includes(q) || (c.code||'').toLowerCase().includes(q));
        }
        if (this.onlyBranch && this.selectedCategoryId) {
          const map = {};
          all.forEach(c => { map[c.id] = c.parentId; });
          const isDescendant = (x) => {
            if (x.id === this.selectedCategoryId) return true;
            let p = x.parentId;
            while (p) {
              if (p === this.selectedCategoryId) return true;
              p = map[p];
            }
            return false;
          };
          vis = vis.filter(isDescendant);
        }
        if (!this.onlyLeaves) return vis;
        return vis.filter(c => !this.hasChildren(c));
      },
      categoryBreadcrumb() {
        const id = this.selectedCategoryId;
        if (!id) return [];
        const byId = {};
        (this.categories || []).forEach(c => { byId[c.id] = c; });
        const chain = [];
        let cur = byId[id];
        while (cur) {
          chain.unshift({ code: cur.code, name: cur.name, id: cur.id });
          cur = cur.parentId ? byId[cur.parentId] : null;
        }
        return chain;
      },
      modalVisibleCategories() {
        const all = (this.categories || []).slice();
        const byParent = {};
        all.forEach(c => {
          const pid = c.parentId || '';
          if (!byParent[pid]) byParent[pid] = [];
          byParent[pid].push(c);
        });
        Object.keys(byParent).forEach(pid => {
          byParent[pid].sort((a,b) => {
            if ((a.sortNo||0) !== (b.sortNo||0)) return (a.sortNo||0) - (b.sortNo||0);
            return (a.code||'').localeCompare(b.code||'');
          });
        });
        const roots = (byParent[''] || all.filter(c => !c.parentId)).sort((a,b)=>{
          if ((a.sortNo||0) !== (b.sortNo||0)) return (a.sortNo||0) - (b.sortNo||0);
          return (a.code||'').localeCompare(b.code||'');
        });
        const out = [];
        const pushNode = (node) => {
          out.push(node);
          const seen = {};
          const children = [].concat(byParent[node.id] || [], byParent[node.code] || []).filter(ch=>{
            const k = String(ch.code || ch.id || '');
            if (!k) return false;
            if (seen[k]) return false;
            seen[k] = true;
            return true;
          });
          if (this.modalExpanded[node.id]) {
            children.forEach(ch => pushNode(ch));
          }
        };
        roots.forEach(r => pushNode(r));
        const q = (this.modalCategoryQuery || '').trim().toLowerCase();
        if (!q) return out;
        return out.filter(c => (c.name||'').toLowerCase().includes(q) || (c.code||'').toLowerCase().includes(q));
      },
      createModalCategoryName() {
        if (!this.createModalCategoryId) return '';
        const c = (this.categories || []).find(x => (x.code || x.id) === this.createModalCategoryId);
        return c ? `${c.name} (${c.code})` : this.createModalCategoryId;
      },
      visibleRules() {
        let rows = (this.rules || []).slice();
        const q = (this.ruleFilter || '').trim().toLowerCase();
        if (q) rows = rows.filter(r => (r.pattern||'').toLowerCase().includes(q));
        if (this.activeOnly) rows = rows.filter(r => !!r.active);
        if (this.selectedBank) rows = rows.filter(r => (r.bankCode||'') === this.selectedBank);
        if (this.selectedCardType) rows = rows.filter(r => (r.cardTypeCode||'') === this.selectedCardType);
        return rows;
      },
      bankOptions() {
        const set = new Set();
        (this.rules||[]).forEach(r => { if (r.bankCode) set.add(r.bankCode); });
        return Array.from(set).sort();
      },
      cardTypeOptions() {
        const set = new Set();
        (this.rules||[]).forEach(r => { if (r.cardTypeCode) set.add(r.cardTypeCode); });
        return Array.from(set).sort();
      },
      recentCategories() {
        const dict = {};
        (this.categories||[]).forEach(c => { dict[c.id] = `${c.code||''} ${c.name||''}`.trim(); });
        return (this.recentCategoryIds||[]).map(id => ({ id, label: dict[id] || id }));
      },
      coverageRecommendedCategories() {
        const list = (this.categories||[]).slice();
        const counts = this.countsMap || {};
        const scored = list.map(c => ({ id: c.id, label: `${c.code||''} ${c.name||''}`.trim(), score: counts[c.code] || 0 }));
        scored.sort((a,b)=> b.score - a.score);
        return scored.filter(x => x.score > 0).slice(0, 6);
      },
      selectedUnmatchedCategoryLabel() {
        if (!this.selectedUnmatchedCategory) return 'All';
        const c = (this.categories||[]).find(x => x.id === this.selectedUnmatchedCategory);
        return c ? `${c.code||''} ${c.name||''}`.trim() : this.selectedUnmatchedCategory;
      },
      coverageVisibleCategories() {
        const all = (this.categories || []).slice();
        const byParent = {};
        all.forEach(c => {
          const pid = c.parentId || '';
          if (!byParent[pid]) byParent[pid] = [];
          byParent[pid].push(c);
        });
        Object.keys(byParent).forEach(pid => {
          byParent[pid].sort((a,b) => {
            if ((a.sortNo||0) !== (b.sortNo||0)) return (a.sortNo||0) - (b.sortNo||0);
            return (a.code||'').localeCompare(b.code||'');
          });
        });
        const roots = (byParent[''] || all.filter(c => !c.parentId)).sort((a,b)=>{
          if ((a.sortNo||0) !== (b.sortNo||0)) return (a.sortNo||0) - (b.sortNo||0);
          return (a.code||'').localeCompare(b.code||'');
        });
        const out = [];
        const pushNode = (node) => {
          out.push(node);
          const seen = {};
          const children = [].concat(byParent[node.id] || [], byParent[node.code] || []).filter(ch=>{
            const k = String(ch.code || ch.id || '');
            if (!k) return false;
            if (seen[k]) return false;
            seen[k] = true;
            return true;
          });
          if (this.coverageExpanded[node.id]) {
            children.forEach(ch => pushNode(ch));
          }
        };
        roots.forEach(r => pushNode(r));
        const q = (this.coverageCategoryQuery || '').trim().toLowerCase();
        if (!q) return out;
        return out.filter(c => (c.name||'').toLowerCase().includes(q) || (c.code||'').toLowerCase().includes(q));
      },
      isAllUnmatchedSelected() {
        const rows = this.unmatchedDetailRows || [];
        if (!rows.length) return false;
        return rows.every(r => this.unmatchedDetailSelection.includes(r.id));
      },
      batchAssignCategoryName() {
        if (!this.batchAssignCategoryId) return '';
        const c = (this.categories || []).find(x => (x.code || x.id) === this.batchAssignCategoryId);
        return c ? `${c.name} (${c.code})` : this.batchAssignCategoryId;
      }
    },
    methods: {
      toggleUnmatchedDetailSelection(id) {
        const idx = this.unmatchedDetailSelection.indexOf(id);
        if (idx >= 0) this.unmatchedDetailSelection.splice(idx, 1);
        else this.unmatchedDetailSelection.push(id);
      },
      toggleAllUnmatchedDetails() {
        if (this.isAllUnmatchedSelected) {
          this.unmatchedDetailSelection = [];
        } else {
          this.unmatchedDetailSelection = (this.unmatchedDetailRows||[]).map(x=>x.id);
        }
      },
      openBatchAssignModal() {
        if (!this.unmatchedDetailSelection.length) return;
        this.batchAssignCategoryId = '';
        this.batchAssignModalVisible = true;
      },
      closeBatchAssignModal() {
        this.batchAssignModalVisible = false;
        this.batchAssignCategoryId = '';
      },
      batchAssignPickCategory(c) {
        if (!c) return;
        this.batchAssignCategoryId = c.id;
        this.updateRecentCategories(c.id);
      },
      async submitBatchAssign() {
        if (!this.batchAssignCategoryId) {
          this.showToast('Please select a category', 'error');
          return;
        }
        const payload = {
          categoryId: this.batchAssignCategoryId,
          transactionIds: this.unmatchedDetailSelection,
          description: this.unmatchedDetailDesc
        };
        try {
          const r = await fetch('/api/rule/batch-assign', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
          });
          if (r.ok) {
            const d = await r.json();
            this.showToast(`Updated ${d.updated} transactions. Rule ${d.ruleCreated?'created':'updated'}.`, 'success');
            this.closeBatchAssignModal();
            this.unmatchedDetailSelection = [];
            // Refresh list
            this.fetchUnmatchedDetails(this.unmatchedDetailDesc, true); 
          } else {
            this.showToast('Batch assign failed', 'error');
          }
        } catch(e) {
          this.showToast('Error: '+e.message, 'error');
        }
      },
      async runFullAnalysis() {
        await this.calculateCoverage();
        await this.fetchUnmatchedTops();
      },
      switchTab(t) {
        this.tab = t;
        if (t === 'dashboard') {
          this.loadDashboard();
        } else if (t === 'rules') {
          this.fetchCategories();
        } else if (t === 'coverage') {
          this.fetchCategories().then(async ()=>{
            await this.fetchCategoryRuleCounts();
            this.coverageCategoryQuery = '';
            this.coverageCatOpen = false;
            this.coverageCatHoverIdx = 0;
            this.coveragePickerOpen = false;
          });
          this.unmatchedRows = [];
          this.unmatchedLoading = false;
          this.fetchUnmatchedDimensions();
          this.loadUnmatchedSettings();
        } else if (t === 'assistant') {
          // nothing extra
        } else if (t === 'model') {
          this.fetchModelMetrics();
        } else if (t === 'lifestyle') {
          if (!this.lifestyleResult) {
            this.fetchLifestyleAnalysis();
          }
        }
      },
      async fetchLifestyleAnalysis() {
        this.lifestyleLoading = true;
        try {
          const r = await fetch('/api/dashboard/lifestyle', { method: 'POST' });
          if (r.ok) {
            this.lifestyleResult = await r.json();
          } else {
            this.showToast('Failed to load lifestyle analysis', 'error');
          }
        } catch(e) {
          this.showToast('Error loading lifestyle analysis', 'error');
        } finally {
          this.lifestyleLoading = false;
        }
      },
      async fetchUnmatchedDimensions() {
        try {
          const r = await fetch('/api/dashboard/unmatched-dimensions', { method:'POST' });
          if (r.ok) {
            const d = await r.json();
            this.unmatchedBankOptions = Array.isArray(d.banks) ? d.banks : [];
            this.unmatchedCardTypeOptions = Array.isArray(d.cardTypes) ? d.cardTypes : [];
            if (d.dateMin) this.unmatchedStartDate = d.dateMin;
            if (d.dateMax) this.unmatchedEndDate = d.dateMax;
          }
        } catch(e) {}
      },
      coverageCategoryOptions() {
        const rows = (this.categories || []).slice().sort((a,b)=>{
          if ((a.sortNo||0) !== (b.sortNo||0)) return (a.sortNo||0) - (b.sortNo||0);
          return (a.code||'').localeCompare(b.code||'');
        });
        return rows.map(c => ({ id: c.id, label: `${c.code || ''} ${c.name || ''}`.trim() }));
      },
      filteredCoverageCategoryOptions() {
        const q = (this.coverageCategoryQuery || '').trim().toLowerCase();
        const opts = this.coverageCategoryOptions;
        if (!q) {
          const rec = this.coverageRecommendedCategories || [];
          if (rec.length) return rec;
          return opts.slice(0, 20);
        }
        return opts.filter(o => o.label.toLowerCase().includes(q));
      },
      onCoverageCategoryQueryKeydown(e) {
        const list = this.filteredCoverageCategoryOptions || [];
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.coverageCatOpen = true;
          this.coverageCatHoverIdx = Math.min(list.length - 1, (this.coverageCatHoverIdx || 0) + 1);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          this.coverageCatOpen = true;
          this.coverageCatHoverIdx = Math.max(0, (this.coverageCatHoverIdx || 0) - 1);
        } else if (e.key === 'Enter') {
          e.preventDefault();
          const opt = list[this.coverageCatHoverIdx || 0] || list[0];
          if (opt) this.pickCoverageCategory(opt);
        } else if (e.key === 'Escape') {
          this.coverageCatOpen = false;
        }
      },
      coverageHasChildren(c) {
        if (!c || !c.id) return false;
        return (this.categories || []).some(x => x.parentId === c.id || x.parentId === c.code);
      },
      coverageIsExpanded(c) {
        return !!this.coverageExpanded[c.id];
      },
      coverageToggleExpand(c) {
        if (!this.coverageHasChildren(c)) return;
        const cur = !!this.coverageExpanded[c.id];
        this.coverageExpanded[c.id] = !cur;
      },
      coverageSelectAll() {
        this.selectedUnmatchedCategory = '';
        this.coverageCategoryQuery = '';
        this.coverageCatOpen = false;
        this.coveragePickerOpen = false;
      },
      coveragePickCategory(c) {
        if (!c) return;
        this.selectedUnmatchedCategory = c.id;
        const label = `${c.code||''} ${c.name||''}`.trim();
        this.coverageCategoryQuery = label;
        this.coverageCatOpen = false;
        this.coveragePickerOpen = false;
        this.updateRecentCategories(c.id);
      },
      pickCoverageCategory(opt) {
        if (!opt) return;
        this.selectedUnmatchedCategory = opt.id;
        this.coverageCategoryQuery = opt.label;
        this.coverageCatOpen = false;
        this.updateRecentCategories(opt.id);
      },
      async recommendForUnmatched(row) {
        if (!row || !row.desc) return;
        row._loading = true;
        try {
          const r = await fetch('/api/rule/recommend', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ desc: row.desc }) });
          if (r.ok) {
            const d = await r.json();
            const rec = d.recommendation || {};
            if (!rec.categoryId && this.selectedUnmatchedCategory) rec.categoryId = this.selectedUnmatchedCategory;
            row._reco = rec;
            row._cands = Array.isArray(d.candidates) ? d.candidates : [];
          }
        } catch(e) {} finally {
          row._loading = false;
        }
      },
      async openRecommendation(row) {
        if (!row || !row.desc) return;
        await this.recommendForUnmatched(row);
        const rec = row._reco || {};
        this.recommendModalVisible = true;
        this.recommendRow = row;
        this.recommendCategoryId = rec.categoryId || this.selectedUnmatchedCategory || '';
        this.modalCategoryQuery = ''; // Reset tree search
        const kw = rec.pattern ? [rec.pattern] : [];
        const toks = Array.isArray(rec.tags) ? rec.tags : [];
        const allKw = Array.from(new Set([].concat(kw, toks))).filter(Boolean);
        this.recommendKeywords = allKw.join(', ');
        this.recommendTags = Array.isArray(rec.tags) ? rec.tags.join(', ') : row.desc || '';
        this.recommendPatternType = (rec.patternType || 'contains');
        this.recommendPriority = rec.priority != null ? rec.priority : (this.unmatchedDefaultPriority || 80);
      },
      closeRecommendationModal() {
        this.recommendModalVisible = false;
        this.recommendRow = null;
      },
      async confirmRecommendationSave() {
        const cid = this.recommendCategoryId || '';
        if (!cid) { this.showToast('请选择分类', 'error'); return; }
        const patterns = String(this.recommendKeywords || '').split(',').map(s=>s.trim()).filter(Boolean);
        if (!patterns.length) { this.showToast('请输入关键词', 'error'); return; }
        const tags = String(this.recommendTags || '').split(',').map(s=>s.trim()).filter(Boolean);
        const payload = {
          categoryId: cid,
          patterns,
          patternType: this.recommendPatternType || 'contains',
          priority: parseInt(this.recommendPriority || 80, 10),
          tags,
          active: 1
        };
        const resp = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (resp.ok) {
          this.showToast('已保存为规则', 'success');
          this.closeRecommendationModal();
          if (this.tab === 'rules' && this.selectedCategoryId === cid) {
            await this.fetchRules();
          }
        } else {
          this.showToast('保存失败', 'error');
        }
      },
      async fetchUnmatchedDetails(row) {
        if (!row || !row.desc) return;
        this.unmatchedDetailVisible = true;
        this.unmatchedDetailLoading = true;
        this.unmatchedDetailDesc = row.desc;
        this.unmatchedDetailRows = [];
        try {
          const payload = {
            description: row.desc,
            startDate: this.unmatchedStartDate || null,
            endDate: this.unmatchedEndDate || null,
            bank: this.unmatchedBank || null,
            cardType: this.unmatchedCardType || null,
            categoryId: this.selectedUnmatchedCategory || null
          };
          const r = await fetch('/api/rule/unmatched-details', { 
            method:'POST', 
            headers:{'Content-Type':'application/json'}, 
            body: JSON.stringify(payload) 
          });
          if (r.ok) {
            const d = await r.json();
            this.unmatchedDetailRows = Array.isArray(d.rows) ? d.rows : [];
          }
        } catch(e) {
          this.showToast('Failed to load details', 'error');
        } finally {
          this.unmatchedDetailLoading = false;
        }
      },
      closeUnmatchedDetails() {
        this.unmatchedDetailVisible = false;
        this.unmatchedDetailRows = [];
        this.unmatchedDetailDesc = '';
      },
      formatDate(ts) {
        if (!ts) return '-';
        try {
          const d = new Date(ts);
          if (isNaN(d.getTime())) return ts;
          return d.toISOString().slice(0, 10);
        } catch(e) { return ts; }
      },
      formatMoney(val) {
        if (val == null) return '-';
        return Number(val).toFixed(2);
      },
      openCreateRuleModal(row) {
        if (!row || !row.desc) return;
        this.createModalRow = row;
        this.createModalVisible = true;
        this.createModalPattern = row.desc || '';
        this.createModalPatternType = 'contains';
        this.createModalPriority = this.unmatchedDefaultPriority || 80;
        this.createModalTags = row.desc || '';
        this.createModalCategoryId = this.selectedUnmatchedCategory || '';
        this.recommendForUnmatched(row).then(()=>{
          const rec = (row && row._reco) || {};
          if (rec.categoryId) this.createModalCategoryId = rec.categoryId;
          if (rec.pattern) this.createModalPattern = rec.pattern;
          if (rec.patternType) this.createModalPatternType = rec.patternType;
          if (rec.priority != null) this.createModalPriority = rec.priority;
          if (Array.isArray(rec.tags) && rec.tags.length) {
            this.createModalTokens = rec.tags.slice();
            this.createModalTags = rec.tags.join(', ');
          }
          const cands = Array.isArray(row._cands) ? row._cands : [];
          if (!this.createModalCategoryId && cands.length) this.createModalCategoryId = cands[0].categoryId;
        });
      },
      openAddRuleModal() {
        this.createModalRow = null;
        this.createModalVisible = true;
        this.createModalFullscreen = false;
        this.createModalPattern = '';
        this.createModalPatternType = 'contains';
        this.createModalPriority = 100;
        this.createModalTags = '';
        this.createModalTokens = [];
        this.createModalCategoryId = this.selectedCategoryId || '';
        this.modalCategoryQuery = '';
      },
      toggleCreateModalFullscreen() {
        this.createModalFullscreen = !this.createModalFullscreen;
      },
      onModalKeydown(e) {
        if (!this.createModalVisible && !this.confirmVisible) return;
        if (e.key === 'Escape') {
          if (this.createModalVisible) this.closeCreateRuleModal();
          if (this.confirmVisible) this.onConfirmNo();
        } else if (e.key === 'Enter') {
          if (e.ctrlKey || e.metaKey) {
            if (this.createModalVisible) this.confirmCreateRuleNext();
          } else {
            if (this.createModalVisible) this.confirmCreateRule();
          }
        }
      },
      updateRecentCategories(cid) {
        if (!cid) return;
        const ids = this.recentCategoryIds.slice();
        const idx = ids.indexOf(cid);
        if (idx >= 0) ids.splice(idx, 1);
        ids.unshift(cid);
        this.recentCategoryIds = ids.slice(0, 6);
      },
      closeCreateRuleModal() {
        this.createModalVisible = false;
        this.createModalRow = null;
      },
      async confirmCreateRule() {
        const cid = this.createModalCategoryId || '';
        if (!cid) { this.showToast('请选择分类', 'error'); return; }
        const kwStr = (this.createModalTags || '').trim();
        if (!kwStr) { this.showToast('请输入关键词（Keywords）', 'error'); return; }
        const patterns = kwStr.split(',').map(s=>s.trim()).filter(Boolean);
        const tagStr = (this.createModalPattern || '').trim();
        const tags = tagStr ? tagStr.split(',').map(s=>s.trim()).filter(Boolean) : [];
        
        const doSave = async () => {
          const payload = {
            categoryId: cid,
            patterns,
            patternType: this.createModalPatternType || 'contains',
            priority: parseInt(this.createModalPriority || 80, 10),
            tags,
            active: 1
          };
          const r = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
          if (r.ok) {
            if (this.tab === 'rules' && this.selectedCategoryId === cid) {
              await this.fetchRules();
            }
            this.closeCreateRuleModal();
            this.showToast('Rule created', 'success');
          }
        };

        try {
          const rl = await fetch('/api/rule/list', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ categoryId: cid }) });
          let exists = [];
          if (rl.ok) {
            const d = await rl.json();
            const rules = Array.isArray(d.rows) ? d.rows : [];
            const existingSet = new Set(rules.map(x => (x.pattern||'').trim()));
            exists = patterns.filter(p => existingSet.has((p||'').trim()));
          }
          if (exists && exists.length) {
             const msg = `以下关键词已存在：${exists.join(', ')}\n仍要保存其他新关键词吗？`;
             this.showConfirm(msg, async () => {
               // 保存未重复的部分
               const unique = patterns.filter(p => !exists.includes(p));
               if (!unique.length) { this.showToast('全部关键词已存在，未保存', 'error'); return; }
               const payload = {
                 categoryId: cid,
                 patterns: unique,
                 patternType: this.createModalPatternType || 'contains',
                 priority: parseInt(this.createModalPriority || 80, 10),
                 tags,
                 active: 1
               };
               const r = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
               if (r.ok) {
                 if (this.tab === 'rules' && this.selectedCategoryId === cid) {
                   await this.fetchRules();
                 }
                 this.closeCreateRuleModal();
                 this.showToast('Rule created', 'success');
               }
             }, 'Duplicate Pattern');
             return;
          }
        } catch(e) {}
        
        await doSave();
      },
      chooseCandidate(c) {
        if (!c) return;
        this.createModalCategoryId = c.categoryId || this.createModalCategoryId;
        const sc = parseInt(c.score || 0, 10);
        const p = Math.min(100, Math.max(60, Math.round(sc / 2)));
        this.createModalPriority = p;
        this.updateRecentCategories(this.createModalCategoryId);
      },
      toggleKeywordChip(t) {
        const cur = (this.createModalTags || '').split(',').map(s=>s.trim()).filter(Boolean);
        const has = cur.includes(t);
        const next = has ? cur.filter(x => x !== t) : cur.concat([t]);
        this.createModalTags = next.join(', ');
      },
      modalHasChildren(c) {
        if (!c || !c.id) return false;
        return (this.categories || []).some(x => x.parentId === c.id || x.parentId === c.code);
      },
      modalIsExpanded(c) {
        return !!this.modalExpanded[c.id];
      },
      modalToggleExpand(c) {
        if (!this.modalHasChildren(c)) return;
        const cur = !!this.modalExpanded[c.id];
        this.modalExpanded[c.id] = !cur;
      },
      modalPickCategory(c) {
        if (!c) return;
        this.createModalCategoryId = c.code || c.id;
        this.updateRecentCategories(this.createModalCategoryId);
      },
      highlightText(text, query) {
        const t = (text || '');
        const q = (query || '').trim();
        if (!q) return this.escapeHtml(t);
        const lowerT = t.toLowerCase();
        const lowerQ = q.toLowerCase();
        let i = 0;
        let out = '';
        while (true) {
          const idx = lowerT.indexOf(lowerQ, i);
          if (idx === -1) {
            out += this.escapeHtml(t.slice(i));
            break;
          }
          out += this.escapeHtml(t.slice(i, idx));
          out += '<mark>' + this.escapeHtml(t.slice(idx, idx + q.length)) + '</mark>';
          i = idx + q.length;
        }
        return out;
      },
      escapeHtml(s) {
        return String(s)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;');
      },
      async confirmCreateRuleNext() {
        const cur = this.createModalRow;
        await this.confirmCreateRule();
        const list = this.filteredUnmatchedRows || [];
        const idx = list.findIndex(x => x === cur);
        const next = list[idx+1];
        if (next) this.openCreateRuleModal(next);
      },
      setPatternFromToken(t) {
        if (!t) return;
        this.createModalPattern = t;
      },
      async applyRecommendation(row) {
        if (!row || !row._reco) return;
        const rec = row._reco || {};
        const cid = rec.categoryId || this.selectedUnmatchedCategory;
        if (!cid) { this.showToast('请选择分类', 'error'); return; }
        const pLower = String((rec.pattern || row.desc) || '').trim().toLowerCase();
        const rawTags = Array.isArray(rec.tags) ? rec.tags : [row.desc];
        const tags = rawTags.filter(t => String(t || '').trim().toLowerCase() !== pLower);
        const payload = {
          categoryId: cid,
          pattern: rec.pattern || row.desc,
          patternType: rec.patternType || 'contains',
          priority: rec.priority != null ? rec.priority : (this.unmatchedDefaultPriority || 80),
          tags,
          active: 1
        };
        const resp = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (resp.ok) {
          if (this.tab === 'rules' && this.selectedCategoryId === cid) {
            await this.fetchRules();
          }
          this.showToast('已保存为规则', 'success');
        }
      },
      starString(p) {
        const n = p >= 90 ? 5 : p >= 70 ? 4 : p >= 50 ? 3 : p >= 30 ? 2 : 1;
        return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(n);
      },
      async calculateCoverage() {
        if (this.busyMode === 'chat') { try{ console.log('[FinMind] skip coverage during chat'); }catch(e){}; return; }
        this.coverageLoading = true;
        try {
            const r = await fetch('/api/dashboard/coverage', { method: 'POST' });
            if (r.ok) {
                this.coverageResult = await r.json();
            } else {
                this.showToast('Failed to calculate coverage', 'error');
            }
        } catch(e) {
            console.error(e);
            this.showToast('Error calculating coverage', 'error');
        } finally {
            this.coverageLoading = false;
        }
      },
      async fetchModelMetrics() {
        this.modelMetricsLoading = true;
        try {
          const r = await fetch('/api/dashboard/model-metrics', { method: 'POST' });
          if (r.ok) {
            this.modelMetrics = await r.json();
            try { this.modelMetricsLastUpdated = new Date().toLocaleString(); } catch(e) {}
          } else {
            this.showToast('Failed to load model metrics', 'error');
          }
        } catch(e) {
          this.showToast('Error loading model metrics', 'error');
        } finally {
          this.modelMetricsLoading = false;
        }
      },
      exportModelMetrics() {
        if (!this.modelMetrics) return;
        const data = JSON.stringify(this.modelMetrics, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'model_metrics.json';
        a.click();
        URL.revokeObjectURL(url);
      },
      retryLastChat() {
        if (this.chatLoading) return;
        if (this.chatStatus !== 'error') return;
        const lastUser = [...this.chatMessages].reverse().find(m => m.role === 'user');
        if (!lastUser || !lastUser.content) return;
        this.chatInput = lastUser.content;
        this.sendChatMessage();
      },
      clearChat() {
        if (this.chatLoading) return;
        this.chatMessages = [{ role: 'assistant', content: 'Hello! I am FinMind AI. How can I help you today?' }];
        this.chatStatus = 'idle';
        this.chatRespStatus = null;
        this.chatError = '';
        this.chatTimestamp = '';
      },
      copyMessage(i) {
        const msg = this.chatMessages[i];
        if (!msg || !msg.content) return;
        try {
          navigator.clipboard && navigator.clipboard.writeText(msg.content);
        } catch(e) {}
      },
      async sendChatMessage() {
        const text = (this.chatInput||'').trim();
        if (!text) return;
        try { console.log('[FinMind] sendChatMessage:', text); } catch(e){}
        this.busyMode = 'chat';
        this.chatTimestamp = new Date().toLocaleTimeString();
        this.chatMessages.push({ role: 'user', content: text });
        this.chatInput = '';
        this.chatLoading = true;
        this.chatStatus = 'sending';
        this.chatRespStatus = null;
        this.chatError = '';
        
        try {
          const r = await fetch('/api/agents/chat', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ query: text })
          });
          try { console.log('[FinMind] chat resp status:', r.status); } catch(e){}
          this.chatRespStatus = r.status;
          if (r.ok) {
            const d = await r.json();
            const msg = d.response || 'No response.';
            if (msg === 'OTHER' || /^Error/i.test(msg)) {
              this.chatMessages.push({ role: 'assistant', content: 'AI服务不可用或密钥无效，请检查 QWEN_API_KEY。' });
              this.chatStatus = 'error';
              this.chatError = 'LLM unavailable';
              try { console.warn('[FinMind] chat LLM unavailable, response=', msg); } catch(e){}
            } else {
              this.chatMessages.push({ role: 'assistant', content: msg });
              this.chatStatus = 'received';
              this.chatTimestamp = new Date().toLocaleTimeString();
            }
          } else {
            this.chatMessages.push({ role: 'assistant', content: 'Sorry, I encountered an error.' });
            this.chatStatus = 'error';
            this.chatError = 'HTTP ' + r.status;
          }
        } catch(e) {
          try { console.error('[FinMind] chat error:', e); } catch(_){}
          this.chatMessages.push({ role: 'assistant', content: 'Network error.' });
          this.chatStatus = 'error';
          this.chatError = 'Network error';
        } finally {
          this.chatLoading = false;
          this.busyMode = '';
          // scroll to bottom
          this.$nextTick(() => {
            const box = document.querySelector('.chat-box');
            if (box) box.scrollTop = box.scrollHeight;
          });
        }
      },
      async fetchUnmatchedTops() {
        this.unmatchedLoading = true;
        this.unmatchedSummary = null;
        this.unmatchedPage = 1;
        try {
          const r = await fetch('/api/dashboard/unmatched-tops', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({
            startDate: this.unmatchedStartDate || null,
            endDate: this.unmatchedEndDate || null,
            bank: this.unmatchedBank || null,
            cardType: this.unmatchedCardType || null,
            categoryId: this.selectedUnmatchedCategory || null
          }) });
          if (r.ok) {
            const d = await r.json();
            this.unmatchedRows = Array.isArray(d.rows) ? d.rows : [];
            this.unmatchedSummary = { total: d.total || 0, unmatched: d.unmatched || 0, elapsedMs: d.elapsedMs || 0 };
          } else {
            this.unmatchedRows = [];
          }
        } catch(e) {
          this.unmatchedRows = [];
        } finally {
          this.unmatchedLoading = false;
        }
      },
      setUnmatchedPage(p) {
        const tp = this.unmatchedTotalPages;
        const np = Math.min(Math.max(1, p), tp);
        this.unmatchedPage = np;
      },
      exportUnmatchedCSV() {
        const rows = this.filteredUnmatchedRows || [];
        const header = ['Desc','Count'];
        const lines = [header.join(',')].concat(rows.map(r => {
          const desc = String(r.desc||'').replace(/"/g,'""');
          const count = r.count || 0;
          return `"${desc}",${count}`;
        }));
        const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'unmatched_top_list.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      },
      async recommendPage() {
        if (this.unmatchedBulkLoading) return;
        const list = this.paginatedUnmatchedRows || [];
        if (!list.length) return;
        this.unmatchedBulkLoading = true;
        this.unmatchedBulkProgress = { action: 'recommend', done: 0, total: list.length };
        this.unmatchedAbortRequested = false;
        try {
          for (let row of list) {
            if (this.unmatchedAbortRequested) break;
            await this.recommendForUnmatched(row);
            this.unmatchedBulkProgress.done++;
          }
        } catch(e) {} finally {
          this.unmatchedBulkLoading = false;
          this.unmatchedAbortRequested = false;
          this.unmatchedBulkProgress = { action: '', done: 0, total: 0 };
        }
      },
      async recommendAll() {
        if (this.unmatchedBulkLoading) return;
        const list = this.filteredUnmatchedRows || [];
        if (!list.length) return;
        this.unmatchedBulkLoading = true;
        this.unmatchedBulkProgress = { action: 'recommend', done: 0, total: list.length };
        this.unmatchedAbortRequested = false;
        try {
          for (let row of list) {
            if (this.unmatchedAbortRequested) break;
            await this.recommendForUnmatched(row);
            this.unmatchedBulkProgress.done++;
          }
        } catch(e) {} finally {
          this.unmatchedBulkLoading = false;
          this.unmatchedAbortRequested = false;
          this.unmatchedBulkProgress = { action: '', done: 0, total: 0 };
        }
      },
      clearRecommendation(row) {
        if (!row) return;
        row._reco = null;
      },
      cancelBulk() {
        this.unmatchedAbortRequested = true;
      },
      saveUnmatchedSettings() {
        try {
          const obj = {
            startDate: this.unmatchedStartDate || '',
            endDate: this.unmatchedEndDate || '',
            bank: this.unmatchedBank || '',
            cardType: this.unmatchedCardType || '',
            topN: parseInt(this.unmatchedTopN || 50, 10),
            pageSize: parseInt(this.unmatchedPageSize || 10, 10),
            minCount: parseInt(this.unmatchedMinCount || 1, 10),
            ignore: this.unmatchedIgnoreKeywords || '',
            defaultPriority: parseInt(this.unmatchedDefaultPriority || 80, 10)
          };
          localStorage.setItem('fm_unmatched_settings', JSON.stringify(obj));
        } catch(e) {}
      },
      loadUnmatchedSettings() {
        try {
          const s = localStorage.getItem('fm_unmatched_settings');
          if (!s) return;
          const obj = JSON.parse(s);
          this.unmatchedStartDate = obj.startDate || this.unmatchedStartDate;
          this.unmatchedEndDate = obj.endDate || this.unmatchedEndDate;
          this.unmatchedBank = obj.bank || '';
          this.unmatchedCardType = obj.cardType || '';
          this.unmatchedTopN = obj.topN || this.unmatchedTopN;
          this.unmatchedPageSize = obj.pageSize || this.unmatchedPageSize;
          this.unmatchedMinCount = obj.minCount || this.unmatchedMinCount;
          this.unmatchedIgnoreKeywords = obj.ignore || this.unmatchedIgnoreKeywords;
          this.unmatchedDefaultPriority = obj.defaultPriority || this.unmatchedDefaultPriority;
        } catch(e) {}
      },
      async saveAllRecommendations() {
        if (this.unmatchedBulkLoading) return;
        const list = (this.unmatchedRows || []).filter(r => r && r._reco);
        if (!list.length) return;
        if (!window.confirm('确认保存全部推荐吗？')) return;
        this.unmatchedBulkLoading = true;
        this.unmatchedBulkProgress = { action: 'save', done: 0, total: list.length };
        this.unmatchedAbortRequested = false;
        try {
          for (let row of list) {
            if (this.unmatchedAbortRequested) break;
            await this.applyRecommendation(row);
            this.unmatchedBulkProgress.done++;
          }
          alert('全部推荐已保存');
        } catch(e) {} finally {
          this.unmatchedBulkLoading = false;
          this.unmatchedAbortRequested = false;
          this.unmatchedBulkProgress = { action: '', done: 0, total: 0 };
        }
      },
      setDatePreset(p) {
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth()+1).padStart(2,'0');
        const d = String(now.getDate()).padStart(2,'0');
        const today = `${y}-${m}-${d}`;
        if (p === '7d' || p === '30d' || p === '90d') {
          const days = p === '7d' ? 7 : (p === '30d' ? 30 : 90);
          const sd = new Date(now.getTime() - days*24*60*60*1000);
          const sy = sd.getFullYear();
          const sm = String(sd.getMonth()+1).padStart(2,'0');
          const sdv = String(sd.getDate()).padStart(2,'0');
          this.unmatchedStartDate = `${sy}-${sm}-${sdv}`;
          this.unmatchedEndDate = today;
        } else if (p === 'ytd') {
          const sy = y;
          this.unmatchedStartDate = `${sy}-01-01`;
          this.unmatchedEndDate = today;
        }
        this.saveUnmatchedSettings();
      },
      clearUnmatchedResults() {
        this.unmatchedRows = [];
        this.unmatchedSummary = null;
        this.unmatchedPage = 1;
      },
      resetUnmatchedFilters() {
        this.unmatchedFilter = '';
        this.unmatchedTopN = 50;
        this.unmatchedMinCount = 1;
        this.unmatchedIgnoreKeywords = '';
        this.unmatchedPageSize = 10;
        this.unmatchedBank = '';
        this.unmatchedCardType = '';
        this.saveUnmatchedSettings();
      },
      async createRuleFromUnmatched(row) {
        if (!row || !row.desc) return;
        if (!this.selectedUnmatchedCategory) { alert('请选择分类'); return; }
        const payload = { categoryId: this.selectedUnmatchedCategory, pattern: row.desc, patternType: 'contains', priority: 70, active: 1 };
        const r = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (r.ok) {
          alert('Rule created');
        }
      },
      async addTagFromUnmatched(row) {
        if (!row || !row.desc) return;
        if (!this.selectedUnmatchedCategory) { alert('请选择分类'); return; }
        if (!this.selectedRuleIdForTag) { alert('请输入要添加标签的规则ID'); return; }
        try {
          const rl = await fetch('/api/rule/list', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ categoryId:this.selectedUnmatchedCategory }) });
          if (!rl.ok) return;
          const d = await rl.json();
          const rules = Array.isArray(d.rows) ? d.rows : [];
          const obj = rules.find(x => x.id === this.selectedRuleIdForTag);
          if (!obj) { alert('Rule not found in selected category'); return; }
          const tags = Array.isArray(obj.tags) ? obj.tags.slice() : [];
          if (!tags.includes(row.desc)) tags.push(row.desc);
          const payload = Object.assign({}, obj, { tags, categoryId: this.selectedUnmatchedCategory });
          const resp = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
          if (resp.ok) {
            alert('Tag added');
          }
        } catch(e) {}
      },
      async classify() {
        this.result = null;
        const r = await fetch('/api/classify', {
          method: 'POST',
          headers: { 'Content-Type':'application/json' },
          body: JSON.stringify({ description: this.form.description, money: this.form.money })
        });
        if (r.ok) this.result = await r.json();
      },
      loadSample() {
        this.sampleLines = [
          ["", "", "", "38.00", "", "", "Starbucks purchase"],
          ["", "", "", "65.00", "", "", "Dinner - restaurant"],
          ["", "", "", "120.00", "", "", "Groceries - supermarket"]
        ];
      },
      async computeInsights() {
        this.insights = null;
        const r = await fetch('/api/insights', {
          method: 'POST',
          headers: { 'Content-Type':'application/json' },
          body: JSON.stringify({ lines: this.sampleLines })
        });
        if (r.ok) this.insights = await r.json();
      },
      async loadDashboard() {
        if (!this.sampleLines.length) this.loadSample();
        await this.computeInsights();
        if (!this.insights) return;
        this.distribution = (this.insights.distribution || []).slice(0, 7);
        let acc = 0;
        const segs = this.distribution.map((row, i) => {
          const p = (row.ratio || 0) * 100;
          const start = acc;
          acc += p;
          return `${this.palette[i % this.palette.length]} ${start}% ${acc}%`;
        });
        this.donutStyle = `conic-gradient(${segs.join(',')})`;
        const maxRatio = Math.max.apply(null, this.distribution.map(x => x.ratio || 0).concat([0]));
        this.health.spendControl = Math.max(0, 100 - maxRatio * 100);
        const idx = this.distribution.findIndex(x => /invest|投资|储蓄/i.test(x.type || ''));
        const saveRatio = idx >= 0 ? (this.distribution[idx].ratio || 0) * 100 : Math.min(20, (this.distribution.length * 2));
        this.health.savingsRate = saveRatio;
        const score = 0.6 * this.health.spendControl + 0.4 * this.health.savingsRate;
        this.health.score = Math.max(0, Math.min(100, Math.round(score)));
      },
      async fetchCategories() {
        const r = await fetch('/api/rule/categories', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ txn_types:this.selectedTxnType || 'expense' }) });
        if (r.ok) {
          const d = await r.json();
          this.categories = d.rows || [];
          // expand all root nodes (no parentId or level===0/1)
          this.expandedIds = {};
          this.selectedCategoryId = '';
          this.selectedCategoryCode = '';
          this.selectedCategoryName = '';
          await this.fetchCategoryRuleCounts();
          this.restoreState();
          if (!this.selectedCategoryId && this.categoryOptions.length) {
            this.onCategorySelect(this.categoryOptions[0].id);
          }
          this.updateCategoryQueryLabel();
          this.catOpen = false;
          this.catHoverIdx = 0;
        }
      },
      onCategorySelect() {
        const id = this.selectedCategoryId;
        if (!id) return;
        this.selectCategory(id);
        this.updateCategoryQueryLabel();
        this.catOpen = false;
      },
      updateCategoryQueryLabel() {
        this.categoryQuery = '';
      },
      pickCategory(opt) {
        if (!opt) return;
        this.selectedCategoryId = opt.id;
        this.onCategorySelect();
      },
      onCategoryQueryKeydown(e) {
        const list = this.filteredCategoryOptions || [];
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.catOpen = true;
          this.catHoverIdx = Math.min(list.length - 1, (this.catHoverIdx || 0) + 1);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          this.catOpen = true;
          this.catHoverIdx = Math.max(0, (this.catHoverIdx || 0) - 1);
        } else if (e.key === 'Enter') {
          e.preventDefault();
          const opt = list[this.catHoverIdx || 0] || list[0];
          if (opt) this.pickCategory(opt);
        } else if (e.key === 'Escape') {
          this.catOpen = false;
        } else {
          this.catOpen = true;
          this.catHoverIdx = 0;
        }
      },
      async fetchCategoryRuleCounts() {
        const codes = (this.categories||[]).map(c => c.code).filter(Boolean);
        if (!codes.length) { this.countsMap = {}; return; }
        const r = await fetch('/api/rule/counts', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ codes }) });
        if (r.ok) {
          const d = await r.json();
          this.countsMap = d.counts || {};
        } else {
          this.countsMap = {};
        }
      },
      countFor(c) {
        const code = c && c.code;
        return (this.countsMap && code) ? (this.countsMap[code] || 0) : 0;
      },
      saveState() {
        try {
          const state = {
            expandedIds: this.expandedIds,
            selectedCategoryId: this.selectedCategoryId,
            selectedTxnType: this.selectedTxnType
          };
          localStorage.setItem('fm_rules_state', JSON.stringify(state));
        } catch(e) {}
      },
      restoreState() {
        try {
          const s = localStorage.getItem('fm_rules_state');
          if (!s) return;
          const st = JSON.parse(s);
          this.selectedTxnType = 'all';
          this.expandedIds = st.expandedIds || {};
          this.selectedCategoryId = st.selectedCategoryId || '';
          if (this.selectedCategoryId) {
            const c = (this.categories||[]).find(x => x.id === this.selectedCategoryId);
            this.selectedCategoryCode = c ? c.code : '';
            this.selectedCategoryName = c ? c.name : '';
            this.expandPathTo(this.selectedCategoryId);
            this.fetchRules();
          }
        } catch(e) {}
      },
      expandPathTo(id) {
        const map = {};
        (this.categories||[]).forEach(c => { map[c.id] = c.parentId; });
        let cur = id;
        while (cur) {
          const pid = map[cur];
          if (pid) this.expandedIds[pid] = true;
          cur = pid;
        }
      },
      async changeTxnType(type) {
        this.selectedTxnType = type || 'all';
        this.selectedCategoryId = '';
        this.selectedCategoryCode = '';
        this.selectedCategoryName = '';
        await this.fetchCategories();
      },
      hasChildren(c) {
        if (!c || !c.id) return false;
        return (this.categories || []).some(x => x.parentId === c.id || x.parentId === c.code);
      },
      isExpanded(c) {
        return !!this.expandedIds[c.id];
      },
      toggleExpand(c) {
        if (!this.hasChildren(c)) return;
        const cur = !!this.expandedIds[c.id];
        this.expandedIds[c.id] = !cur;
        this.saveState();
      },
      expandAll() {
        const ids = {};
        (this.categories || []).forEach(c => { ids[c.id] = true; });
        this.expandedIds = ids;
      },
      collapseAll() {
        this.expandedIds = {};
      },
      navigateCrumb(b) {
        if (!b || !b.id) return;
        this.selectCategory(b.id);
      },
      onTreeItemClick(c, evt) {
        if (this.hasChildren(c)) {
          this.toggleExpand(c);
          return;
        }
        this.selectCategory(c.id);
      },
      selectCategory(id) {
        const c = (this.categories || []).find(x => x.id === id);
        if (c && this.hasChildren(c)) {
          this.expandedIds[c.id] = true;
          const findLeaf = (nodeId) => {
            const children = (this.categories||[]).filter(x => x.parentId === nodeId || x.parentId === c.code).sort((a,b)=>a.sortNo-b.sortNo);
            for (let child of children) {
              if (this.hasChildren(child)) {
                const leaf = findLeaf(child.id);
                if (leaf) return leaf;
              } else {
                return child;
              }
            }
            return c;
          };
          const leaf = findLeaf(c.id);
          id = leaf ? leaf.id : id;
        }
        this.selectedCategoryId = id;
        this.selectedCategoryCode = c ? c.code : '';
        this.selectedCategoryName = c ? c.name : '';
        this.ruleFilter = '';
        this.activeOnly = false;
        this.saveState();
        this.fetchRules();
      },
      async fetchRules() {
        if (this.busyMode === 'chat') { try{ console.log('[FinMind] skip rule/list during chat'); }catch(e){}; return; }
        if (!this.selectedCategoryId) return;
        this.rulesLoading = true;
        this.errorMsg = '';
        try {
          const r = await fetch('/api/rule/list', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ categoryId:this.selectedCategoryId }) });
          if (r.ok) {
            const d = await r.json();
            this.rules = Array.isArray(d.rows) ? d.rows : [];
          } else {
            this.errorMsg = 'Failed to load rules';
            this.rules = [];
          }
        } catch(e) {
          this.errorMsg = 'Network error';
          this.rules = [];
        } finally {
          this.rulesLoading = false;
        }
      },
      editRule(r) {
        const tagsStr = Array.isArray(r.tags) ? r.tags.join(', ') : '';
        this.ruleForm = Object.assign({}, r, { tags: tagsStr });
      },
      resetRuleForm() {
        this.ruleForm = { pattern:'', patternType:'contains', priority:100, active:1, remark:'', minAmount:null, maxAmount:null, startDate:null, endDate:null, tags:'', bankCode:'', cardTypeCode:'' };
      },
      async saveRuleDetail() {
        if (!this.selectedCategoryId) { this.showToast('Please select a category first', 'error'); return; }
        const tags = typeof this.ruleForm.tags === 'string' 
          ? this.ruleForm.tags.split(',').map(s=>s.trim()).filter(Boolean) 
          : (Array.isArray(this.ruleForm.tags) ? this.ruleForm.tags : []);
        
        const payload = Object.assign({}, this.ruleForm, { 
          categoryId: this.selectedCategoryId, 
          tags: tags 
        });
        
        try {
            const r = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
            if (r.ok) {
              await this.fetchRules();
              this.showToast('Rule saved', 'success');
            } else {
                this.showToast('Failed to save rule', 'error');
            }
        } catch(e) {
            this.showToast('Error saving rule', 'error');
        }
      },
      async toggleRuleActive(r) {
        if (!r || !r.id) return;
        const payload = Object.assign({}, r, { active: r.active ? 0 : 1, categoryId: this.selectedCategoryId });
        const resp = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (resp.ok) {
          await this.fetchRules();
        }
      },
      async setRuleWeight(r, p) {
        if (!r || !r.id) return;
        const payload = Object.assign({}, r, { priority: p, categoryId: this.selectedCategoryId });
        const resp = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (resp.ok) await this.fetchRules();
      },
      toggleActiveOnly() {
        this.activeOnly = !this.activeOnly;
      },
      toggleFormActive() {
        if (!this.ruleForm) return;
        const v = this.ruleForm.active;
        this.ruleForm.active = v ? 0 : 1;
      },
      async deleteRule(r) {
        const target = (r && r.id) ? r : this.ruleForm;
        if (!target || !target.id) return;
        const pat = String(target.pattern || '').trim();
        const typ = String(target.patternType || 'contains');
        const cat = String(target.categoryId || this.selectedCategoryCode || '').trim();
        const tags = Array.isArray(target.tags) ? target.tags.join(', ') : '';
        const msg = [
          '确定要删除以下规则？',
          '',
          `Pattern：${pat || '(空)'}`,
          `Type：${typ}`,
          `Category：${cat || '(未选择)'}`,
          tags ? `Tags：${tags}` : ''
        ].filter(Boolean).join('\n');
        this.showConfirm(msg, async () => {
          const resp = await fetch('/api/rule/delete', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id:target.id }) });
          if (resp.ok) {
            await this.fetchRules();
            if (this.ruleForm.id === target.id) {
              this.resetRuleForm();
            }
            this.showToast('Rule deleted', 'success');
          } else {
            this.showToast('Failed to delete rule', 'error');
          }
        }, '删除规则');
      },
      async quickAddRule() {
        if (!this.selectedCategoryId || !this.newRule.pattern) return;
        const payload = Object.assign({}, this.newRule, { categoryId: this.selectedCategoryId, active:1 });
        const r = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (r.ok) {
          this.newRule.pattern = '';
          await this.fetchRules();
        }
      },
      toggleSelect(r) {
        if (!r || !r.id) return;
        const cur = !!this.selectedRuleIds[r.id];
        this.selectedRuleIds[r.id] = !cur;
      },
      toggleSelectAll() {
        const target = !this.selectAllChecked;
        this.selectAllChecked = target;
        (this.visibleRules||[]).forEach(r => { this.selectedRuleIds[r.id] = target; });
      },
      async bulkActivate(val) {
        const ids = Object.keys(this.selectedRuleIds).filter(id => this.selectedRuleIds[id]);
        if (!ids.length) return;
        for (let r of (this.rules||[])) {
          if (ids.includes(r.id)) await this.toggleRuleActive(r);
        }
        this.selectAllChecked = false;
        this.selectedRuleIds = {};
      },
      async bulkSetWeight() {
        const ids = Object.keys(this.selectedRuleIds).filter(id => this.selectedRuleIds[id]);
        if (!ids.length) return;
        for (let r of (this.rules||[])) {
          if (ids.includes(r.id)) await this.setRuleWeight(r, this.bulkWeight);
        }
        this.selectAllChecked = false;
        this.selectedRuleIds = {};
      },
      cycleWeight(r) {
        const thresholds = [30,50,70,90,100];
        const cur = r.priority || 100;
        let idx = thresholds.findIndex(x => x > cur);
        if (idx < 0) idx = 0;
        const next = thresholds[idx];
        this.setRuleWeight(r, next);
      },
      showToast(msg, kind='info') {
        this.toastMessage = msg;
        this.toastKind = kind;
        if (this.toastTimer) clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => {
          this.toastMessage = '';
        }, 3000);
      },
      showConfirm(msg, cb, title='Confirm') {
        this.confirmMessage = msg;
        this.confirmCallback = cb;
        this.confirmTitle = title;
        this.confirmVisible = true;
      },
      onConfirmYes() {
        if (this.confirmCallback) this.confirmCallback();
        this.confirmVisible = false;
        this.confirmCallback = null;
      },
      onConfirmNo() {
        this.confirmVisible = false;
        this.confirmCallback = null;
      },
      async fetchUnmatchedDetails(row) {
        if (!row || !row.desc) return;
        this.unmatchedDetailVisible = true;
        this.unmatchedDetailLoading = true;
        this.unmatchedDetailDesc = row.desc;
        this.unmatchedDetailRows = [];
        try {
          const payload = {
             description: row.desc,
             startDate: this.unmatchedStartDate || null,
             endDate: this.unmatchedEndDate || null,
             bank: this.unmatchedBank || null,
             cardType: this.unmatchedCardType || null,
             categoryId: this.selectedUnmatchedCategory || null
          };
          const r = await fetch('/api/rule/unmatched-details', { 
            method:'POST', 
            headers:{'Content-Type':'application/json'}, 
            body: JSON.stringify(payload) 
          });
          if (r.ok) {
             const d = await r.json();
             this.unmatchedDetailRows = Array.isArray(d.rows) ? d.rows : [];
          }
        } catch(e) {
          this.showToast('Failed to load details', 'error');
        } finally {
          this.unmatchedDetailLoading = false;
        }
      },
      closeUnmatchedDetails() {
        this.unmatchedDetailVisible = false;
        this.unmatchedDetailRows = [];
        this.unmatchedDetailDesc = '';
      },
      formatDate(ts) {
        if (!ts) return '-';
        try {
          // Handle ISO string or timestamp
          const d = new Date(ts);
          if (isNaN(d.getTime())) return ts;
          return d.toISOString().slice(0, 10);
        } catch(e) { return ts; }
      },
      formatMoney(val) {
        if (val == null) return '-';
        return Number(val).toFixed(2);
      }
    },
    mounted() {
      this.switchTab(this.tab);
    }
  };
  const vm = createApp(appDef).mount('#app');
  try {
    window.__fm_app = vm;
    window.switchTab = function(t){ try{ window.__fm_app && window.__fm_app.switchTab && window.__fm_app.switchTab(t); }catch(e){} };
  } catch(e) {}
})(); 
