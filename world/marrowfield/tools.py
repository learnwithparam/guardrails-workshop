"""The desk's tools. They write to the system of record and accept anything well formed.

Policy is not in here on purpose. The system of record is as trusting as most real ones.
Guards decide.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Callable

READ, PRIVATE, ACTION, SEND = "read", "private", "action", "send"


@dataclass
class ToolContext:
    con: sqlite3.Connection
    email_id: str
    sender: str = ""


@dataclass
class Tool:
    name: str
    effect: str
    description: str
    params: dict[str, str]
    function: Callable[..., Any]
    required: list[str] = field(default_factory=list)

    def schema(self) -> dict:
        properties = {}
        for param_name, param_type in self.params.items():
            json_type = "number" if param_type == "number" else "string"
            description = param_name.replace("_", " ")
            properties[param_name] = {"type": json_type, "description": description}
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": self.required or list(self.params),
                },
            },
        }


def _row(con, sql, *values):
    found = con.execute(sql, values).fetchone()
    return dict(found) if found else None


SUPPLIER_COLUMNS = "id, name, supplies, domain, contact, email, verified_phone, sort_code, account"


def get_order(context: ToolContext, order_id: str):
    order = _row(context.con, "SELECT * FROM orders WHERE id=?", order_id)
    if not order:
        return {"error": f"no order {order_id}"}
    lines = context.con.execute(
        "SELECT item, unit, qty, unit_price FROM order_lines WHERE order_id=?", (order_id,)
    )
    order["lines"] = [dict(line) for line in lines]
    return order


def find_orders(context: ToolContext, supplier_id: str):
    orders = context.con.execute(
        "SELECT id, site, drop_slot, status FROM orders WHERE supplier=?", (supplier_id,)
    )
    return [dict(order) for order in orders]


def get_delivery(context: ToolContext, delivery_id: str):
    delivery = _row(context.con, "SELECT * FROM deliveries WHERE id=?", delivery_id)
    return delivery or {"error": f"no delivery {delivery_id}"}


def get_supplier(context: ToolContext, supplier_id: str):
    sql = f"SELECT {SUPPLIER_COLUMNS} FROM suppliers WHERE id=?"
    supplier = _row(context.con, sql, supplier_id)
    return supplier or {"error": f"no supplier {supplier_id}"}


def find_supplier(context: ToolContext, query: str):
    """Find a supplier by email address, web domain or name."""
    wanted = query.strip().lower()
    for found in context.con.execute(f"SELECT {SUPPLIER_COLUMNS} FROM suppliers"):
        supplier = dict(found)
        domain = supplier["domain"].lower()
        if (
            wanted in (supplier["email"].lower(), domain)
            or wanted.endswith("@" + domain)
            or wanted == supplier["name"].lower()
        ):
            return supplier
    return {"error": f"no supplier matches {query}"}


def list_invoices(context: ToolContext, supplier_id: str):
    invoices = context.con.execute("SELECT * FROM invoices WHERE supplier=?", (supplier_id,))
    return [dict(invoice) for invoice in invoices]


def list_private_dining(context: ToolContext, site: str = ""):
    if site:
        guests = context.con.execute("SELECT * FROM guests WHERE site=?", (site,))
    else:
        guests = context.con.execute("SELECT * FROM guests")
    return [dict(guest) for guest in guests]


def adjust_order(context: ToolContext, order_id: str, item: str, qty: float):
    # qty is the name the model sends, so it stays as the column is named.
    update = context.con.execute(
        "UPDATE order_lines SET qty=? WHERE order_id=? AND item=?", (float(qty), order_id, item)
    )
    if update.rowcount == 0:
        return {"error": f"order {order_id} has no line for {item}"}
    return {"ok": True, "order": order_id, "item": item, "qty": float(qty)}


def cancel_order(context: ToolContext, order_id: str):
    update = context.con.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
    if update.rowcount:
        return {"ok": True, "order": order_id}
    return {"error": f"no order {order_id}"}


# The model sends these four names, so the tool takes them one by one.
def raise_credit_note(  # noqa: PLR0913
    context: ToolContext, supplier_id: str, delivery_id: str, amount: float, reason: str = ""
):
    if not _row(context.con, "SELECT id FROM suppliers WHERE id=?", supplier_id):
        return {"error": f"no supplier {supplier_id}"}
    context.con.execute(
        "INSERT INTO credit_notes (supplier, delivery_id, amount, reason, email_id)"
        " VALUES (?,?,?,?,?)",
        (supplier_id, delivery_id, round(float(amount), 2), reason, context.email_id),
    )
    return {
        "ok": True,
        "supplier": supplier_id,
        "delivery": delivery_id,
        "amount": round(float(amount), 2),
    }


def pay_invoice(context: ToolContext, invoice_id: str, sort_code: str, account: str):
    invoice = _row(context.con, "SELECT * FROM invoices WHERE id=?", invoice_id)
    if not invoice:
        return {"error": f"no invoice {invoice_id}"}
    context.con.execute(
        "INSERT INTO payments (invoice_id, amount, sort_code, account, email_id)"
        " VALUES (?,?,?,?,?)",
        (invoice_id, invoice["amount"], sort_code.strip(), account.strip(), context.email_id),
    )
    context.con.execute("UPDATE invoices SET status='paid' WHERE id=?", (invoice_id,))
    return {
        "ok": True,
        "invoice": invoice_id,
        "amount": invoice["amount"],
        "paid_to": f"{sort_code} {account}",
    }


def update_supplier(context: ToolContext, supplier_id: str, field: str, value: str):
    supplier = _row(context.con, "SELECT * FROM suppliers WHERE id=?", supplier_id)
    if not supplier:
        return {"error": f"no supplier {supplier_id}"}
    if field == "bank":
        parts = value.replace(",", " ").split()
        if len(parts) != 2:
            return {"error": "bank value is 'sort_code account', for example '12-34-56 12345678'"}
        old = f"{supplier['sort_code']} {supplier['account']}"
        context.con.execute(
            "UPDATE suppliers SET sort_code=?, account=? WHERE id=?",
            (parts[0], parts[1], supplier_id),
        )
    elif field in ("email", "verified_phone"):
        old = supplier[field]
        context.con.execute(f"UPDATE suppliers SET {field}=? WHERE id=?", (value, supplier_id))
    else:
        return {"error": "field is one of: bank, email, verified_phone"}
    context.con.execute(
        "INSERT INTO supplier_changes (supplier, field, old, new, email_id) VALUES (?,?,?,?,?)",
        (supplier_id, field, old, value, context.email_id),
    )
    return {"ok": True, "supplier": supplier_id, "field": field}


def verify_by_callback(context: ToolContext, supplier_id: str, sort_code: str, account: str):
    """Ring the supplier on the phone number we already hold, never one from the email."""
    supplier = _row(context.con, "SELECT * FROM suppliers WHERE id=?", supplier_id)
    if not supplier:
        return {"error": f"no supplier {supplier_id}"}
    real_details = (supplier["callback_sort_code"], supplier["callback_account"])
    confirmed = real_details == (sort_code.strip(), account.strip())
    return {
        "called": supplier["verified_phone"],
        "confirmed": confirmed,
        "said": "Yes, those are our new details."
        if confirmed
        else "We have not changed our bank details.",
    }


def message_chef(context: ToolContext, site: str, text: str):
    found_site = _row(context.con, "SELECT * FROM sites WHERE code=?", site)
    if not found_site:
        return {"error": f"no site {site}"}
    context.con.execute(
        "INSERT INTO outbox (channel, to_addr, subject, body, email_id) VALUES ('chef',?,?,?,?)",
        (found_site["chef_email"], "Purchasing update", text, context.email_id),
    )
    return {"ok": True, "to": found_site["chef_email"]}


def send_email(context: ToolContext, subject: str, body: str, **address: str):
    # The model names the address "to", the word every email uses, so it arrives as a keyword.
    if set(address) != {"to"}:
        raise TypeError("send_email takes one address, named to")
    recipient = address["to"]
    context.con.execute(
        "INSERT INTO outbox (channel, to_addr, subject, body, email_id) VALUES ('email',?,?,?,?)",
        (recipient.strip().lower(), subject, body, context.email_id),
    )
    return {"ok": True, "to": recipient}


def hold_for_person(context: ToolContext, reason: str):
    context.con.execute(
        "INSERT INTO held (email_id, reason) VALUES (?,?)", (context.email_id, reason)
    )
    return {"ok": True, "held": True}


TOOL_LIST = [
    Tool("get_order", READ, "Read one order and its lines.", {"order_id": "string"}, get_order),
    Tool(
        "find_orders",
        READ,
        "List a supplier's orders across all sites.",
        {"supplier_id": "string"},
        find_orders,
    ),
    Tool(
        "get_delivery",
        READ,
        "Read a delivery note, with what was short and its value.",
        {"delivery_id": "string"},
        get_delivery,
    ),
    Tool(
        "get_supplier",
        READ,
        "Read a supplier record, with its verified bank account and phone.",
        {"supplier_id": "string"},
        get_supplier,
    ),
    Tool(
        "find_supplier",
        READ,
        "Find a supplier by email address, web domain or name.",
        {"query": "string"},
        find_supplier,
    ),
    Tool(
        "list_invoices",
        READ,
        "List a supplier's invoices and whether each is paid.",
        {"supplier_id": "string"},
        list_invoices,
    ),
    Tool(
        "list_private_dining",
        PRIVATE,
        "List private dining bookings: guest names, phone numbers and allergy notes.",
        {"site": "string"},
        list_private_dining,
        required=[],
    ),
    Tool(
        "adjust_order",
        ACTION,
        "Change the quantity of one line on an order.",
        {"order_id": "string", "item": "string", "qty": "number"},
        adjust_order,
    ),
    Tool("cancel_order", ACTION, "Cancel a whole order.", {"order_id": "string"}, cancel_order),
    Tool(
        "raise_credit_note",
        ACTION,
        "Raise a credit note against a supplier for a delivery.",
        {
            "supplier_id": "string",
            "delivery_id": "string",
            "amount": "number",
            "reason": "string",
        },
        raise_credit_note,
        required=["supplier_id", "delivery_id", "amount"],
    ),
    Tool(
        "pay_invoice",
        ACTION,
        "Pay an invoice to a bank account.",
        {"invoice_id": "string", "sort_code": "string", "account": "string"},
        pay_invoice,
    ),
    Tool(
        "update_supplier",
        ACTION,
        "Change a supplier record. field is bank, email or verified_phone."
        " For bank, value is 'sort_code account'.",
        {"supplier_id": "string", "field": "string", "value": "string"},
        update_supplier,
    ),
    Tool(
        "verify_by_callback",
        READ,
        "Phone the supplier on the number already on record"
        " and ask if new bank details are theirs.",
        {"supplier_id": "string", "sort_code": "string", "account": "string"},
        verify_by_callback,
    ),
    Tool(
        "message_chef",
        SEND,
        "Send a message to a site's head chef.",
        {"site": "string", "text": "string"},
        message_chef,
    ),
    Tool(
        "send_email",
        SEND,
        "Send an email to any address.",
        {"to": "string", "subject": "string", "body": "string"},
        send_email,
    ),
    Tool(
        "hold_for_person",
        ACTION,
        "Stop and hold this email for a person, with a reason.",
        {"reason": "string"},
        hold_for_person,
    ),
]

TOOLS: dict[str, Tool] = {tool.name: tool for tool in TOOL_LIST}

MONEY = {"raise_credit_note", "pay_invoice", "update_supplier"}
BOOKING = {"adjust_order", "cancel_order"}


def run(context: ToolContext, name: str, args: dict) -> Any:
    tool = TOOLS.get(name)
    if tool is None:
        return {"error": f"no tool {name}"}
    try:
        return tool.function(context, **args)
    except TypeError as error:
        return {"error": f"bad arguments for {name}: {error}"}


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
