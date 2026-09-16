"""Role-based staff navigation.

Links are shown in the sidebar according to staff.role.
Routes are still protected with @role_required — hiding a link is not security.
"""

ALL_ROLES = ("ADMIN", "OPERATOR", "AUCTION_CLERK", "FINANCE", "VIEWER")
RECORD_ROLES = ("ADMIN", "OPERATOR")
TRADE_ROLES = ("ADMIN", "AUCTION_CLERK")
FINANCE_ROLES = ("ADMIN", "FINANCE")

# endpoint, label, Bootstrap icon, roles that may see the link, optional prefix for "active"
NAV_ITEMS = (
    {
        "endpoint": "dashboard.index",
        "label": "Dashboard",
        "icon": "bi-speedometer2",
        "roles": ALL_ROLES,
        "section": None,
    },
    {
        "endpoint": "farmers.index",
        "label": "Farmers",
        "icon": "bi-flower2",
        "roles": RECORD_ROLES,
        "prefix": "farmers.",
        "section": "Records",
    },
    {
        "endpoint": "buyers.index",
        "label": "Buyers",
        "icon": "bi-cart3",
        "roles": RECORD_ROLES,
        "prefix": "buyers.",
        "section": "Records",
    },
    {
        "endpoint": "produce.index",
        "label": "Produce",
        "icon": "bi-basket",
        "roles": RECORD_ROLES,
        "prefix": "produce.",
        "section": "Records",
    },
    {
        "endpoint": "grades.index",
        "label": "Grades",
        "icon": "bi-award",
        "roles": ("ADMIN",),
        "prefix": "grades.",
        "section": "Records",
    },
    {
        "endpoint": "depots.index",
        "label": "Depots",
        "icon": "bi-geo-alt",
        "roles": RECORD_ROLES,
        "prefix": "depots.",
        "section": "Records",
    },
    {
        "endpoint": "lots.index",
        "label": "Lots",
        "icon": "bi-box-seam",
        "roles": ("ADMIN", "OPERATOR", "AUCTION_CLERK"),
        "prefix": "lots.",
        "section": "Trading",
    },
    {
        "endpoint": "auctions.index",
        "label": "Auctions",
        "icon": "bi-hammer",
        "roles": TRADE_ROLES,
        "prefix": "auctions.",
        "section": "Trading",
    },
    {
        "endpoint": "bids.index",
        "label": "Bids",
        "icon": "bi-tag",
        "roles": TRADE_ROLES,
        "prefix": "bids.",
        "section": "Trading",
    },
    {
        "endpoint": "sales.index",
        "label": "Sales",
        "icon": "bi-receipt",
        "roles": ("ADMIN", "AUCTION_CLERK", "FINANCE"),
        "prefix": "sales.",
        "section": "Trading",
    },
    {
        "endpoint": "payments.index",
        "label": "Payments",
        "icon": "bi-credit-card",
        "roles": FINANCE_ROLES,
        "prefix": "payments.",
        "section": "Finance",
    },
    {
        "endpoint": "collections.index",
        "label": "Collections",
        "icon": "bi-truck",
        "roles": ("ADMIN", "FINANCE"),
        "prefix": "collections.",
        "section": "Finance",
    },
    {
        "endpoint": "reports.index",
        "label": "Reports",
        "icon": "bi-bar-chart",
        "roles": ("ADMIN", "FINANCE", "VIEWER"),
        "prefix": "reports.",
        "section": "Finance",
    },
    {
        "endpoint": "staff.index",
        "label": "Staff",
        "icon": "bi-people",
        "roles": ("ADMIN",),
        "prefix": "staff.",
        "section": "System",
    },
    {
        "endpoint": "dashboard.administration",
        "label": "Administration",
        "icon": "bi-database",
        "roles": ("ADMIN",),
        "section": "System",
    },
)


def items_for_role(role):
    """Nav entries visible to this staff role, grouped for the sidebar."""
    if not role:
        return []
    visible = [item for item in NAV_ITEMS if role in item["roles"]]
    grouped = []
    current_section = object()
    bucket = None
    for item in visible:
        section = item.get("section")
        if section != current_section:
            current_section = section
            bucket = {"section": section, "links": []}
            grouped.append(bucket)
        bucket["links"].append(item)
    return grouped
