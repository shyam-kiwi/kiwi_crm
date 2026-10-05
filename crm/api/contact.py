import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values("CRM Deal", linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			frappe.db.set_value(
				"CRM Deal",
				linked_deal.parent,
				{
					"email": doc.email_id,
					"mobile_no": doc.mobile_no,
				},
			)


@frappe.whitelist()
def get_linked_deals(contact: str):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"currency",
				"deal_value",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def get_linked_leads(contact: str):
	"""Get linked leads for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	lead_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Lead"},
		fields=["parent"],
		distinct=True,
	)

	leads = []
	for d in lead_names:
		lead = frappe.db.get_value(
			"CRM Lead",
			d.parent,
			[
				"name",
				"lead_name",
				"status",
				"email",
				"mobile_no",
				"lead_owner",
				"modified",
			],
			as_dict=True,
		)
		if lead:
			leads.append(lead)

	return leads


@frappe.whitelist()
def get_linked_tickets(contact: str):
	"""Get linked HD Tickets for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_cached_doc("Contact", contact)
	phone_numbers = [p.phone for p in contact_doc.phone_nos] if contact_doc.phone_nos else []

	# Build OR filters: contact link OR matching phone numbers
	or_filters = [["contact", "=", contact]]
	for phone in phone_numbers:
		or_filters.append(["custom_phone_number", "=", phone])

	tickets = frappe.get_all(
		"HD Ticket",
		or_filters=or_filters,
		fields=[
			"name",
			"subject",
			"status",
			"priority",
			"contact",
			"custom_phone_number",
			"modified",
		],
		order_by="modified desc",
		distinct=True,
	)

	return tickets


@frappe.whitelist()
def get_linked_notes(contact: str):
	"""Get linked notes for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	notes = frappe.db.get_all(
		"FCRM Note",
		filters={"reference_doctype": "Contact", "reference_docname": contact},
		fields=["name", "title", "content", "owner", "modified", "creation"],
		order_by="modified desc",
	)

	return notes or []


@frappe.whitelist()
def create_new(contact: str, field: str, value: str):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results
