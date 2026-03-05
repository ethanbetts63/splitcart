# Store Grouping

Supermarkets like Coles, Aldi and Woolworths generally price nationally — every store charges the same. Scraping and storing a separate `Price` row for each physical location would be massively redundant. The grouping system detects this and deduplicates: once stores are confirmed to have matching prices, only the **anchor** store retains `Price` rows. All other members have their prices deleted. In this way companies like IGA, or one offs like Coles Metro, will have full data fidelity but the vast majority of duplication is removed. 

For two groups to be merged their anchors need to have 98% of their product range be the same products at the same price. The 2% is more often than not a data gathering issue anyway so its more than acceptable data loss for the massive reduction in database size and faster db queries. 

---

## Key Terms

- **Group** — a set of stores confirmed to share identical prices
- **Anchor** — the single store per group that retains `Price` rows; the source of truth for the group
- **Member** — any non-anchor store in a group; has no `Price` rows of its own
---

## Lifecycle

```
python manage.py cluster_stores
  └─ Deletes all StoreGroups
  └─ Creates one StoreGroup per Store, each store as its own anchor

        ▼  (runs at end of every update --products)

GroupMaintenanceOrchestrator
  │
  ├─ Phase 1: Internal Health Checks  (existing multi-member groups)
  │    ├─ Skip group if anchor has no current pricing (flag anchor for re-scrape)
  │    ├─ Compare each member's prices against the anchor
  │    │    ├─ Match  → delete member's Price rows (now redundant), cache result 7 days
  │    │    └─ No match → eject member into its own new group
  │    └─ (stale non-matches skip comparison, cached 7 days)
  │
  └─ Phase 2: Inter-Group Merging  (find new matches across groups)
       ├─ Compare every anchor against every other anchor (in same company)
       ├─ Match → merge smaller group into larger; delete all Price rows for merged stores
       └─ No match → cache non-match 7 days, skip on next run
```

The whole system becomes improves with each life cycle. The end state is that supermarkets with generally national pricing converge to 1 or 2 main groups and a couple outliers. And supermarkets with store by store pricing see very little convergance.
---

## Querying Prices Correctly

Because member stores have no `Price` rows, any query for "prices at these stores" must first resolve member IDs to their anchor IDs. This is handled in two ways:

**In views** (`ProductListView`, `BargainCarouselView`) — raw `store_ids` from the frontend are resolved once at the start of the request using `get_pricing_stores_map()`, then `anchor_store_ids` is used for all ORM queries. The frontend passes `selectedStoreIds` directly and never needs to know about anchors.

**In utility methods** — use the `Price` manager:

```python
Price.objects.for_stores(store_ids)
```

`for_stores()` calls `get_pricing_stores_map()` internally, which walks each store's `StoreGroupMembership` to find its anchor. The result is cached for 1 hour per company.

**Never filter prices directly by raw store IDs** — member stores will return nothing.


**Additional thoughts** — 
The 98% rule is completely arbitrary. I picked it after playing around with the values and seeing the results but over time more thorough analysis is needed. For example if a company runs a set of sales on less than 2% of their products that would not be caught by our system. A real concern. My current justification is that the 98% rule is simple, database size conservative and becuase we ensure no partial scrapes make it to the database, reasonably accurate.  

This system does not support historical pricing (other than a was_price). This project began with full historical pricing on products but I found that it is essentially irrelvant to the user, it takes up the vast majority of db space, and of course slows down queries. Therefor this is an intentional limitation in the grouping design. 
---

## Related Files

- `products/models/price.py` — `PriceQuerySet.for_stores()`
- `products/utils/get_pricing_stores.py` — anchor resolution + 1-hour cache
- `companies/models/store_group.py`
- `companies/models/store_group_membership.py`
- `data_management/database_updating_classes/group_maintenance_orchestrator.py`
- `data_management/database_updating_classes/internal_group_health_checker.py`
- `data_management/database_updating_classes/intergroup_comparer.py`
