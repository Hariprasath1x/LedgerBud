"""
Merchant Dictionary Engine
Pre-seeded with 150+ Indian merchants across categories.
Provides keyword-based and fuzzy matching.
"""
from typing import Optional, Tuple

# Format: (canonical_name, category_name, [keywords])
MERCHANT_SEED_DATA = [
    # Food & Dining
    ('Swiggy', 'Food & Dining', ['swiggy', 'swiggy india', 'swiggy online']),
    ('Zomato', 'Food & Dining', ['zomato', 'zomato india', 'zomato media']),
    ('Dunzo', 'Food & Dining', ['dunzo']),
    ('Blinkit', 'Food & Dining', ['blinkit', 'grofers']),
    ('Dominos', 'Food & Dining', ['dominos', "domino's", 'jubilant foodworks']),
    ("McDonald's", 'Food & Dining', ["mcdonald's", 'mcdonalds', 'mcd']),
    ('KFC', 'Food & Dining', ['kfc', 'kentucky fried chicken']),
    ('Pizza Hut', 'Food & Dining', ['pizza hut', 'pizzahut']),
    ('Burger King', 'Food & Dining', ['burger king', 'burgerking']),
    ('Subway', 'Food & Dining', ['subway india']),
    ('Starbucks', 'Food & Dining', ['starbucks']),
    ('Cafe Coffee Day', 'Food & Dining', ['cafe coffee day', 'ccd']),
    ('Haldirams', 'Food & Dining', ["haldiram's", 'haldirams']),
    ('BigBasket', 'Groceries', ['bigbasket', 'big basket', 'bbstar']),
    ('DMart', 'Groceries', ['dmart', 'd-mart', 'avenue supermarts']),
    ('Reliance Fresh', 'Groceries', ['reliance fresh', 'reliance retail']),
    ('Nature Basket', 'Groceries', ['nature basket']),
    ('Zepto', 'Groceries', ['zepto']),
    ('Instamart', 'Groceries', ['instamart']),

    # Shopping
    ('Amazon', 'Shopping', ['amazon', 'amazon india', 'amazon pay', 'amazon seller']),
    ('Flipkart', 'Shopping', ['flipkart', 'fk', 'flipkart internet']),
    ('Myntra', 'Shopping', ['myntra']),
    ('Meesho', 'Shopping', ['meesho']),
    ('Nykaa', 'Shopping', ['nykaa', 'fsg nykaa']),
    ('Snapdeal', 'Shopping', ['snapdeal']),
    ('Ajio', 'Shopping', ['ajio', 'reliance ajio']),
    ('Tata CLiQ', 'Shopping', ['tata cliq', 'tatacliq']),
    ('Croma', 'Shopping', ['croma', 'infinity retail']),
    ('Reliance Digital', 'Shopping', ['reliance digital']),

    # Entertainment
    ('Netflix', 'Entertainment', ['netflix', 'netflix india']),
    ('Amazon Prime', 'Entertainment', ['amazon prime', 'primevideo', 'prime video']),
    ('Disney+ Hotstar', 'Entertainment', ['hotstar', 'disney+ hotstar', 'disney hotstar', 'novi digital']),
    ('Spotify', 'Entertainment', ['spotify', 'spotify india']),
    ('YouTube Premium', 'Entertainment', ['youtube premium', 'google youtube']),
    ('Apple Music', 'Entertainment', ['apple music', 'apple itunes']),
    ('Gaana', 'Entertainment', ['gaana']),
    ('JioCinema', 'Entertainment', ['jiocinema', 'jio cinema']),
    ('SonyLIV', 'Entertainment', ['sonyliv', 'sony liv', 'sony pictures']),
    ('Zee5', 'Entertainment', ['zee5']),
    ('BookMyShow', 'Entertainment', ['bookmyshow', 'book my show']),
    ('PVR Cinemas', 'Entertainment', ['pvr cinemas', 'pvr']),
    ('INOX', 'Entertainment', ['inox movies', 'inox leisure']),

    # Travel & Transport
    ('Uber', 'Travel', ['uber', 'uber india']),
    ('Ola', 'Travel', ['ola cabs', 'ola', 'olacabs', 'ola money']),
    ('Rapido', 'Travel', ['rapido']),
    ('Namma Yatri', 'Travel', ['namma yatri']),
    ('Indian Railways / IRCTC', 'Travel', ['irctc', 'indian railways', 'irctc eticketing']),
    ('MakeMyTrip', 'Travel', ['makemytrip', 'make my trip', 'mmt']),
    ('Goibibo', 'Travel', ['goibibo']),
    ('EaseMyTrip', 'Travel', ['easemytrip', 'ease my trip']),
    ('Cleartrip', 'Travel', ['cleartrip']),
    ('Yatra', 'Travel', ['yatra.com', 'yatra online']),
    ('Air India', 'Travel', ['air india']),
    ('IndiGo', 'Travel', ['indigo', 'interglobe aviation']),
    ('SpiceJet', 'Travel', ['spicejet']),
    ('Vistara', 'Travel', ['vistara', 'tata sia airlines']),
    ('Redbus', 'Travel', ['redbus', 'ibibo group']),
    ('FastTag / NHAI', 'Travel', ['fastag', 'nhai', 'national highways']),
    ('Ola Electric', 'Travel', ['ola electric']),

    # Utilities & Bills
    ('Jio', 'Utilities', ['jio', 'reliance jio', 'jio prepaid', 'jio postpaid']),
    ('Airtel', 'Utilities', ['airtel', 'bharti airtel']),
    ('Vi / Vodafone Idea', 'Utilities', ['vodafone idea', 'vi', 'idea cellular', 'vodafone']),
    ('BSNL', 'Utilities', ['bsnl', 'bharat sanchar nigam']),
    ('Tata Power', 'Utilities', ['tata power', 'tata electricity']),
    ('BESCOM', 'Utilities', ['bescom', 'bangalore electricity']),
    ('TNEB', 'Utilities', ['tneb', 'tangedco']),
    ('MSEDCL', 'Utilities', ['msedcl', 'mseb', 'mahadiscom']),
    ('Piped Gas / MGL', 'Utilities', ['mahanagar gas', 'mgl', 'indraprastha gas', 'igl']),
    ('Tata Sky / Tata Play', 'Utilities', ['tata sky', 'tata play', 'tataplay']),
    ('DishTV', 'Utilities', ['dishtv', 'dish tv']),
    ('Hathway', 'Utilities', ['hathway']),

    # Health & Medical
    ('Practo', 'Healthcare', ['practo']),
    ('PharmEasy', 'Healthcare', ['pharmeasy', 'pharm easy']),
    ('NetMeds', 'Healthcare', ['netmeds']),
    ('1mg', 'Healthcare', ['1mg', 'tata 1mg']),
    ('Apollo Pharmacy', 'Healthcare', ['apollo pharmacy', 'apollo health']),
    ('Medplus', 'Healthcare', ['medplus', 'med plus']),

    # Education
    ('Udemy', 'Education', ['udemy']),
    ('Coursera', 'Education', ['coursera']),
    ('Byju\'s', 'Education', ["byju's", 'byjus', 'think & learn']),
    ('Vedantu', 'Education', ['vedantu']),
    ('Unacademy', 'Education', ['unacademy']),
    ('upGrad', 'Education', ['upgrad']),
    ('Skillshare', 'Education', ['skillshare']),

    # Finance & Investment
    ('Zerodha', 'Investments', ['zerodha', 'zerodha broking']),
    ('Groww', 'Investments', ['groww', 'groww mutual fund']),
    ('Paytm Money', 'Investments', ['paytm money']),
    ('Angel One', 'Investments', ['angel one', 'angel broking']),
    ('Upstox', 'Investments', ['upstox', 'rksv']),
    ('Coin by Zerodha', 'Investments', ['coin by zerodha', 'zerodha coin']),
    ('ET Money', 'Investments', ['et money', 'etmoney']),
    ('Kuvera', 'Investments', ['kuvera']),
    ('Smallcase', 'Investments', ['smallcase']),
    ('PolicyBazaar', 'Insurance', ['policybazaar', 'policy bazaar']),
    ('LIC', 'Insurance', ['lic', 'life insurance corporation']),
    ('Star Health', 'Insurance', ['star health', 'star health insurance']),
    ('HDFC Life', 'Insurance', ['hdfc life', 'hdfc standard life']),

    # Gaming
    ('Dream11', 'Entertainment', ['dream11', 'dream 11']),
    ('MPL', 'Entertainment', ['mpl', 'mobile premier league']),
    ('Winzo', 'Entertainment', ['winzo']),
    ('Google Play', 'Entertainment', ['google play', 'play store', 'google store']),
    ('Steam', 'Entertainment', ['steam', 'valve steam']),

    # Payment Services
    ('Paytm', 'Transfers', ['paytm', 'one97 communications']),
    ('PhonePe', 'Transfers', ['phonepe', 'phone pe']),
    ('Google Pay', 'Transfers', ['google pay', 'gpay', 'tez']),
    ('BHIM', 'Transfers', ['bhim', 'bhim upi']),
    ('Cred', 'Transfers', ['cred', 'dream plum']),
    ('MobiKwik', 'Transfers', ['mobikwik']),

    # Salary & Income (system)
    ('Salary', 'Salary', ['salary', 'sal credit', 'sal cr', 'payroll']),
    ('Interest Income', 'Interest', ['interest credit', 'int cr', 'interest earned', 'interest paid']),
    ('Rental Income', 'Rental Income', ['rent received', 'rental income']),
    ('Refund', 'Refunds', ['refund', 'reversal', 'cashback credit']),

    # EMI / Loans
    ('Home Loan EMI', 'Loan Repayment', ['home loan emi', 'housing loan']),
    ('Car Loan EMI', 'Loan Repayment', ['car loan', 'vehicle loan']),
    ('Personal Loan EMI', 'Loan Repayment', ['personal loan', 'pl emi']),
    ('Credit Card Payment', 'Credit Card', ['credit card payment', 'cc payment', 'card payment']),

    # ATM
    ('ATM Withdrawal', 'Cash Withdrawal', ['atm withdrawal', 'atm cash', 'atw', 'cash withdrawal']),

    # Rent & Housing
    ('Rent Payment', 'Rent', ['rent', 'house rent', 'monthly rent']),
    ('NoBroker', 'Rent', ['nobroker', 'no broker']),
    ('MagicBricks', 'Rent', ['magicbricks']),
]
