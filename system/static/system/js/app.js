/* FinMind main app */
(function(){
  const { createApp } = window.Vue;
  createApp({
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
        expandedIds: {}
      };
    },
    created() {
      this.categoryQuery = '';
      this.catOpen = false;
      this.catHoverIdx = 0;
    },
    computed: {
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
            if (seen[ch.id]) return false;
            seen[ch.id] = true;
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
      }
    },
    methods: {
      starString(p) {
        const n = p >= 90 ? 5 : p >= 70 ? 4 : p >= 50 ? 3 : p >= 30 ? 2 : 1;
        return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(n);
      },
      async calculateCoverage() {
        this.coverageLoading = true;
        try {
            const r = await fetch('/api/dashboard/coverage', { method: 'POST' });
            if (r.ok) {
                this.coverageResult = await r.json();
            } else {
                alert('Failed to calculate coverage');
            }
        } catch(e) {
            console.error(e);
            alert('Error calculating coverage');
        } finally {
            this.coverageLoading = false;
        }
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
        const arr = Array.isArray(r.tags) ? r.tags.slice() : [];
        this.ruleForm = Object.assign({ tagsArr: arr, tagInput:'' }, r);
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
      async saveRule() {
        if (!this.ruleForm) return;
        const payload = Object.assign({}, this.ruleForm, { categoryId: this.selectedCategoryId, tags: (this.ruleForm.tagsArr||[]) });
        const r = await fetch('/api/rule/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (r.ok) {
          await this.fetchRules();
        }
      },
      addTag() {
        const t = (this.ruleForm.tagInput || '').trim();
        if (!t) return;
        this.ruleForm.tagsArr = this.ruleForm.tagsArr || [];
        if (!this.ruleForm.tagsArr.includes(t)) this.ruleForm.tagsArr.push(t);
        this.ruleForm.tagInput = '';
      },
      removeTag(t) {
        if (!this.ruleForm || !this.ruleForm.tagsArr) return;
        this.ruleForm.tagsArr = this.ruleForm.tagsArr.filter(x => x !== t);
      },
      async deleteRule(r) {
        if (!r || !r.id) return;
        const ok = confirm('Delete this rule?');
        if (!ok) return;
        const resp = await fetch('/api/rule/delete', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id:r.id }) });
        if (resp.ok) {
          await this.fetchRules();
        }
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
      }
    },
    mounted() {
      this.loadDashboard();
      this.fetchCategories();
    }
  }).mount('#app');
})(); 
