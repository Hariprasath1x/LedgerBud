// Transaction management functions

// Initialize sample transactions if none exist
function initializeSampleTransactions() {
    const existing = localStorage.getItem('transactions');
    if (!existing) {
        const sampleTransactions = [
            {
                id: Date.now() + '-1',
                amount: 5000,
                type: 'income',
                category: 'Investment',
                date: '2026-01-20',
                notes: 'Monthly salary payment'
            },
            {
                id: Date.now() + '-2',
                amount: 350,
                type: 'expense',
                category: 'Food',
                date: '2026-01-19',
                notes: 'Weekly grocery shopping'
            },
            {
                id: Date.now() + '-3',
                amount: 1200,
                type: 'expense',
                category: 'Rent',
                date: '2026-01-18',
                notes: 'Monthly apartment rent'
            },
            {
                id: Date.now() + '-4',
                amount: 50,
                type: 'expense',
                category: 'Recharges',
                date: '2026-01-17',
                notes: 'Mobile recharge'
            },
            {
                id: Date.now() + '-5',
                amount: 2000,
                type: 'investment',
                category: 'Investment',
                date: '2026-01-16',
                notes: 'Mutual fund SIP'
            },
            {
                id: Date.now() + '-6',
                amount: 150,
                type: 'expense',
                category: 'OTT',
                date: '2026-01-15',
                notes: 'Netflix and Prime subscriptions'
            },
            {
                id: Date.now() + '-7',
                amount: 500,
                type: 'insurance',
                category: 'Insurance',
                date: '2026-01-14',
                notes: 'Health insurance premium'
            },
            {
                id: Date.now() + '-8',
                amount: 800,
                type: 'expense',
                category: 'EMI',
                date: '2026-01-13',
                notes: 'Car loan EMI'
            },
            {
                id: Date.now() + '-9',
                amount: 200,
                type: 'expense',
                category: 'Travel',
                date: '2026-01-12',
                notes: 'Fuel and transport'
            },
            {
                id: Date.now() + '-10',
                amount: 3000,
                type: 'income',
                category: 'Investment',
                date: '2026-01-11',
                notes: 'Freelance project payment'
            }
        ];
        localStorage.setItem('transactions', JSON.stringify(sampleTransactions));
    }
}

// Get all transactions
function getTransactions() {
    initializeSampleTransactions();
    const transactions = localStorage.getItem('transactions');
    return transactions ? JSON.parse(transactions) : [];
}

// Add a new transaction
function addTransaction(transactionData) {
    const transactions = getTransactions();
    const newTransaction = {
        id: Date.now().toString(),
        ...transactionData,
        createdAt: new Date().toISOString()
    };
    transactions.push(newTransaction);
    localStorage.setItem('transactions', JSON.stringify(transactions));
    return newTransaction;
}

// Remove a transaction
function removeTransaction(id) {
    let transactions = getTransactions();
    transactions = transactions.filter(t => t.id !== id);
    localStorage.setItem('transactions', JSON.stringify(transactions));
}

// Get transactions by type
function getTransactionsByType(type) {
    const transactions = getTransactions();
    return transactions.filter(t => t.type === type);
}

// Get transactions by date range
function getTransactionsByDateRange(startDate, endDate) {
    const transactions = getTransactions();
    return transactions.filter(t => {
        const transactionDate = new Date(t.date);
        return transactionDate >= new Date(startDate) && transactionDate <= new Date(endDate);
    });
}

// Calculate totals
function calculateTotals() {
    const transactions = getTransactions();
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    
    // Filter current month transactions
    const monthlyTransactions = transactions.filter(t => {
        const date = new Date(t.date);
        return date.getMonth() === currentMonth && date.getFullYear() === currentYear;
    });
    
    const income = monthlyTransactions
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + t.amount, 0);
    
    const expense = monthlyTransactions
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0);
    
    const investment = monthlyTransactions
        .filter(t => t.type === 'investment')
        .reduce((sum, t) => sum + t.amount, 0);
    
    const insurance = monthlyTransactions
        .filter(t => t.type === 'insurance')
        .reduce((sum, t) => sum + t.amount, 0);
    
    const savings = income - expense - investment - insurance;
    const netBalance = income - expense - investment - insurance;
    
    return {
        income,
        expense,
        investment,
        insurance,
        savings,
        netBalance
    };
}

// Get category breakdown
function getCategoryBreakdown(type) {
    const transactions = getTransactionsByType(type);
    const breakdown = {};
    
    transactions.forEach(t => {
        if (breakdown[t.category]) {
            breakdown[t.category] += t.amount;
        } else {
            breakdown[t.category] = t.amount;
        }
    });
    
    return breakdown;
}

// Get monthly data for charts
function getMonthlyData(monthsBack = 6) {
    const transactions = getTransactions();
    const monthlyData = {
        months: [],
        income: [],
        expense: [],
        investment: [],
        insurance: [],
        savings: [],
        cumulativeSavings: []
    };
    
    const currentDate = new Date();
    let cumulativeSavings = 0;
    
    for (let i = monthsBack - 1; i >= 0; i--) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
        const monthName = date.toLocaleDateString('en-US', { month: 'short' });
        monthlyData.months.push(monthName);
        
        const monthTransactions = transactions.filter(t => {
            const transactionDate = new Date(t.date);
            return transactionDate.getMonth() === date.getMonth() && 
                   transactionDate.getFullYear() === date.getFullYear();
        });
        
        const income = monthTransactions
            .filter(t => t.type === 'income')
            .reduce((sum, t) => sum + t.amount, 0);
        
        const expense = monthTransactions
            .filter(t => t.type === 'expense')
            .reduce((sum, t) => sum + t.amount, 0);
        
        const investment = monthTransactions
            .filter(t => t.type === 'investment')
            .reduce((sum, t) => sum + t.amount, 0);
        
        const insurance = monthTransactions
            .filter(t => t.type === 'insurance')
            .reduce((sum, t) => sum + t.amount, 0);
        
        const savings = income - expense - investment - insurance;
        cumulativeSavings += savings;
        
        monthlyData.income.push(income);
        monthlyData.expense.push(expense);
        monthlyData.investment.push(investment);
        monthlyData.insurance.push(insurance);
        monthlyData.savings.push(savings);
        monthlyData.cumulativeSavings.push(cumulativeSavings);
    }
    
    return monthlyData;
}
