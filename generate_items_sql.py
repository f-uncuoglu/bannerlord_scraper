import pandas as pd

# Read your items CSV
items_df = pd.read_csv('items/items.csv')

# Create Item_Types inserts
print("-- Item Types")
print("INSERT INTO Item_Types (item_type_id, item_type) VALUES")
print("  (1, 'melee_weapons'),")
print("  (2, 'ranged_weapons'),")
print("  (3, 'armors'),")
print("  (4, 'shields'),")
print("  (5, 'horses');")
print()

# Create Items inserts
print("-- Items")
print("INSERT INTO Items (item_id, item_type_id, culture_id, name) VALUES")

item_inserts = []
for _, row in items_df.iterrows():
    item_id = int(row['Item_ID'])
    item_type_id = int(row['Item_Type_ID']) if pd.notna(row['Item_Type_ID']) else 'NULL'
    culture_id = int(row['Culture_ID']) if pd.notna(row['Culture_ID']) else 'NULL'
    name = str(row['Item_Name']).replace("'", "''")
    
    item_inserts.append(f"  ({item_id}, {item_type_id}, {culture_id}, '{name}')")

print(",\n".join(item_inserts) + ";")

# use python generate_items_sql.py > items.sql to generate the SQL file