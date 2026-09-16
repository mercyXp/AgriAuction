# AgriAuction Normalization

This document explains why the AgriAuction schema in `database/schema.sql` is in **Third Normal Form (3NF)**. It is written for an IT212 defence: each normal form is defined, an unnormalized mistake is shown, and then the actual tables are checked.

A **functional dependency** `X → Y` means: if two rows have the same value of `X`, they must have the same value of `Y`.

---

## 1. First Normal Form (1NF)

A relation is in 1NF when:

1. Every intersection of a row and a column holds **one atomic value**.
2. There are **no repeating groups** (no “bid1, bid2, bid3” columns).
3. Every row is **unique** (a primary key exists).

### What we avoided

An unnormalized “lot sheet” might look like this:

| lot_number | farmer | produce | bids |
|---|---|---|---|
| LOT-0001 | Mutale, Chipata, 0977... | Maize, Grade A, 12.5 tonnes | Bwalya 4500; Phiri 4800; Zimba 4800 |

Problems:

- `farmer` mixes name, town and phone in one cell (**not atomic**).
- `produce` mixes type, grade and quantity (**not atomic**).
- `bids` stores several bids in one cell (**repeating group**).

### How AgriAuction satisfies 1NF

Each fact has its own column and, where there can be many facts, its own table.

| Fact | Where it lives |
|---|---|
| One farmer’s phone | `farmers.phone` |
| One lot quantity | `produce_lots.quantity` |
| One bid | one row in `bids` |
| One payment | one row in `payments` |

Every table has a primary key (`staff_id`, `farmer_id`, `lot_id`, `bid_id`, and so on), so rows are unique.

`ENUM` columns such as `produce_lots.status` still hold **one** value (`OPEN` or `SOLD`), not a list. That is atomic.

**Conclusion:** all eleven tables are in 1NF.

---

## 2. Second Normal Form (2NF)

A relation is in 2NF when:

1. It is already in 1NF.
2. Every non-key attribute is **fully functionally dependent** on the **whole** primary key.
3. There is **no partial dependency**.

A partial dependency can only appear when the primary key is **composite** (two or more columns). If `A` is only part of the key and `A → B`, then `B` is a partial dependency.

### What we avoided

A poorly keyed bid table:

```text
PRIMARY KEY (lot_id, buyer_id)

lot_id, buyer_id  →  bid_amount, bid_time
buyer_id          →  business_name, phone     ← partial dependency
lot_id            →  lot_number, minimum_bid_price  ← partial dependency
```

`business_name` would be copied onto every bid by that buyer. If the company changed its name, many bid rows would have to be updated. That is a 2NF failure.

### How AgriAuction satisfies 2NF

Every table uses a **single-column surrogate primary key**. Non-key attributes therefore depend on the whole key, because the key has only one column.

Example:

```text
bid_id → lot_id, buyer_id, bid_amount, bid_time, status, created_at
```

Buyer details are stored once in `buyers` and referenced by `buyer_id`. Lot details are stored once in `produce_lots` and referenced by `lot_id`.

### Candidate keys (not extra partial keys)

Some tables also have a unique business code. That code is an **alternate key**, not a second part of a composite PK.

```text
farmer_id   → farmer_code, first_name, last_name, phone, ...
farmer_code → farmer_id, first_name, last_name, phone, ...
```

The same pattern applies to `username` / `email` on `staff`, `buyer_code` on `buyers`, `lot_number` on `produce_lots`, and `sale_reference` on `successful_sales`. Each of those unique attributes determines the whole row. That is still full dependency, not partial dependency.

**Conclusion:** all eleven tables are in 2NF.

---

## 3. Third Normal Form (3NF)

A relation is in 3NF when:

1. It is already in 2NF.
2. There is **no transitive dependency** of a non-key attribute on the primary key.

A transitive dependency looks like:

```text
PK → A
A  → B     (A is not a candidate key)
therefore PK → B through A
```

`B` should then move to a table whose key is `A`.

### What we avoided

If produce lots stored the farmer’s details:

```text
lot_id → farmer_id
farmer_id → first_name, last_name, farm_name, phone
```

Then:

```text
lot_id → first_name, last_name, farm_name, phone
```

would be transitive. Changing a farmer’s phone would require updating every lot they ever registered.

### How lookup tables remove transitivity

AgriAuction stores only the **foreign key** on the lot, and keeps determined attributes in the parent table.

```text
produce_lots.lot_id → farmer_id, produce_type_id, grade_id, depot_id, quantity, ...

farmers.farmer_id                 → first_name, last_name, farm_name, phone, ...
produce_types.produce_type_id     → name, description, unit_of_measure, ...
quality_grades.grade_id           → grade_code, grade_name, description, ...
depots.depot_id                   → depot_code, depot_name, location, capacity, ...
```

To print “Mutale’s maize at Lusaka Depot”, the application **joins**. It does not copy those names onto the lot row.

The same idea applies to:

- `bids.buyer_id` instead of copying `business_name`
- `payments.recorded_by` instead of copying the staff member’s name
- `payments.sale_id` instead of copying `sale_amount` into every payment as the only record of the sale

### `unit_of_measure` on both produce types and lots

`produce_types` has a default unit. `produce_lots` also stores `unit_of_measure`.

This is **not** a 3NF violation. The lot column records the unit **used for that consignment**. If maize later changed its default from `tonne` to `kg`, old lots must still show the unit they were auctioned in. That value is a fact about the lot, not a fact that can only exist on the produce type.

```text
lot_id → unit_of_measure          (unit of this consignment)
produce_type_id → unit_of_measure (default unit of the commodity)
```

Those are two different attributes.

