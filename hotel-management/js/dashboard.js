// Admin dashboard: charts + smooth UI behaviors
(function () {
  // Chart.js
  var chartEls = {
    revenue: document.getElementById('monthlyRevenueChart'),
    occupancy: document.getElementById('roomOccupancyChart'),
    growth: document.getElementById('customerGrowthChart'),
  };

  function baseLabel(n) {
    var d = new Date();
    d.setMonth(d.getMonth() - (n));
    return d.toLocaleString('default', { month: 'short' });
  }

  function buildLineChart(el) {
    if (!el || !window.Chart) return;
    var ctx = el.getContext('2d');

    var labels = [baseLabel(5), baseLabel(4), baseLabel(3), baseLabel(2), baseLabel(1), 'Now'];
    var data = [180000, 210000, 195000, 260000, 240000, 310000];

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Monthly Revenue',
          data: data,
          borderColor: 'rgba(212,175,55,0.95)',
          backgroundColor: 'rgba(212,175,55,0.18)',
          tension: 0.35,
          fill: true,
          pointRadius: 3,
          pointHoverRadius: 5
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                var val = context.parsed.y || 0;
                return ' ₹' + val.toLocaleString('en-IN');
              }
            }
          }
        },
        scales: {
          y: { ticks: { color: 'rgba(255,255,255,.75)' }, grid: { color: 'rgba(255,255,255,.08)' } },
          x: { ticks: { color: 'rgba(255,255,255,.75)' }, grid: { color: 'rgba(255,255,255,.08)' } },
        }
      }
    });
  }

  function buildDoughnutChart(el) {
    if (!el || !window.Chart) return;
    var ctx = el.getContext('2d');

    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Available', 'Occupied'],
        datasets: [{
          data: [38, 62],
          backgroundColor: ['rgba(255,255,255,.14)', 'rgba(212,175,55,0.95)'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { color: 'rgba(255,255,255,.75)' } },
          tooltip: { enabled: true }
        }
      }
    });
  }

  function buildBarChart(el) {
    if (!el || !window.Chart) return;
    var ctx = el.getContext('2d');

    var labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    var data = [1200, 1380, 1260, 1600, 1710, 1900];

    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Customer Growth',
          data: data,
          backgroundColor: 'rgba(212,175,55,0.85)',
          borderRadius: 10,
          barThickness: 14
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                var val = context.parsed.y || 0;
                return ' ' + val.toLocaleString('en-IN') + ' customers';
              }
            }
          }
        },
        scales: {
          y: { ticks: { color: 'rgba(255,255,255,.75)' }, grid: { color: 'rgba(255,255,255,.08)' } },
          x: { ticks: { color: 'rgba(255,255,255,.75)' }, grid: { color: 'rgba(255,255,255,.08)' } },
        }
      }
    });
  }

  buildLineChart(chartEls.revenue);
  buildDoughnutChart(chartEls.occupancy);
  buildBarChart(chartEls.growth);
})();

