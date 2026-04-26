import csv
import random

# Sample TX ZIP codes (20 ZIPs)
sample_texas_zips = [
    "75001","75006","75007","75019","75038",
    "75039","75040","75041","75042","75043",
    "75044","75048","75050","75051","75052",
    "75054","75056","75057","75058","75060"
]


service_types = ["Unarmed Guard", "Armed Guard", "Executive Protection"]

output_csv = "texas_sample_pricing.csv"

with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["zip_code", "state_code", "service_type", "avg_price", "min_price", "max_price"])

    for zip_code in sample_texas_zips:
        for st_name in service_types:
            if st_name == "Unarmed Guard":
                min_price = random.uniform(18, 25)
            elif st_name == "Armed Guard":
                min_price = random.uniform(28, 40)
            else:
                min_price = random.uniform(50, 100)

            max_price = min_price + random.uniform(5, 20)
            avg_price = (min_price + max_price) / 2

            writer.writerow([
                zip_code,
                "TX",
                st_name,
                round(avg_price, 2),
                round(min_price, 2),
                round(max_price, 2)
            ])

print(f"Sample Texas pricing CSV generated: {output_csv}")