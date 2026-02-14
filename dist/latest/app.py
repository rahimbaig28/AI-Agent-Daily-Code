# Auto-generated via Perplexity on 2026-02-14T07:47:04.538924Z
import json
import datetime
import os
import statistics
import sys
from math import ceil

DATA_FILE = 'debt_forecast.json'
CSV_FILE = 'debt_export.csv'

def get_today():
    return datetime.date.today().isoformat()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f).get('debts', [])
        except:
            pass
    return []

def save_data(debts):
    with open(DATA_FILE, 'w') as f:
        json.dump({'debts': debts}, f, indent=2)

def validate_float(prompt, min_val=0):
    while True:
        try:
            val = float(input(prompt))
            if val >= min_val:
                return val
            print(f"Value must be >= {min_val}")
        except ValueError:
            print("Invalid number")

def add_debt(debts):
    name = input("Debt name: ").strip()
    if not name:
        print("Name required")
        return
    principal = validate_float("Principal: ")
    apr = validate_float("APR (e.g. 0.18 for 18%): ")
    min_payment = validate_float("Minimum payment: ", 0.01)
    
    debt = {
        'name': name,
        'principal': principal,
        'apr': apr,
        'min_payment': min_payment,
        'start_date': get_today()
    }
    debts.append(debt)
    save_data(debts)
    print(f"Added {name}")

def update_payment(debts):
    if not debts:
        print("No debts")
        return
    print("\nDebts:")
    for i, d in enumerate(debts):
        print(f"{i}: {d['name']} - ${d['principal']:.2f}")
    
    try:
        idx = int(input("Select debt (index): "))
        if 0 <= idx < len(debts):
            new_payment = validate_float("New minimum payment: ", 0.01)
            debts[idx]['min_payment'] = new_payment
            save_data(debts)
            print("Updated")
        else:
            print("Invalid index")
    except ValueError:
        print("Invalid input")

def forecast_debt(debt):
    if debt['principal'] <= 0:
        return {'months': 0, 'total_interest': 0, 'payoff_date': debt['start_date']}
    
    principal = debt['principal']
    monthly_rate = debt['apr'] / 12
    payment = debt['min_payment']
    months = 0
    total_interest = 0
    start_date = datetime.date.fromisoformat(debt['start_date'])
    
    while principal > 0 and months < 360:
        # Daily compound interest (approx monthly)
        interest = principal * monthly_rate
        total_interest += interest
        principal += interest
        
        principal_payment = min(payment - interest, principal)
        principal -= principal_payment
        principal = max(0, principal)
        months += 1
    
    payoff_date = (start_date + datetime.timedelta(days=30*months)).isoformat()
    return {'months': months, 'total_interest': total_interest, 'payoff_date': payoff_date}

def print_forecast(debts):
    if not debts:
        print("No debts")
        return
    
    print("\n" + "="*80)
    print(f"{'Name':<20} {'Balance':>10} {'Payment':>10} {'Payoff':>12} {'Interest':>12}")
    print("="*80)
    
    forecasts = []
    for debt in debts:
        forecast = forecast_debt(debt)
        forecasts.append((debt, forecast))
        balance = debt['principal']
        print(f"{debt['name']:<20} ${balance:>9.2f} ${debt['min_payment']:>9.2f} "
              f"{forecast['payoff_date'][:10]:>12} ${forecast['total_interest']:>11.2f}")
    
    return forecasts

def print_summary(debts):
    if not debts:
        print("No debts")
        return
    
    total_debt = sum(d['principal'] for d in debts)
    apr_values = [d['apr'] for d in debts if d['principal'] > 0]
    avg_apr = statistics.mean(apr_values) * 100 if apr_values else 0
    total_payment = sum(d['min_payment'] for d in debts)
    
    print("\nSummary:")
    print(f"Total debt: ${total_debt:,.2f}")
    print(f"Average APR: {avg_apr:.1f}%")
    print(f"Total monthly payment: ${total_payment:,.2f}")
    
    forecasts = []
    for debt in debts:
        forecast = forecast_debt(debt)
        forecasts.append((debt, forecast))
    
    # Sort by payoff time
    forecasts.sort(key=lambda x: x[1]['months'])
    
    print("\nDebts sorted by payoff time:")
    print(f"{'Name':<20} {'Months':>6} {'Payoff':>12}")
    print("-"*45)
    for debt, forecast in forecasts:
        print(f"{debt['name']:<20} {forecast['months']:>6} {forecast['payoff_date'][:10]:>12}")

def export_csv(debts):
    forecasts = print_forecast(debts)  # Also displays forecast
    if not forecasts:
        return
    
    with open(CSV_FILE, 'w') as f:
        f.write("Name,Principal,APR,Min Payment,Est Payoff,Total Interest\n")
        for debt, forecast in forecasts:
            f.write(f"{debt['name']},{debt['principal']:.2f},{debt['apr']:.4f},"
                   f"{debt['min_payment']:.2f},{forecast['payoff_date']},"
                   f"{forecast['total_interest']:.2f}\n")
    print(f"\nExported to {CSV_FILE}")

def main():
    debts = load_data()
    
    while True:
        print("\nDebt Forecaster")
        print("1) Add debt")
        print("2) Update payment")
        print("3) Forecast payoff dates")
        print("4) View summary")
        print("5) Export CSV")
        print("6) Quit")
        
        choice = input("Choose: ").strip()
        
        if choice == '1':
            add_debt(debts)
        elif choice == '2':
            update_payment(debts)
        elif choice == '3':
            print_forecast(debts)
        elif choice == '4':
            print_summary(debts)
        elif choice == '5':
            export_csv(debts)
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()