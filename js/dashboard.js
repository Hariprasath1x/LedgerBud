// Dashboard page logic

function loadDashboard() {
    // Get totals
    const totals = calculateTotals();
    
    // Update summary cards
    document.getElementById('totalIncome').textContent = `$${totals.income.toFixed(2)}`;
    document.getElementById('totalExpense').textContent = `$${totals.expense.toFixed(2)}`;
    document.getElementById('savings').textContent = `$${totals.savings.toFixed(2)}`;
    document.getElementById('netBalance').textContent = `$${totals.netBalance.toFixed(2)}`;
    
    // Get monthly data
    const monthlyData = getMonthlyData(6);
    
    // Create Monthly Income vs Expense Chart
    const monthlyChart = new ApexCharts(document.querySelector("#monthlyChart"), {
        chart: {
            type: 'bar',
            height: 300,
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
            }
        ],
        colors: ['#16a34a', '#dc2626'],
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: '55%',
                endingShape: 'rounded'
            }
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
            categories: monthlyData.months
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
    });
    monthlyChart.render();
    
    // Get category breakdown for expenses
    const categoryBreakdown = getCategoryBreakdown('expense');
    const categories = Object.keys(categoryBreakdown);
    const values = Object.values(categoryBreakdown);
    
    if (categories.length > 0) {
        // Create Category-wise Expense Chart
        const categoryChart = new ApexCharts(document.querySelector("#categoryChart"), {
            chart: {
                type: 'pie',
                height: 300
            },
            series: values,
            labels: categories,
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
        categoryChart.render();
    } else {
        document.querySelector('#categoryChart').innerHTML = '<p class="text-center text-gray-500 py-8">No expense data available</p>';
    }
    
    // Load recent transactions
    loadRecentTransactions();
}

function loadRecentTransactions() {
    const transactions = getTransactions();
    const recentTransactions = transactions
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 5);
    
    const tbody = document.getElementById('transactionsTable');
    tbody.innerHTML = '';
    
    if (recentTransactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                    No transactions found
                </td>
            </tr>
        `;
        return;
    }
    
    recentTransactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        let typeColor = '';
        let amountSign = '';
        
        switch(transaction.type) {
            case 'income':
                typeColor = 'text-green-600';
                amountSign = '+';
                break;
            case 'expense':
                typeColor = 'text-red-600';
                amountSign = '-';
                break;
            case 'investment':
                typeColor = 'text-blue-600';
                amountSign = '-';
                break;
            case 'insurance':
                typeColor = 'text-purple-600';
                amountSign = '-';
                break;
        }
        
        row.innerHTML = `
            <td class="px-6 py-4 text-sm text-gray-900">${transaction.date}</td>
            <td class="px-6 py-4 text-sm text-gray-900">${transaction.notes || transaction.category}</td>
            <td class="px-6 py-4 text-sm text-gray-600">${transaction.category}</td>
            <td class="px-6 py-4 text-sm">
                <span class="px-2 py-1 text-xs font-medium rounded ${getTypeBadgeClass(transaction.type)}">
                    ${transaction.type}
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-right font-medium ${typeColor}">${amountSign}$${transaction.amount.toFixed(2)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function getTypeBadgeClass(type) {
    const badgeClasses = {
        'income': 'bg-green-100 text-green-800',
        'expense': 'bg-red-100 text-red-800',
        'investment': 'bg-blue-100 text-blue-800',
        'insurance': 'bg-purple-100 text-purple-800'
    };
    return badgeClasses[type] || 'bg-gray-100 text-gray-800';
}
