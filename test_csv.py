import pandas as pd
import os

# CSV file ka naam
CSV_FILE = "creditcard.csv"

print("=" * 50)
print("CREDIT CARD FRAUD DATASET TEST")
print("=" * 50)

# Check whether CSV exists
if not os.path.exists(CSV_FILE):
    print("❌ ERROR: creditcard.csv nahi mili.")
    print("Make sure CSV project folder ke andar hai.")
    exit()

print("✅ CSV file mil gayi.")

try:
    # CSV read karna
    df = pd.read_csv(CSV_FILE)

    print("✅ CSV successfully loaded!")
    print()

    # Basic information
    print("Number of transactions:", len(df))
    print("Number of columns:", len(df.columns))

    print()
    print("Columns:")
    print(df.columns.tolist())

    print()
    print("First 5 rows:")
    print(df.head())

    print()
    print("Dataset information:")
    print(df.info())

    # Check Class column
    if "Class" in df.columns:

        print()
        print("Fraud/Normal transaction count:")

        print(df["Class"].value_counts())

        print()
        print("Class meaning:")
        print("0 = Normal transaction")
        print("1 = Fraud transaction")

        print()
        print("Fraud transactions:",
              int((df["Class"] == 1).sum()))

        print("Normal transactions:",
              int((df["Class"] == 0).sum()))

        print()
        print("✅ DATASET IS READY!")

    else:
        print()
        print("❌ ERROR: 'Class' column nahi mili.")

except Exception as e:
    print()
    print("❌ CSV READ ERROR:")
    print(e)