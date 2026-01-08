document.addEventListener("DOMContentLoaded", () => {
  const mobileCtx = document.getElementById("mobileChart").getContext("2d");
  const regionCtx = document.getElementById("regionChart").getContext("2d");
  const productCtx = document.getElementById("topProductsChart").getContext("2d");
  const lineCtx = document.getElementById("lineChart").getContext("2d");

  let mobileChart, regionChart, productChart, lineChart;

  // pause updates while user is interacting
  let isHovering = false;
  [mobileCtx.canvas, regionCtx.canvas, productCtx.canvas, lineCtx.canvas].forEach(c => {
    c.style.pointerEvents = "auto"; // ensure canvas accepts pointer events
    c.addEventListener("mouseenter", () => { isHovering = true; });
    c.addEventListener("mouseleave", () => { isHovering = false; });
  });

  async function fetchData() {
    if (isHovering) return; // don't update while user is interacting (prevents stuck tooltips)

    try {
      const res = await fetch("/data");
      const data = await res.json();

      const mobileLabels = Object.keys(data.mobile_sales || {});
      const mobileValues = Object.values(data.mobile_sales || {});

      const regionLabels = Object.keys(data.region_sales || {});
      const regionValues = Object.values(data.region_sales || {}).map(r => r.total_revenue ?? 0);

      const productLabels = Object.keys(data.top_selling_products || {});
      const productValues = Object.values(data.top_selling_products || {});

      const weekLabels = data.weekly_region_sales?.times || [];
      const weeklyData = data.weekly_region_sales?.sales || {};

      const COLORS = ['#4F46E5','#10B981','#F59E0B','#EF4444','#3B82F6'];

      const lineDatasets = Object.keys(weeklyData).map((region, index) => ({
        label: region,
        data: weeklyData[region],
        borderWidth: 2,
        fill: false,
        borderColor: COLORS[index % COLORS.length],
        tension: 0.3,
        pointRadius: 2
      }));

      const smallFontOptions = {
        plugins: {
          legend: {
            labels: { color: "#fff", font: { size: 10 } }
          },
          title: {
            display: true,
            color: "#38bdf8",
            font: { size: 16 }
          },
          tooltip: {
            enabled: true,
            mode: "index",
            intersect: false,
            // avoid sticky tooltips when moving between points
            position: "nearest",
          }
        },
        interaction: {
          mode: "nearest", // nearest or index depending on desired behaviour
          intersect: false
        },
        hover: {
          mode: "nearest",
          intersect: false
        },
        animation: {
          duration: 0 // turn off animation so updates don't disrupt hover state
        }
      };

      const tickFont = { size: 10 };

      // --- Mobile Chart (create once, update in-place) ---
      if (!mobileChart) {
        mobileChart = new Chart(mobileCtx, {
          type: "bar",
          data: {
            labels: mobileLabels,
            datasets: [{
              label: "Total Sales",
              data: mobileValues,
              backgroundColor: mobileLabels.map(() => `hsl(${Math.random() * 360}, 80%, 60%)`),
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            ...smallFontOptions,
            plugins: {
              ...smallFontOptions.plugins,
              title: { ...smallFontOptions.plugins.title, text: "Mobile Phone Sales (Total Cumulative Revenue)" }
            },
            scales: {
              x: { ticks: { color: "#fff", font: tickFont } },
              y: { ticks: { color: "#fff", font: tickFont } }
            }
          }
        });
      } else {
        mobileChart.data.labels = mobileLabels;
        mobileChart.data.datasets[0].data = mobileValues;
        mobileChart.update();
      }

      // --- Region (doughnut) ---
      if (!regionChart) {
        const REGION_COLORS = ['#60A5FA', '#34D399', '#FBBF24', '#F87171', '#A78BFA'];
        regionChart = new Chart(regionCtx, {
          type: "doughnut",
          data: {
            labels: regionLabels,
            datasets: [{
              label: "Total Revenue",
              data: regionValues,
              backgroundColor: regionLabels.map((_, i) => REGION_COLORS[i % REGION_COLORS.length]),
              borderColor: "#1E293B",
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "40%",
            radius: "90%",
            ...smallFontOptions,
            plugins: {
              ...smallFontOptions.plugins,
              title: { ...smallFontOptions.plugins.title, text: "Revenue by Region", font: { size: 18 } },
              legend: { labels: { color: "#fff", font: { size: 12 } } }
            }
          }
        });
      } else {
        regionChart.data.labels = regionLabels;
        regionChart.data.datasets[0].data = regionValues;
        regionChart.update();
      }

      // --- Top products ---
      if (!productChart) {
        productChart = new Chart(productCtx, {
          type: "bar",
          data: {
            labels: productLabels,
            datasets: [{
              label: "Units Sold In Last 5 Minutes Completed Window",
              data: productValues,
              backgroundColor: productLabels.map(() => `hsl(${Math.random() * 360}, 80%, 60%)`),
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            ...smallFontOptions,
            plugins: {
              ...smallFontOptions.plugins,
              title: { ...smallFontOptions.plugins.title, text: "Product Units Sold" }
            },
            scales: {
              x: { ticks: { color: "#fff", font: tickFont } },
              y: { ticks: { color: "#fff", font: tickFont } }
            }
          }
        });
      } else {
        productChart.data.labels = productLabels;
        productChart.data.datasets[0].data = productValues;
        productChart.update();
      }

      // --- Line Chart ---
      if (!lineChart) {
        lineChart = new Chart(lineCtx, {
          type: "line",
          data: {
            labels: weekLabels,
            datasets: lineDatasets
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            ...smallFontOptions,
            plugins: {
              ...smallFontOptions.plugins,
              title: { ...smallFontOptions.plugins.title, text: "Last 10 Minutes - Regional Sales" }
            },
            scales: {
              x: { ticks: { color: "#fff", font: tickFont } },
              y: { ticks: { color: "#fff", font: tickFont }, beginAtZero: true }
            }
          }
        });
      } else {
        lineChart.data.labels = weekLabels;
        lineChart.data.datasets = lineDatasets;
        lineChart.update();
      }

    } catch (err) {
      console.error("Error fetching/updating charts:", err);
    }
  }

  // initial load
  fetchData();

  // update every 5s but skip while hover
  const updater = setInterval(() => {
    fetchData();
  }, 5000);
});
