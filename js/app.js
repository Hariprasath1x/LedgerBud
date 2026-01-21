// Main application logic

// Load dashboard data
async function loadDashboardData() {
    try {
        // Get transactions and summary
        const transactions = await getTransactions();
        const summary = await getSummary();
        
        // Update summary cards
        document.getElementById('totalIncome').textContent = `$${summary.income.toFixed(2)}`;
        document.getElementById('totalExpense').textContent = `$${summary.expense.toFixed(2)}`;
        document.getElementById('savings').textContent = `$${summary.savings.toFixed(2)}`;
        document.getElementById('netBalance').textContent = `$${summary.netBalance.toFixed(2)}`;
        
        // Process data for charts
        const chartData = processTransactionData(transactions);
        
        // Create charts
        createMonthlyChart(chartData.monthly.income, chartData.monthly.expense);
        
        if (chartData.category.values.length > 0) {
            createCategoryChart(chartData.category.categories, chartData.category.values);
        } else {
            // Show placeholder if no expense data
            document.querySelector('#categoryChart').innerHTML = '<p class="text-center text-gray-500 py-8">No expense data available</p>';
        }
        
        // Load recent transactions
        loadRecentTransactions(transactions.slice(0, 5));
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Load recent transactions table
function loadRecentTransactions(transactions) {
    const tbody = document.getElementById('transactionsTable');
    tbody.innerHTML = '';
    
    if (transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                    No transactions found
                </td>
            </tr>
        `;
        return;
    }
    
    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        const typeColor = transaction.type === 'income' ? 'text-green-600' : 'text-red-600';
        const amountSign = transaction.type === 'income' ? '+' : '-';
        
        row.innerHTML = `
            <td class="px-6 py-4 text-sm text-gray-900">${transaction.date}</td>
            <td class="px-6 py-4 text-sm text-gray-900">${transaction.description}</td>
            <td class="px-6 py-4 text-sm text-gray-600">${transaction.category}</td>
            <td class="px-6 py-4 text-sm">
                <span class="px-2 py-1 text-xs font-medium rounded ${transaction.type === 'income' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${transaction.type}
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-right font-medium ${typeColor}">${amountSign}$${transaction.amount.toFixed(2)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Validate form input
function validateTransactionForm(data) {
    if (!data.type || !data.amount || !data.category || !data.description || !data.date) {
        return { valid: false, message: 'All required fields must be filled' };
    }
    
    if (data.amount <= 0) {
        return { valid: false, message: 'Amount must be greater than zero' };
    }
    
    return { valid: true };
}

// Show notification
function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-md shadow-lg text-white ${
        type === 'success' ? 'bg-green-600' : 'bg-red-600'
    } z-50`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Export data to CSV
function exportToCSV(transactions) {
    const headers = ['Date', 'Description', 'Category', 'Type', 'Amount', 'Notes'];
    const rows = transactions.map(t => [
        t.date,
        t.description,
        t.category,
        t.type,
        t.amount,
        t.notes || ''
    ]);
    
    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
        csvContent += row.map(cell => `"${cell}"`).join(',') + '\n';
    });
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Calculate percentage change
function calculatePercentageChange(current, previous) {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
}
