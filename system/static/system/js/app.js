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
        health: { score: 0, spendControl: 0, savingsRate: 0 }
      };
    },
    methods: {
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
      }
    },
    mounted() {
      this.loadDashboard();
    }
  }).mount('#app');
})(); 
