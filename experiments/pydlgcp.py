import os
from google.cloud import billing_v1
import csv
import datetime

# --- Configuration ---
# Set the path to your service account key file
# IMPORTANT: Replace 'path/to/your/service-account-key.json' with the actual path
# Make sure this file is secure and not committed to version control.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/service-account-key.json"

# Region for which you want to retrieve pricing (Jakarta)
JAKARTA_REGION = "asia-southeast2"

# Output CSV file name
OUTPUT_CSV_FILE = "gcp_compute_pricing_jakarta.csv"

# --- API Client Setup ---
client = billing_v1.CloudCatalogClient()

# --- Get Compute Engine Service ID ---
# The Cloud Billing Catalog API requires a service ID to list SKUs.
# We'll iterate through services to find Compute Engine.
compute_engine_service_id = None
for service in client.list_services():
    if service.display_name == "Compute Engine":
        compute_engine_service_id = service.service_id
        print(f"Found Compute Engine Service ID: {compute_engine_service_id}")
        break

if not compute_engine_service_id:
    print("Error: Could not find Compute Engine service ID.")
    exit()

# --- Fetch SKUs for Compute Engine in Jakarta ---
print(f"Fetching SKUs for Compute Engine in {JAKARTA_REGION}...")

# Define the service name for the SKU list request
service_name = f"services/{compute_engine_service_id}"

# Prepare data for CSV
pricing_data = []
# Add header row
pricing_data.append([
    "SKU ID",
    "SKU Description",
    "Resource Family",
    "Resource Group",
    "Usage Type",
    "Service Regions",
    "Unit",
    "Price per Unit (USD)",
    "Start Time",
    "End Time",
    "Effective Time"
])

try:
    # Iterate through SKUs, filtering by service and region
    # The list_skus method might return many SKUs, so we use pagination.
    request = billing_v1.ListSkusRequest(
        parent=service_name,
        # Filter to include only SKUs available in the Jakarta region
        # The filter string format is important: "serviceRegions=asia-southeast2"
        filter=f"serviceRegions={JAKARTA_REGION}"
    )

    for sku in client.list_skus(request=request):
        # The pricingInfo field is a list, typically containing one or more pricing periods.
        # We'll take the latest pricing information if multiple are present.
        if sku.pricing_info:
            # Sort pricing info by effective_time to get the latest
            sorted_pricing_info = sorted(
                sku.pricing_info, key=lambda x: x.effective_time, reverse=True
            )
            latest_pricing = sorted_pricing_info[0]

            # Extract pricing details
            unit = latest_pricing.pricing_expression.usage_unit
            currency = latest_pricing.pricing_expression.display_quantity.currency_code
            # The "unit_price" is a list of components if there are tiers.
            # For simplicity, we'll take the first tier's price.
            # If your tools need tier-based pricing, you'll need to iterate through latest_pricing.tiered_rates
            price = latest_pricing.pricing_expression.tiered_rates[0].unit_price.units + \
                    latest_pricing.pricing_expression.tiered_rates[0].unit_price.nanos / 1e9

            # Get resource family, group, and usage type from category
            resource_family = sku.category.resource_family or "N/A"
            resource_group = sku.category.resource_group or "N/A"
            usage_type = sku.category.usage_type or "N/A"

            pricing_data.append([
                sku.sku_id,
                sku.description,
                resource_family,
                resource_group,
                usage_type,
                ", ".join(sku.service_regions),
                unit,
                f"{price:.9f} {currency}", # Format price for readability
                latest_pricing.usage_start_time.isoformat() if latest_pricing.usage_start_time else "N/A",
                latest_pricing.usage_end_time.isoformat() if latest_pricing.usage_end_time else "N/A",
                latest_pricing.effective_time.isoformat() if latest_pricing.effective_time else "N/A"
            ])
        else:
            # SKU with no pricing info
            pricing_data.append([
                sku.sku_id,
                sku.description,
                sku.category.resource_family or "N/A",
                sku.category.resource_group or "N/A",
                sku.category.usage_type or "N/A",
                ", ".join(sku.service_regions),
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A"
            ])

except Exception as e:
    print(f"An error occurred: {e}")
    exit()

# --- Write to CSV ---
try:
    with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(pricing_data)
    print(f"Successfully exported pricing data to {OUTPUT_CSV_FILE}")
except IOError as e:
    print(f"Error writing to CSV file: {e}")