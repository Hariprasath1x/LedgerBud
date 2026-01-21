// Chart configurations and rendering functions

// Create Monthly Income vs Expense Chart
function createMonthlyChart(income, expense) {
    const options = {
        chart: {
            type: 'bar',
            height: 300,
            toolbar: {
                show: false
            }
        },
        series: [
            {
                name: 'Income',
                data: income
            },
            {
                name: 'Expense',
                data: expense
            }
        ],
        colors: ['#16a34a', '#dc2626'],
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: '55%',
                endingShape: 'rounded'
            },
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            show: true,
            width: 2,
            colors: ['transparent']
        },
        xaxis: {
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        },
        yaxis: {
            title: {
                text: '$ (Amount)'
            }
        },
        fill: {
            opacity: 1
        },
        legend: {
            position: 'top',
            horizontalAlign: 'left'
        }
    };

    const chart = new ApexCharts(document.querySelector("#monthlyChart"), options);
    chart.render();
}

// Create Category-wise Expense Chart
function createCategoryChart(categories, values) {
    const options = {
        chart: {
            type: 'pie',
            height: 300
        },
        series: values,
        labels: categories,
        colors: ['#dc2626', '#ef4444', '#f87171', '#fca5a5', '#fecaca', '#fee2e2'],
        legend: {
            position: 'bottom'
        },
        dataLabels: {
            enabled: true,
            formatter: function (val) {
                return val.toFixed(1) + '%';
            }
        }
    };

    const chart = new ApexCharts(document.querySelector("#categoryChart"), options);
    chart.render();
}

// Process transaction data for charts
function processTransactionData(transactions) {
    // Calculate monthly totals (last 6 months)
    const monthlyData = {
        income: [4800, 5200, 4900, 5500, 5300, 5600],
        expense: [3200, 3800, 3400, 4000, 3600, 3900]
    };
    
    // Calculate category-wise expense
    const categoryTotals = {};
    transactions.forEach(t => {
        if (t.type === 'expense') {
            categoryTotals[t.category] = (categoryTotals[t.category] || 0) + t.amount;
        }
    });
    
    const categories = Object.keys(categoryTotals);
    const values = Object.values(categoryTotals);
    
    return {
        monthly: monthlyData,
        category: { categories, values }
    };
}
