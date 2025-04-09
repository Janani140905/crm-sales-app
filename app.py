import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Sales CRM System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create products table
    c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create feedback table
    c.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        product_id INTEGER,
        rating INTEGER NOT NULL,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Create sales table
    c.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        customer_name TEXT,
        customer_email TEXT,
        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Create inventory_log table
    c.execute('''
    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        quantity_change INTEGER NOT NULL,
        reason TEXT,
        log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')

    # Insert a default admin user if not exists
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_password = hashlib.sha256("password".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                 ("admin", hashed_password, "admin"))
    
    # Insert sample products if not exists
    c.execute("SELECT * FROM products LIMIT 1")
    if not c.fetchone():
        sample_products = [
            ("Laptop Pro", "High-performance laptop for professionals", "Electronics", 1299.99, 50),
            ("Office Chair", "Ergonomic office chair", "Furniture", 249.99, 100),
            ("CRM Software Premium", "Enterprise CRM solution", "Software", 499.99, 999),
            ("Business Phone", "Professional business phone system", "Electronics", 299.99, 75),
            ("Marketing Services", "Digital marketing service package", "Services", 999.99, 999),
            ("Desk Organizer", "Premium desk organizer set", "Office Supplies", 49.99, 200),
            ("Conference Table", "Large conference room table", "Furniture", 899.99, 20),
            ("Wireless Headset", "Professional wireless headset", "Electronics", 129.99, 150),
            ("Project Management Tool", "Cloud-based project management software", "Software", 299.99, 999),
            ("Customer Support Package", "Premium customer support service", "Services", 799.99, 999)
        ]
        c.executemany("INSERT INTO products (name, description, category, price, stock_quantity) VALUES (?, ?, ?, ?, ?)",
                     sample_products)
        
        # Insert sample sales data
        sample_sales = [
            (1, 2, 2599.98, "John Smith", "john@example.com", "2025-03-15 09:30:00"),
            (3, 1, 499.99, "Sarah Johnson", "sarah@example.com", "2025-03-16 14:20:00"),
            (2, 4, 999.96, "Michael Brown", "michael@example.com", "2025-03-18 11:45:00"),
            (5, 1, 999.99, "Emma Wilson", "emma@example.com", "2025-03-20 16:30:00"),
            (8, 2, 259.98, "David Lee", "david@example.com", "2025-03-22 10:15:00"),
            (4, 1, 299.99, "Lisa Wang", "lisa@example.com", "2025-03-25 13:40:00"),
            (7, 1, 899.99, "Robert Garcia", "robert@example.com", "2025-03-28 15:55:00")
        ]
        c.executemany("INSERT INTO sales (product_id, quantity, total_price, customer_name, customer_email, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
                     sample_sales)
        
        # Insert sample inventory log data
        sample_inventory_logs = [
            (1, -2, "Sale to John Smith", "2025-03-15 09:30:00"),
            (3, -1, "Sale to Sarah Johnson", "2025-03-16 14:20:00"),
            (6, 50, "Restocked inventory", "2025-03-17 08:00:00"),
            (2, -4, "Sale to Michael Brown", "2025-03-18 11:45:00"),
            (5, -1, "Sale to Emma Wilson", "2025-03-20 16:30:00"),
            (8, -2, "Sale to David Lee", "2025-03-22 10:15:00"),
            (4, -1, "Sale to Lisa Wang", "2025-03-25 13:40:00"),
            (7, -1, "Sale to Robert Garcia", "2025-03-28 15:55:00"),
            (9, 100, "Restocked inventory", "2025-04-01 09:00:00"),
            (2, 25, "Restocked inventory", "2025-04-02 10:30:00")
        ]
        c.executemany("INSERT INTO inventory_log (product_id, quantity_change, reason, log_date) VALUES (?, ?, ?, ?)",
                     sample_inventory_logs)
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# User Authentication Functions
def verify_password(username, password):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = c.fetchone()
    
    conn.close()
    return user

def get_user_role(username):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    c.execute("SELECT role FROM users WHERE username = ?", (username,))
    role = c.fetchone()
    
    conn.close()
    return role[0] if role else None

def username_exists(username):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    count = c.fetchone()[0]
    
    conn.close()
    return count > 0

def register_user(username, password, role="customer"):
    if username_exists(username):
        return False, "Username already exists. Please choose a different username."
    
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        conn.close()
        return True, "Registration successful! Please log in."
    except Exception as e:
        conn.close()
        return False, f"Registration failed: {str(e)}"

# Product Functions
def get_products(search_term=None, category=None):
    conn = sqlite3.connect('crm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM products"
    params = []
    
    if search_term:
        query += " WHERE (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
    elif category and category != "All":
        query += " WHERE category = ?"
        params.append(category)
    
    c.execute(query, params)
    products = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return products

def get_product_categories():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in c.fetchall()]
    
    conn.close()
    return categories

def get_product_by_id(product_id):
    conn = sqlite3.connect('crm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    
    conn.close()
    return dict(product) if product else None

# Feedback Functions
def submit_feedback(customer_name, customer_email, product_id, rating, comments):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    c.execute(
        "INSERT INTO feedback (customer_name, customer_email, product_id, rating, comments) VALUES (?, ?, ?, ?, ?)",
        (customer_name, customer_email, product_id, rating, comments)
    )
    
    conn.commit()
    conn.close()
    return True

# Database Explorer Functions
def get_tables():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    # Get list of tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in c.fetchall()]
    
    conn.close()
    return tables

def get_table_info(table_name):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    
    # Get table info (columns)
    c.execute(f"PRAGMA table_info({table_name});")
    columns = c.fetchall()
    
    # Get first 5 rows
    c.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    sample_data = c.fetchall()
    
    # Get total row count
    c.execute(f"SELECT COUNT(*) FROM {table_name};")
    row_count = c.fetchone()[0]
    
    conn.close()
    return {"columns": columns, "sample_data": sample_data, "row_count": row_count}

def execute_query(query):
    conn = sqlite3.connect('crm.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute(query)
        
        # Check if query is SELECT
        if query.strip().upper().startswith("SELECT"):
            results = [dict(row) for row in c.fetchall()]
            conn.close()
            return {"success": True, "results": results, "row_count": len(results)}
        else:
            # For non-SELECT queries
            conn.commit()
            row_count = c.rowcount
            conn.close()
            return {"success": True, "row_count": row_count}
            
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Sidebar for navigation
with st.sidebar:
    # Use a simple emoji instead of an external image
    st.markdown("# 💼")
    st.title("Sales CRM System")
    
    if st.session_state.logged_in:
        st.write(f"Logged in as: **{st.session_state.username}**")
        st.write(f"Role: **{st.session_state.role}**")
        
        st.markdown("### Navigation")
        if st.button("Dashboard"):
            st.session_state.page = 'dashboard'
        if st.button("Products"):
            st.session_state.page = 'products'
        if st.button("Customer Feedback"):
            st.session_state.page = 'feedback'
        if st.button("Database Explorer"):
            st.session_state.page = 'database'
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.page = 'login'
            st.rerun()
    else:
        st.info("Please login to access the CRM system")

# Main content based on page selection
if not st.session_state.logged_in:
    st.session_state.page = 'login'

if st.session_state.page == 'login':
    st.title("Welcome to the Sales CRM System")
    
    # Create tabs for login and registration
    login_tab, register_tab = st.tabs(["Login", "Register"])
    
    with login_tab:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            ### Welcome Back
            
            This system helps sales teams manage customer relationships, track products, and collect customer feedback.
            
            **Features:**
            - Product management and search
            - Customer feedback collection
            - Sales analytics and reporting
            
            Login with your credentials to get started.
            
            **Default admin login:**
            - Username: admin
            - Password: password
            """)
        
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if username and password:
                        user = verify_password(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = get_user_role(username)
                            st.session_state.page = 'dashboard'
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please enter both username and password")
    
    with register_tab:
        st.markdown("### Create a New Account")
        st.markdown("Register to access our product catalog and submit feedback.")
        
        with st.form("register_form"):
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if not new_username or not new_password or not confirm_password:
                    st.error("All fields are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.success(message)
                        # Switch to login tab after successful registration
                        st.info("You can now log in with your new account!")
                    else:
                        st.error(message)

elif st.session_state.page == 'dashboard':
    st.title("Dashboard")
    
    # Display date and welcome message
    current_date = datetime.now().strftime("%B %d, %Y")
    st.markdown(f"### Today: {current_date}")
    st.markdown(f"### Welcome back, {st.session_state.username}!")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Products", value="10+")
    
    with col2:
        st.metric(label="Customer Feedback", value="Coming Soon")
    
    with col3:
        st.metric(label="User Role", value=st.session_state.role.capitalize() if st.session_state.role else "Guest")
    
    # Quick links
    st.markdown("### Quick Links")
    quick_col1, quick_col2 = st.columns(2)
    
    with quick_col1:
        if st.button("Search Products"):
            st.session_state.page = 'products'
            st.rerun()
    
    with quick_col2:
        if st.button("Submit Feedback"):
            st.session_state.page = 'feedback'
            st.rerun()
    
    # Recent products
    st.markdown("### Recent Products")
    products = get_products()[:5]  # Get 5 most recent products
    
    for product in products:
        st.markdown(f"""
        **{product['name']}** - ${product['price']:.2f}  
        {product['description']}  
        Category: {product['category']} | Stock: {product['stock_quantity']}
        """)
        st.markdown("---")

elif st.session_state.page == 'products':
    st.title("Products")
    
    # Search and filter options
    st.markdown("### Search Products")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("Search by name or description")
    
    with col2:
        categories = ["All"] + get_product_categories()
        selected_category = st.selectbox("Category", categories)
    
    # Get filtered products
    filtered_products = get_products(search_term, selected_category if selected_category != "All" else None)
    
    # Display products in a grid
    st.markdown("### Product Catalog")
    
    if not filtered_products:
        st.info("No products found matching your search criteria.")
    else:
        # Display products in rows of 3
        for i in range(0, len(filtered_products), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(filtered_products):
                    product = filtered_products[i + j]
                    with cols[j]:
                        st.markdown(f"#### {product['name']}")
                        st.markdown(f"**Price:** ${product['price']:.2f}")
                        st.markdown(f"**Category:** {product['category']}")
                        st.markdown(f"**Description:** {product['description']}")
                        st.markdown(f"**In Stock:** {product['stock_quantity']}")
                        
                        # Button to leave feedback for this product
                        if st.button(f"Leave Feedback", key=f"feedback_{product['id']}"):
                            st.session_state.selected_product_id = product['id']
                            st.session_state.page = 'feedback'
                            st.rerun()
                        
                        st.markdown("---")

elif st.session_state.page == 'feedback':
    st.title("Customer Feedback")
    
    # Get selected product if any
    selected_product = None
    if 'selected_product_id' in st.session_state:
        selected_product = get_product_by_id(st.session_state.selected_product_id)
    
    with st.form("feedback_form"):
        st.markdown("### Submit Feedback")
        
        customer_name = st.text_input("Your Name")
        customer_email = st.text_input("Your Email")
        
        # Product selection
        if selected_product:
            st.markdown(f"**Selected Product:** {selected_product['name']}")
            product_id = selected_product['id']
        else:
            products = get_products()
            product_options = ["-- Select a product --"] + [f"{p['id']}: {p['name']}" for p in products]
            product_selection = st.selectbox("Product", product_options)
            
            if product_selection == "-- Select a product --":
                product_id = None
            else:
                product_id = int(product_selection.split(":")[0])
        
        # Rating
        rating = st.slider("Rating", 1, 5, 5)
        
        # Comments
        comments = st.text_area("Comments")
        
        submit_button = st.form_submit_button("Submit Feedback")
        
        if submit_button:
            if not customer_name or not customer_email:
                st.error("Please provide your name and email.")
            elif not product_id:
                st.error("Please select a product.")
            else:
                success = submit_feedback(customer_name, customer_email, product_id, rating, comments)
                if success:
                    st.success("Thank you for your feedback!")
                    # Clear selected product
                    if 'selected_product_id' in st.session_state:
                        del st.session_state.selected_product_id
                else:
                    st.error("Failed to submit feedback. Please try again.")

elif st.session_state.page == 'database':
    st.title("Database Explorer")
    
    if st.session_state.role != 'admin':
        st.error("You don't have permission to access the database explorer. Admin privileges required.")
    else:
        # Get the database tables
        tables = get_tables()
        
        # Two tabs for exploring tables and running custom queries
        db_tab1, db_tab2 = st.tabs(["Explore Tables", "Run Custom Queries"])
        
        with db_tab1:
            st.subheader("Database Tables")
            
            # Select a table to explore
            selected_table = st.selectbox("Select a table to explore", tables)
            
            if selected_table:
                # Get table information
                table_info = get_table_info(selected_table)
                
                # Display table stats
                st.markdown(f"**Total Rows:** {table_info['row_count']}")
                
                # Display table schema
                st.markdown("### Table Schema")
                schema_data = []
                for col in table_info['columns']:
                    schema_data.append({
                        "Column ID": col[0],
                        "Name": col[1],
                        "Type": col[2],
                        "NotNull": "✓" if col[3] else "",
                        "Default Value": col[4] if col[4] is not None else "",
                        "Primary Key": "✓" if col[5] else ""
                    })
                
                st.dataframe(pd.DataFrame(schema_data))
                
                # Display sample data
                st.markdown("### Sample Data (First 5 rows)")
                
                # Create a DataFrame from sample data
                if table_info['sample_data']:
                    column_names = [col[1] for col in table_info['columns']]
                    df = pd.DataFrame(table_info['sample_data'], columns=column_names)
                    st.dataframe(df)
                else:
                    st.info("No data in this table.")
                
                # Button to view all data
                if st.button("View All Data"):
                    query_result = execute_query(f"SELECT * FROM {selected_table};")
                    
                    if query_result['success']:
                        st.dataframe(pd.DataFrame(query_result['results']))
                        st.markdown(f"Total rows: {query_result['row_count']}")
                    else:
                        st.error(f"Error executing query: {query_result['error']}")
        
        with db_tab2:
            st.subheader("Run SQL Queries")
            
            # SQL query input
            st.markdown("""
            Enter your SQL query below. Be careful with UPDATE, DELETE, and INSERT operations.
            
            Examples:
            ```sql
            -- Get all products with price > $300
            SELECT * FROM products WHERE price > 300;
            
            -- Count products by category
            SELECT category, COUNT(*) as count FROM products GROUP BY category;
            
            -- Join products and feedback
            SELECT p.name, f.rating, f.comments 
            FROM feedback f 
            JOIN products p ON f.product_id = p.id;
            ```
            """)
            
            query = st.text_area("SQL Query", height=150)
            
            # Run query button
            if st.button("Run Query"):
                if not query:
                    st.error("Please enter a SQL query.")
                else:
                    # Confirm destructive operations
                    if any(op in query.upper() for op in ["UPDATE", "DELETE", "DROP", "TRUNCATE"]):
                        confirm = st.checkbox("I confirm I want to run this query that may modify or delete data")
                        if not confirm:
                            st.warning("Please confirm the operation to proceed with data modification.")
                            st.stop()
                    
                    # Execute the query
                    query_result = execute_query(query)
                    
                    if query_result['success']:
                        if 'results' in query_result:
                            # For SELECT queries
                            if query_result['results']:
                                st.dataframe(pd.DataFrame(query_result['results']))
                            else:
                                st.info("Query executed successfully, but returned no results.")
                            st.markdown(f"Rows returned: {query_result['row_count']}")
                        else:
                            # For non-SELECT queries
                            st.success(f"Query executed successfully. Rows affected: {query_result['row_count']}")
                    else:
                        st.error(f"Error executing query: {query_result['error']}")

# Footer
st.markdown("---")
st.markdown("© 2025 Sales CRM System | Made with Streamlit")