### `buyer_id` on `successful_sales`

A sale stores `winning_bid_id` and also `buyer_id`. The winning bid already has a buyer:

```text
winning_bid_id → buyer_id     (from bids)
```

This looks redundant, but it does **not** break 3NF, because `winning_bid_id` and `lot_id` are **UNIQUE** on `successful_sales`. They are candidate keys.

3NF allows `X → A` when `X` is a candidate key. Here:

```text
sale_id         → buyer_id      (sale_id is the primary key)
winning_bid_id  → buyer_id      (winning_bid_id is unique, so a candidate key)
lot_id          → buyer_id      (lot_id is unique, so a candidate key)
```

The extra `buyer_id` column is **controlled redundancy** so reports can read the winner without always joining `bids`. The foreign key still requires that buyer to exist. Application logic (later phases) must keep it equal to the winning bid’s buyer.

**Conclusion:** the schema is in 3NF.

---

## 4. Functional dependencies by table

Timestamps (`created_at`, `updated_at`) depend on the primary key in every table. They are omitted below to keep the lists readable.

### staff

```text
staff_id      → username, email, password_hash, first_name, last_name, role, is_active
username      → staff_id, email, password_hash, first_name, last_name, role, is_active
email         → staff_id, username, password_hash, first_name, last_name, role, is_active
```

`username` and `email` are unique, so each is a candidate key.

### farmers

```text
farmer_id    → farmer_code, first_name, last_name, phone, email, address,
               farm_name, registration_date, is_active
farmer_code  → farmer_id, first_name, last_name, phone, email, address,
               farm_name, registration_date, is_active
```

### buyers

```text
buyer_id    → buyer_code, business_name, contact_person, phone, email, address,
              registration_date, is_active
buyer_code  → buyer_id, business_name, contact_person, phone, email, address,
              registration_date, is_active
```

`business_name` is **not** a key. Two companies could theoretically share a similar trading name; the unique business identity is `buyer_id` / `buyer_code`.

### produce_types

```text
produce_type_id → name, description, unit_of_measure, is_active
name            → produce_type_id, description, unit_of_measure, is_active
```

### quality_grades

```text
grade_id    → grade_code, grade_name, description, is_active
grade_code  → grade_id, grade_name, description, is_active
```

### depots

```text
depot_id    → depot_code, depot_name, location, capacity, is_active
depot_code  → depot_id, depot_name, location, capacity, is_active
```

`location` does not determine `depot_name`. Lusaka can have more than one depot.

### produce_lots

```text
lot_id      → lot_number, farmer_id, produce_type_id, grade_id, depot_id,
              quantity, unit_of_measure, inspection_date, auction_start,
              auction_end, minimum_bid_price, status
lot_number  → lot_id, farmer_id, produce_type_id, grade_id, depot_id,
              quantity, unit_of_measure, inspection_date, auction_start,
              auction_end, minimum_bid_price, status
```

There is **no** `farmer_id → quantity`. One farmer has many lots with different quantities. That is why lots are a separate table.

### bids

```text
bid_id → lot_id, buyer_id, bid_amount, bid_time, status
```

A buyer may bid more than once on the same lot, so `(lot_id, buyer_id)` is not treated as a unique key. Each offer is its own row.

### successful_sales

```text
sale_id         → sale_reference, lot_id, winning_bid_id, buyer_id,
                  sale_amount, sale_date, status
sale_reference  → sale_id, lot_id, winning_bid_id, buyer_id,
                  sale_amount, sale_date, status
lot_id          → sale_id, sale_reference, winning_bid_id, buyer_id,
                  sale_amount, sale_date, status
winning_bid_id  → sale_id, sale_reference, lot_id, buyer_id,
                  sale_amount, sale_date, status
```

`lot_id` and `winning_bid_id` are unique, so each is a candidate key. That is how the database prevents two sales for one lot.

### payments

```text
payment_id         → sale_id, payment_reference, amount, payment_method,
                     payment_date, status, recorded_by
payment_reference  → payment_id, sale_id, amount, payment_method,
                     payment_date, status, recorded_by
```

`sale_id` does **not** determine `amount`, because one sale can have several payments.

### collections

```text
collection_id          → sale_id, collection_reference, collected_quantity,
                         collection_date, collected_by, notes
collection_reference   → collection_id, sale_id, collected_quantity,
                         collection_date, collected_by, notes
sale_id                → collection_id, collection_reference, collected_quantity,
                         collection_date, collected_by, notes
```

`sale_id` is unique, so a sale has at most one collection row.

---

## 5. Why the final design is 3NF

| Normal form | Test | Result in AgriAuction |
|---|---|---|
| **1NF** | Atomic values, no repeating groups, unique rows | One value per column; many bids/payments are many rows; every table has a PK |
| **2NF** | No partial dependency on part of a composite key | PKs are single columns; related data is in parent tables, not copied onto children |
| **3NF** | No transitive dependency through a non-key attribute | Farmer, buyer, type, grade, depot and staff details live in their own tables and are referenced by foreign keys |

The design was not “normalized because we used foreign keys”. It is in 3NF because:

1. Repeating auction activity was modelled as **separate rows** (`bids`, `payments`).
2. Attributes that belong to another entity were **moved** to that entity (`farmers`, `buyers`, `produce_types`, `quality_grades`, `depots`, `staff`).
3. Remaining attributes on each table depend on that table’s **candidate keys**, not on some other non-key column.

Further business rules (only OPEN lots can be bid on, verified payments cannot exceed the sale amount) are **integrity rules**, not extra normal forms. They will be enforced with CHECK constraints already in the schema, plus later transactions and stored procedures.
