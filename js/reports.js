// Reports page logic

function loadReports() {
    const monthlyData = getMonthlyData(6);
    
    // Monthly Trend Chart
    const monthlyTrendChart = new ApexCharts(document.querySelector("#monthlyTrendChart"), {
        chart: {
            type: 'line',
            height: 350,
            toolbar: { show: false }
        },
        series: [
            {
                name: 'Income',
                data: monthlyData.income
            },
            {
                name: 'Expense',
                data: monthlyData.expense
            },
            {
                name: 'Savings',
                data: monthlyData.savings
            }
        ],
        colors: ['#16a34a', '#dc2626', '#2563eb'],
        xaxis: {
            categories: monthlyData.months
        },
        stroke: {
            curve: 'smooth',
            width: 2
        },
        markers: {
            size: 4
        },
        legend: {
            position: 'top'
        },
        yaxis: {
            title: {
                text: '$ (Amount)'
            }
        }
    });
    monthlyTrendChart.render();
    
    // Income Category Chart
    const incomeBreakdown = getCategoryBreakdown('income');
    const incomeCategories = Object.keys(incomeBreakdown);
    const incomeValues = Object.values(incomeBreakdown);
    
    if (incomeCategories.length > 0) {
        const incomeCategoryChart = new ApexCharts(document.querySelector("#incomeCategoryChart"), {
            chart: {
                type: 'donut',
                height: 300
            },
            series: incomeValues,
            labels: incomeCategories,
            colors: ['#16a34a', '#22c55e', '#4ade80', '#86efac', '#bbf7d0', '#dcfce7'],
            legend: {
                position: 'bottom'
            },
            dataLabels: {
                enabled: true,
                formatter: function (val) {
                    return val.toFixed(1) + '%';
                }
            }
        });
        incomeCategoryChart.render();
    } else {
        document.querySelector('#incomeCategoryChart').innerHTML = '<p class="text-center text-gray-500 py-8">No income data available</p>';
    }
    
    // Expense Category Chart
    const expenseBreakdown = getCategoryBreakdown('expense');
    const expenseCategories = Object.keys(expenseBreakdown);
    const expenseValues = Object.values(expenseBreakdown);
    
    if (expenseCategories.length > 0) {
        const expenseCategoryChart = new ApexCharts(document.querySelector("#expenseCategoryChart"), {
            chart: {
                type: 'donut',
                height: 300
            },
            series: expenseValues,
            labels: expenseCategories,
            colors: ['#dc2626', '#ef4444', '#f87171', '#fca5a5', '#fecaca', '#fee2e2', '#fef2f2', '#991b1b'],
            legend: {
                position: 'bottom'
            },
            dataLabels: {
                enabled: true,
                formatter: function (val) {
                    return val.toFixed(1) + '%';
                }
            }
        });
        expenseCategoryChart.render();
    } else {
        document.querySelector('#expenseCategoryChart').innerHTML = '<p class="text-center text-gray-500 py-8">No expense data available</p>';
    }
    
    // Savings Growth Chart
    const savingsGrowthChart = new ApexCharts(document.querySelector("#savingsGrowthChart"), {
        chart: {
            type: 'area',
            height: 350,
            toolbar: { show: false }
        },
        series: [{
            name: 'Cumulative Savings',
            data: monthlyData.cumulativeSavings
        }],
        colors: ['#2563eb'],
        xaxis: {
            categories: monthlyData.months
        },
        stroke: {
            curve: 'smooth',
            width: 2
        },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.4,
                opacityTo: 0.1
            }
        },
        yaxis: {
            title: {
                text: '$ (Amount)'
            }
        }
    });
    savingsGrowthChart.render();
    
    // Update statistics
    const totalIncome = monthlyData.income.reduce((a, b) => a + b, 0);
    const totalExpense = monthlyData.expense.reduce((a, b) => a + b, 0);
    const monthsCount = monthlyData.months.length;
    
    const avgIncome = monthsCount > 0 ? totalIncome / monthsCount : 0;
    const avgExpense = monthsCount > 0 ? totalExpense / monthsCount : 0;
    const savingsRate = totalIncome > 0 ? ((totalIncome - totalExpense) / totalIncome * 100) : 0;
    
    document.getElementById('avgIncome').textContent = `$${avgIncome.toFixed(2)}`;
    document.getElementById('avgExpense').textContent = `$${avgExpense.toFixed(2)}`;
    document.getElementById('savingsRate').textContent = `${savingsRate.toFixed(1)}%`;
}
