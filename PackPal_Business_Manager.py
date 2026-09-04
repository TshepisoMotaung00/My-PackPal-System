import pandas as pd
from datetime import datetime, date
import calendar
import os
import warnings
# Hide pandas FutureWarning to keep PackPal menu clean for customers
warnings.simplefilter(action='ignore', category=FutureWarning)
 
# ========== FILES ==========
ORDERS_FILE = "PackPal_orders.csv"
PRODUCTS_FILE = "PackPal_products.csv"
SALES_FILE = "PackPal_sales.csv"
 
# ========== INIT ==========
def init_data():
    if not os.path.exists(PRODUCTS_FILE):
        print("Creating new products file...")
        data = [
            ["Lunch Bag", "Black", 160, 60, 3],
            ["Lunch Bag", "Brown", 160, 60, 3],
            ["Lunch Bag", "Blue", 160, 60, 3],
            ["Lunch Bag", "Grey", 160, 60, 3],
            ["Flask Bottle", "Grey", 100, 36, 3],
            ["Flask Bottle", "Gold", 100, 36, 3],
            ["Flask Bottle", "Maroon", 100, 36, 3],
            ["Flask Bottle", "Blue", 100, 36, 3],
        ]
        df = pd.DataFrame(data, columns=["product_name", "color", "price", "cost_price", "stock"])
        df.to_csv(PRODUCTS_FILE, index=False)
 
    if not os.path.exists(SALES_FILE):
        pd.DataFrame(columns=["sale_date","customer_name","customer_contact","customer_location","product_name","color","quantity_sold","total_amount","amount_paid","amount_owed","payment_status","due_date"]).to_csv(SALES_FILE, index=False)
 
    if not os.path.exists(ORDERS_FILE):
        pd.DataFrame(columns=["order_date","customer_name","customer_contact","customer_location","product_name","color","quantity","total_amount","amount_paid","status","delivery_date"]).to_csv(ORDERS_FILE, index=False)
 
def load_products(): return pd.read_csv(PRODUCTS_FILE)
def load_sales(): return pd.read_csv(SALES_FILE)
def load_orders(): return pd.read_csv(ORDERS_FILE) if os.path.exists(ORDERS_FILE) else pd.DataFrame()
def save_products(df): df.to_csv(PRODUCTS_FILE, index=False)
def save_sales(df): df.to_csv(SALES_FILE, index=False)
def save_orders(df): df.to_csv(ORDERS_FILE, index=False)
 
def get_month_end():
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return f"{today.year}-{today.month:02d}-{last_day}"
 
# ========== STOCK ==========
def view_stock():
    df = load_products()
    print("\n----------- STOCK SUMMARY -----------")
    summary = df.groupby("product_name").agg({"price":"first", "stock":"sum"}).reset_index()
    for _, row in summary.iterrows():
        print(f"{row['product_name']} | Price: R{row['price']:.2f} | Total Stock: {row['stock']}")
    print("\n----------- DETAILED -----------")
    for _, row in df.iterrows():
        low = " LOW!" if row['stock'] < 3 else ""
        print(f"{row['product_name']} - {row['color']}: {row['stock']}{low}")
 
