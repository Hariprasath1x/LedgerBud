// API Base Configuration
const API_BASE_URL = 'http://localhost:3000/api';

// API Functions

// Get all transactions
async function getTransactions() {
    try {
        // Simulated API call - replace with actual API endpoint
        // const response = await fetch(`${API_BASE_URL}/transactions`);
        // if (!response.ok) throw new Error('Failed to fetch transactions');
        // return await response.json();
        
        // Demo data
        return getSampleTransactions();
    } catch (error) {
        console.error('Error fetching transactions:', error);
        throw error;
    }
}

// Add new transaction
async function addTransaction(transactionData) {
    try {
        // Simulated API call - replace with actual API endpoint
        // const response = await fetch(`${API_BASE_URL}/transactions/add`, {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify(transactionData)
        // });
        // if (!response.ok) throw new Error('Failed to add transaction');
        // return await response.json();
        
        // Demo: Store in localStorage
        const transactions = JSON.parse(localStorage.getItem('transactions') || '[]');
        const newTransaction = {
            id: Date.now().toString(),
            ...transactionData
        };
        transactions.push(newTransaction);
        localStorage.setItem('transactions', JSON.stringify(transactions));
        return newTransaction;
    } catch (error) {
        console.error('Error adding transaction:', error);
        throw error;
    }
}

// Get summary data
async function getSummary() {
    try {
        // Simulated API call - replace with actual API endpoint
        // const response = await fetch(`${API_BASE_URL}/reports/summary`);
        // if (!response.ok) throw new Error('Failed to fetch summary');
        // return await response.json();
        
        // Demo data
        const transactions = await getTransactions();
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        
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
            
        const savings = income - expense;
        const netBalance = income - expense;
        
        return { income, expense, savings, netBalance };
    } catch (error) {
        console.error('Error fetching summary:', error);
        throw error;
    }
}

// Get monthly report data
async function getMonthlyReportData() {
    try {
        // Simulated API call - replace with actual API endpoint
        // const response = await fetch(`${API_BASE_URL}/reports/monthly`);
        // if (!response.ok) throw new Error('Failed to fetch monthly data');
        // return await response.json();
        
        // Demo data
        return {
            months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            income: [5000, 5200, 4800, 5500, 5300, 5600],
            expense: [3500, 3800, 3200, 4000, 3600, 3900],
            savings: [1500, 1400, 1600, 1500, 1700, 1700],
            cumulativeSavings: [1500, 2900, 4500, 6000, 7700, 9400]
        };
    } catch (error) {
        console.error('Error fetching monthly data:', error);
        throw error;
    }
}

// Get sample transactions (demo data)
function getSampleTransactions() {
    // Check if we have transactions in localStorage
    const storedTransactions = localStorage.getItem('transactions');
    if (storedTransactions) {
        return JSON.parse(storedTransactions);
    }
    
    // Default sample data
    const sampleTransactions = [
        {
            id: '1',
            date: '2026-01-20',
            description: 'Monthly Salary',
            category: 'Salary',
            type: 'income',
            amount: 5000,
            notes: 'January salary'
        },
        {
            id: '2',
            date: '2026-01-19',
            description: 'Grocery Shopping',
            category: 'Food',
            type: 'expense',
            amount: 150.50,
            notes: 'Weekly groceries'
        },
        {
            id: '3',
            date: '2026-01-18',
            description: 'Gas Station',
            category: 'Transport',
            type: 'expense',
            amount: 60.00,
            notes: 'Fuel'
        },
        {
            id: '4',
            date: '2026-01-17',
            description: 'Freelance Project',
            category: 'Freelance',
            type: 'income',
            amount: 800,
            notes: 'Web development project'
        },
        {
            id: '5',
            date: '2026-01-16',
            description: 'Electricity Bill',
            category: 'Utilities',
            type: 'expense',
            amount: 120.00,
            notes: 'January bill'
        },
        {
            id: '6',
            date: '2026-01-15',
            description: 'Restaurant',
            category: 'Food',
            type: 'expense',
            amount: 85.00,
            notes: 'Dinner with friends'
        },
        {
            id: '7',
            date: '2026-01-14',
            description: 'Online Course',
            category: 'Education',
            type: 'expense',
            amount: 49.99,
            notes: 'JavaScript course'
        },
        {
            id: '8',
            date: '2026-01-13',
            description: 'Stock Dividend',
            category: 'Investment',
            type: 'income',
            amount: 250,
            notes: 'Quarterly dividend'
        },
        {
            id: '9',
            date: '2026-01-12',
            description: 'Gym Membership',
            category: 'Healthcare',
            type: 'expense',
            amount: 50.00,
            notes: 'Monthly membership'
        },
        {
            id: '10',
            date: '2026-01-11',
            description: 'Movie Tickets',
            category: 'Entertainment',
            type: 'expense',
            amount: 30.00,
            notes: 'Weekend movie'
        }
    ];
    
    // Store sample data
    localStorage.setItem('transactions', JSON.stringify(sampleTransactions));
    return sampleTransactions;
}
