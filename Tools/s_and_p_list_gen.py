import pandas as pd
import json

table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
df = table[0]

# Create a list of dictionaries
stock_data = df[['Symbol', 'Security']].to_dict('records')

# Determine the midpoint
midpoint = len(stock_data) // 2

# Split the list into two halves
first_half = stock_data[:midpoint]
second_half = stock_data[midpoint:]

# Convert the lists of dictionaries to strings with line breaks
first_half_str = 'stock_data = ' + json.dumps(first_half, indent=4)
second_half_str = 'stock_data = ' + json.dumps(second_half, indent=4)

# Write the strings to Python files
with open('s_and_p_first_half.py', 'w') as f:
    f.write(first_half_str)

with open('s_and_p_second_half.py', 'w') as f:
    f.write(second_half_str)
