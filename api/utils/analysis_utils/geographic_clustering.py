import numpy as np
from sklearn.cluster import DBSCAN
from companies.models import Company, Store, StoreGroup, StoreGroupMembership

def create_geographic_clusters():
    """
    Finds geographic clusters of stores for each company using DBSCAN
    and saves the results to the database.
    """
    # Clear out all existing group data for a clean run
    StoreGroupMembership.objects.all().delete()
    StoreGroup.objects.all().delete()
    print("Cleared all existing store group data.")

    # --- DBSCAN Parameters ---
    # The maximum distance (in kilometers) between two stores to be considered neighbors.
    eps_km = 25 
    # The minimum number of stores required to form a dense region (a cluster).
    min_samples = 3

    # Convert eps from kilometers to radians for use with haversine metric
    kms_per_radian = 6371.0088
    epsilon = eps_km / kms_per_radian

    # Process each company separately
    for company in Company.objects.all():
        print(f"\nProcessing {company.name}...")

        # Get all active stores for the company with valid coordinates
        stores = list(Store.objects.filter(
            company=company, 
            is_active=True, 
            latitude__isnull=False, 
            longitude__isnull=False
        ))

        if len(stores) < min_samples:
            print(f"Skipping {company.name}, not enough stores ({len(stores)}) to form clusters.")
            continue

        # Prepare coordinate data for DBSCAN
        coords = np.array([[float(s.latitude), float(s.longitude)] for s in stores])
        
        # Run DBSCAN
        db = DBSCAN(
            eps=epsilon, 
            min_samples=min_samples, 
            algorithm='ball_tree', 
            metric='haversine'
        ).fit(np.radians(coords))

        labels = db.labels_

        # Get the unique cluster labels found (excluding -1, which is noise/outliers)
        unique_labels = set(labels) - {-1}

        # --- Save results to the database ---

        # 1. Create StoreGroup objects for each cluster found
        for label in unique_labels:
            group_name = f"{company.name.lower()}-cluster-{label}"
            StoreGroup.objects.create(name=group_name, company=company)
            print(f"  Created group: {group_name}")

        # 2. Create StoreGroupMembership for each store in a cluster
        for i, store in enumerate(stores):
            label = labels[i]
            if label != -1:
                group = StoreGroup.objects.get(name=f"{company.name.lower()}-cluster-{label}")
                StoreGroupMembership.objects.create(store=store, group=group)

        # 3. Report results
        num_outliers = np.sum(labels == -1)
        print(f"  Result: Found {len(unique_labels)} clusters and {num_outliers} outliers.")

    return True