# ========== ORDERS ==========
def place_order():
    print("\n--- PLACE ORDER (On The Road) ---")
    df_orders = load_orders()
    df_products = load_products()
    customer = input("Customer name: ").strip()
    contact = input("Customer contact: ").strip()
    location = input("Customer location: ").strip()
    product = input("Product (Flask Bottle / Lunch Bag): ").strip()
    color = input("Color: ").strip()
    try:
        qty = int(input("Quantity: ").strip())
        paid = float(input("Deposit paid (0 if none): R").strip() or 0)
    except:
        print("ERROR: Numbers only"); return
    mask = (df_products['product_name'].str.lower() == product.lower()) & (df_products['color'].str.lower() == color.lower())
    price = float(df_products.loc[mask, 'price'].values[0]) if mask.any() else 160.0
    total = price * qty
    new_order = {"order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"customer_name": customer, "customer_contact": contact, "customer_location": location,"product_name": product, "color": color, "quantity": qty,"total_amount": total, "amount_paid": paid, "status": "Pending", "delivery_date": ""}
    df_orders.loc[len(df_orders)] = new_order
    save_orders(df_orders)
    print(f"\n✅ ORDER SAVED: {qty}x {product}-{color} for {customer} - R{total} (Deposit R{paid})")
 
def view_orders():
    df = load_orders()
    if df.empty:
        print("\nNo orders yet"); return
    pending = df[df['status']=="Pending"]
    if pending.empty:
        print("\nNo PENDING orders - all delivered!"); return
    print("\n--- PENDING ORDERS TO DELIVER ---")
    print(pending.to_string(index=True))
 
def deliver_order():
    df_orders = load_orders()
    df_products = load_products()
    df_sales = load_sales()
    view_orders()
    if df_orders.empty: return
    try:
        idx = int(input("\nEnter order number (Index) to deliver: ").strip())
    except:
        print("Enter number"); return
    if idx not in df_orders.index or df_orders.loc[idx, 'status']!= "Pending":
        print("Invalid order"); return
    order = df_orders.loc[idx]
    mask = (df_products['product_name'].str.lower() == order['product_name'].lower()) & (df_products['color'].str.lower() == order['color'].lower())
    if mask.any():
        stock = int(df_products.loc[mask, 'stock'].values[0])
        if stock < int(order['quantity']):
            print(f"❌ Not enough stock! You have {stock}, need {order['quantity']}."); return
        df_products.loc[mask, 'stock'] -= int(order['quantity'])
        save_products(df_products)
    owed = float(order['total_amount']) - float(order['amount_paid'])
    new_sale = {"sale_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"customer_name": order['customer_name'], "customer_contact": order['customer_contact'],"customer_location": order['customer_location'], "product_name": order['product_name'],"color": order['color'], "quantity_sold": order['quantity'],"total_amount": order['total_amount'], "amount_paid": order['amount_paid'],"amount_owed": max(0, owed), "payment_status": "Paid" if owed<=0 else "Credit","due_date": "" if owed<=0 else get_month_end()}
    df_sales.loc[len(df_sales)] = new_sale
    save_sales(df_sales)
    df_orders.loc[idx, 'status'] = "Delivered"
    df_orders.loc[idx, 'delivery_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_orders(df_orders)
    print(f"\n✅ DELIVERED! Moved to Sales. {order['customer_name']}")
 
# ========== SALES ==========
def generate_receipt_file(product, color, qty, price, total, paid, owed, status, sale_date, customer="Walk-in"):
    safe_product = product.replace(" ", "_")
    filename = f"receipt_{safe_product}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("===================================\n")
        f.write("PACKPAL - OFFICIAL RECEIPT\n")
        f.write(f"Date: {sale_date}\n")
        f.write(f"Customer: {customer}\n")
        f.write("===================================\n")
        f.write(f"Product: {product} - {color}\n")
        f.write(f"Quantity: {qty}\n")
        f.write(f"Unit Price: R{price:.2f}\n")
        f.write("-----------------------------------\n")
        f.write(f"TOTAL: R{total:.2f}\n")
        f.write(f"Amount Paid: R{paid:.2f}\n")
        f.write(f"Amount_owed: R{owed:.2f}\n")
        f.write(f"Status: {status}\n")
        if status == "Credit":
            f.write(f"Due Date: {get_month_end()}\n")
        f.write("===================================\n")
        f.write("Thank you for supporting PackPal!\n")
    print(f"\n✅ DONE! Official Receipt: {filename}")
    return filename
 
def make_sale():
    print("\n--- RECORD SALE ---")
    df_products = load_products(); df_sales = load_sales()
    customer = input("Customer name: ").strip()
    contact = input("Customer contact: ").strip()
    location = input("Customer location: ").strip()
    product = input("Product name (Flask Bottle / Lunch Bag): ").strip()
    color = input("Color: ").strip()
    try:
        qty = int(input("Quantity: ").strip())
        paid = float(input("Amount paid: R").strip())
    except:
        print("ERROR: Numbers only"); return
    mask = (df_products['product_name'].str.lower() == product.lower()) & (df_products['color'].str.lower() == color.lower())
    if not mask.any():
        print(f"Not found: {product} - {color}"); return
    stock = int(df_products.loc[mask, 'stock'].values[0]); price = float(df_products.loc[mask, 'price'].values[0])
    if stock < qty:
        print(f"Not enough stock. Available: {stock}"); return
    df_products.loc[mask, 'stock'] -= qty; save_products(df_products)
    total = price * qty; owed = total - paid; status = "Paid" if owed <= 0.01 else "Credit"; due = "" if owed <=0.01 else get_month_end()
    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_sale = {"sale_date": sale_date, "customer_name": customer, "customer_contact": contact,"customer_location": location, "product_name": df_products.loc[mask, 'product_name'].values[0],"color": df_products.loc[mask, 'color'].values[0],"quantity_sold": qty, "total_amount": total, "amount_paid": paid,"amount_owed": max(0, owed), "payment_status": status, "due_date": due}
    df_sales.loc[len(df_sales)] = new_sale; save_sales(df_sales)
    print(f"\nSOLD: {qty}x {new_sale['product_name']}-{new_sale['color']} to {customer}")
    generate_receipt_file(new_sale['product_name'], new_sale['color'], qty, price, total, paid, max(0,owed), status, sale_date, customer)
 
def sales_report():
    df_sales = load_sales(); df_products = load_products()
    print("\n=========== SALES & PROFIT REPORT ===========")
    if df_sales.empty:
        print("No sales yet"); return
    merged = pd.merge(df_sales, df_products[['product_name','color','cost_price']], on=['product_name','color'], how='left')
    merged['profit'] = merged['total_amount'] - (merged['cost_price'] * merged['quantity_sold'])
    for _, r in merged.iterrows():
        print(f"{r['sale_date']} | {r['customer_name']} - {r['product_name']} {r['color']} x{r['quantity_sold']} | R{r['total_amount']:.2f} Profit: R{r['profit']:.2f} {r['payment_status']}")
    print(f"\nTOTAL SALES: R{merged['total_amount'].sum():.2f}")
    print(f"TOTAL PROFIT: R{merged['profit'].sum():.2f}")
 
# ========== MENU ==========
def show_menu():
    print("\n--- PACKPAL PRO ---")
    print("1. View Stock")
    print("2. Record Sale")
    print("3. Place Order (Low Stock)")
    print("4. View Pending Orders")
    print("5. Deliver Order")
    print("6. Sales Report")
    print("7. Exit")
    return input("\nChoose (1-7): ").strip()
    
# =========== MAIN ===========
init_data()
while True:
    choice = show_menu()
   
    if choice == "1":
        view_stock()
    elif choice == "2":
        make_sale()
    elif choice == "3":
        place_order()
    elif choice == "4":
        view_orders()
    elif choice == "5":
        deliver_order()
    elif choice == "6":
        sales_report()
    elif choice == "7":
        print("Bye! PackPal Closed.")
        break
    else:
        print("Invalid choice, try 1-7")
