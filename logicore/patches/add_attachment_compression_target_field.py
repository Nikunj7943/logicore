from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
    create_custom_field(
        "System Settings",
        {
            "fieldname": "custom_attachment_compression_target_mb",
            "label": "Attachment Compression Target (MB)",
            "fieldtype": "Int",
            "insert_after": "max_file_size",
            "default": "2",
            "description": (
                "Driver / Employee / Compliances PDF and image attachments are always "
                "compressed down towards this size (never used to reject an upload — "
                "see Max File Size above for that)."
            ),
        },
    )
