import csv
import random

input_csv = "zip_state_list.csv"
output_csv = "us_pricing.csv"

service_types = ["Unarmed Guard", "Armed Guard", "Executive Protection"]

with open(input_csv, "r", newline="", encoding="latin-1") as infile, open(output_csv, "w", newline="") as outfile:
    reader = csv.reader(infile)
    next(reader)  # skip header line ("PHYSICAL STATE,PHYSICAL ZIP")

    writer = csv.writer(outfile)
    writer.writerow(["zip_code", "state_code", "service_type", "avg_price", "min_price", "max_price"])

    for row in reader:
        if not row or len(row) < 2:
            continue
        state_code = row[0].strip()
        zip_code = row[1].strip()

        for st_name in service_types:
            if st_name == "Unarmed Guard":
                min_price = random.uniform(18, 20)
            elif st_name == "Armed Guard":
                min_price = random.uniform(21, 40)
            else:
                min_price = random.uniform(40, 60)

            max_price = min_price + random.uniform(5, 50)
            avg_price = (min_price + max_price) / 2

            writer.writerow([
                zip_code,
                state_code,
                st_name,
                round(avg_price, 2),
                round(min_price, 2),
                round(max_price, 2)
            ])

print(f"Pricing CSV generated: {output_csv}")