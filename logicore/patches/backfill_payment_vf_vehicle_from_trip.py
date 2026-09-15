import frappe


def execute():
    """Backfill vf_vehicle (shared Vehicle No column) and trip_vehicle_type on trip-based Payments."""
    frappe.reload_doc("logicore", "doctype", "payment")

    frappe.db.sql("""
        UPDATE `tabPayment` p
        INNER JOIN `tabTrip` t ON t.name = p.trip_no
        SET
            p.vf_vehicle = COALESCE(NULLIF(t.vehicle_no, ''), NULLIF(t.vehicle_market, '')),
            p.trip_vehicle_type = CASE
                WHEN COALESCE(p.trip_vehicle_type, '') = '' THEN t.vehicle_type
                ELSE p.trip_vehicle_type
            END
        WHERE p.type != 'Vehicle Finance EMI'
          AND COALESCE(p.vf_vehicle, '') = ''
          AND COALESCE(p.trip_no, '') != ''
          AND (COALESCE(t.vehicle_no, '') != '' OR COALESCE(t.vehicle_market, '') != '')
    """)

    frappe.db.sql("""
        UPDATE `tabPayment` p
        INNER JOIN `tabVehicle` v ON v.name = p.vf_vehicle
        SET p.trip_vehicle_type = v.custom_vehicle_type
        WHERE p.type = 'Vehicle Finance EMI'
          AND COALESCE(p.trip_vehicle_type, '') = ''
          AND COALESCE(p.vf_vehicle, '') != ''
          AND COALESCE(v.custom_vehicle_type, '') != ''
    """)
    frappe.db.commit()
