import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np

# Seed for deterministic generation
DEFAULT_SEED = 42

FAILURE_SCENARIOS = [
    # (failure_type, failure_reason, is_recoverable_prob, default_best_action, method)
    ("network_error", "Gateway connection timed out during 3DS verification", 0.88, "RETRY", "card"),
    ("bank_unavailable", "Issuing bank server currently under maintenance / high latency", 0.82, "RETRY", "upi"),
    ("timeout", "Payment authorization timed out from bank ACS", 0.85, "RETRY", "netbanking"),
    ("abandonment", "Customer abandoned checkout session after order creation", 0.58, "PAYMENT_LINK", "upi"),
    ("insufficient_funds", "Account balance insufficient at transaction attempt", 0.45, "PAYMENT_LINK", "upi"),
    ("card_expired", "Card expiry date reached on recurring subscription charge", 0.72, "SUBSCRIPTION_RECOVERY", "card"),
    ("high_value_risk", "High value enterprise transaction flagged for review", 0.90, "HUMAN_REVIEW", "netbanking"),
    ("fraud_flagged", "Transaction flagged by risk engine for suspicious IP velocity", 0.05, "NO_ACTION", "card"),
    ("invalid_credentials", "Customer entered incorrect OTP/PIN repeatedly", 0.20, "NO_ACTION", "upi"),
    ("card_declined_permanent", "Card blocked or reported stolen by issuer", 0.02, "NO_ACTION", "card"),
]

CUSTOMER_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohan Mehta", "Ananya Iyer", "Vikram Malhotra",
    "Sneha Reddy", "Aditya Verma", "Kavita Rao", "Rajesh Gupta", "Pooja Deshmukh",
    "Arjun Nair", "Neha Joshi", "Sanjay Singhania", "Divya Menon", "Karthik Sundaram",
    "Meera Mukherjee", "Deepak Kapoor", "Shreya Sen", "Nikhil Chawla", "Tanvi Bhatia",
    "Akash Saxena", "Ritu Kulkarni", "Vivek Bansal", "Swati Nambiar", "Manish Pandey"
]


class SyntheticDataGenerator:
    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed
        self.rng = random.Random(seed)
        np.random.seed(seed)

    def generate_customers(self, count: int = 1500) -> List[Dict[str, Any]]:
        customers = []
        for i in range(count):
            name = self.rng.choice(CUSTOMER_NAMES)
            first_name = name.split()[0].lower()
            cid = f"cust_{self.seed}_{i:05d}"
            email = f"{first_name}.{i:04d}@example.com"
            phone = f"+9198{self.rng.randint(10000000, 99999999)}"
            age_days = self.rng.randint(5, 730)
            opt_out = self.rng.random() < 0.02  # 2% opt-out
            customers.append({
                "id": cid,
                "name": name,
                "email": email,
                "phone": phone,
                "customer_age_days": age_days,
                "opt_out": opt_out,
                "created_at": datetime.utcnow() - timedelta(days=age_days),
            })
        return customers

    def generate_dataset(
        self, total_events: int = 50000
    ) -> Dict[str, Any]:
        """
        Deterministically generate at least 50,000 payment events, orders, subscriptions,
        and recovery cases with ground truth.
        """
        self.rng = random.Random(self.seed)
        np.random.seed(self.seed)

        customer_count = min(3000, max(500, total_events // 20))
        customers = self.generate_customers(customer_count)
        customer_ids = [c["id"] for c in customers]

        orders = []
        payments = []
        payment_attempts = []
        subscriptions = []
        invoices = []
        recovery_cases = []
        webhook_events = []
        ground_truth_records = []

        # Target: ~25% are failure/risk events that trigger recovery cases
        num_failure_events = int(total_events * 0.25)
        num_success_events = total_events - num_failure_events

        base_time = datetime.utcnow() - timedelta(days=60)

        # 1. Generate Successful Transactions
        for i in range(num_success_events):
            event_time = base_time + timedelta(minutes=int(i * 1.5))
            cid = self.rng.choice(customer_ids)
            amount = round(float(np.random.choice([499.0, 999.0, 1499.0, 2499.0, 4999.0, 9999.0, 19999.0, 45000.0])), 2)
            oid = f"order_{self.seed}_{i:06d}"
            pid = f"pay_{self.seed}_{i:06d}"
            method = self.rng.choice(["upi", "card", "netbanking"])

            orders.append({
                "id": oid,
                "customer_id": cid,
                "amount": amount,
                "currency": "INR",
                "status": "paid",
                "created_at": event_time,
                "updated_at": event_time + timedelta(seconds=15),
            })

            payments.append({
                "id": pid,
                "order_id": oid,
                "customer_id": cid,
                "amount": amount,
                "currency": "INR",
                "status": "captured",
                "method": method,
                "error_code": None,
                "error_description": None,
                "failure_type": None,
                "created_at": event_time + timedelta(seconds=5),
            })

            # Normal success webhook
            wevt_id = f"evt_{self.seed}_{i:06d}"
            webhook_events.append({
                "id": wevt_id,
                "event_type": "payment.captured",
                "signature": f"sig_{uuid.uuid4().hex[:16]}",
                "processed": True,
                "is_duplicate": False,
                "created_at": event_time + timedelta(seconds=6),
                "processed_at": event_time + timedelta(seconds=7),
                "raw_payload": {
                    "event": "payment.captured",
                    "payload": {
                        "payment": {
                            "entity": {
                                "id": pid,
                                "order_id": oid,
                                "amount": int(amount * 100),
                                "status": "captured",
                            }
                        }
                    }
                }
            })

        # 2. Generate Failure & Risk Events (with Ground Truth)
        for j in range(num_failure_events):
            idx = num_success_events + j
            event_time = base_time + timedelta(minutes=int(idx * 1.5))
            cid = self.rng.choice(customer_ids)
            scenario = self.rng.choice(FAILURE_SCENARIOS)
            (failure_type, failure_reason, recoverable_prob, best_action_default, method) = scenario

            # Amount distribution: some small, some medium, some enterprise > 50,000
            if failure_type == "high_value_risk":
                amount = round(float(self.rng.choice([55000.0, 75000.0, 120000.0, 250000.0])), 2)
            else:
                amount = round(float(self.rng.choice([799.0, 1499.0, 2999.0, 4999.0, 8500.0, 14999.0, 29999.0])), 2)

            oid = f"order_{self.seed}_{idx:06d}"
            pid = f"pay_{self.seed}_{idx:06d}"
            case_id = f"case_{self.seed}_{j:06d}"

            # Determine ground truth deterministically
            is_recoverable = 1 if self.rng.random() < recoverable_prob else 0
            best_action = best_action_default
            if not is_recoverable:
                best_action = "NO_ACTION"
            elif amount >= 50000.0 and best_action != "HUMAN_REVIEW":
                best_action = "HUMAN_REVIEW"

            recovered_amount = amount if is_recoverable else 0.0

            # Entity type
            if failure_type == "card_expired":
                entity_type = "SUBSCRIPTION"
                sub_id = f"sub_{self.seed}_{j:05d}"
                subscriptions.append({
                    "id": sub_id,
                    "customer_id": cid,
                    "plan_id": f"plan_pro_{self.rng.choice([999, 1999, 4999])}",
                    "status": "halted",
                    "amount": amount,
                    "currency": "INR",
                    "current_period_end": event_time,
                    "created_at": event_time - timedelta(days=90),
                })
                entity_id = sub_id
            elif failure_type == "abandonment":
                entity_type = "ORDER_ABANDONMENT"
                entity_id = oid
            else:
                entity_type = "PAYMENT"
                entity_id = pid

            orders.append({
                "id": oid,
                "customer_id": cid,
                "amount": amount,
                "currency": "INR",
                "status": "created" if failure_type == "abandonment" else "attempted",
                "created_at": event_time,
                "updated_at": event_time + timedelta(seconds=10),
            })

            payments.append({
                "id": pid,
                "order_id": oid,
                "customer_id": cid,
                "amount": amount,
                "currency": "INR",
                "status": "failed",
                "method": method,
                "error_code": failure_type.upper(),
                "error_description": failure_reason,
                "failure_type": failure_type,
                "created_at": event_time + timedelta(seconds=5),
            })

            payment_attempts.append({
                "id": f"att_{self.seed}_{j:06d}",
                "payment_id": pid,
                "attempt_number": 1,
                "error_type": failure_type,
                "raw_response": {"error_code": failure_type, "message": failure_reason},
                "created_at": event_time + timedelta(seconds=5),
            })

            # Recoverability score (with realistic slight variance around ground truth prob)
            score = max(0.01, min(0.99, recoverable_prob + self.rng.uniform(-0.10, 0.08)))
            score = round(score, 3)
            expected_recovery_value = round(amount * score, 2)

            # Recovery Case
            recovery_cases.append({
                "id": case_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "customer_id": cid,
                "amount_at_risk": amount,
                "recoverability_score": score,
                "expected_recovery_value": expected_recovery_value,
                "recovered_amount": 0.0,  # Starts strictly 0 until verified
                "failure_reason": failure_reason,
                "failure_type": failure_type,
                "state": "ANALYZING",
                "recommended_action": best_action,
                "authorized_action": None,
                "executed_action": None,
                "retry_count": 0,
                "ai_diagnosis": f"Automated risk detection identified {failure_type}: {failure_reason}",
                "ai_confidence": round(0.75 + 0.20 * self.rng.random(), 2),
                "created_at": event_time + timedelta(seconds=10),
                "updated_at": event_time + timedelta(seconds=10),
            })

            # Ground truth record for benchmarks & evaluations
            ground_truth_records.append({
                "case_id": case_id,
                "entity_id": entity_id,
                "failure_type": failure_type,
                "amount_at_risk": amount,
                "recoverable": is_recoverable,
                "best_action": best_action,
                "recovered_amount": recovered_amount,
                "failure_reason": failure_reason,
                "recoverability_score": score,
            })

            # Failure Webhook event
            wevt_id = f"evt_fail_{self.seed}_{j:06d}"
            webhook_events.append({
                "id": wevt_id,
                "event_type": "payment.failed",
                "signature": f"sig_{uuid.uuid4().hex[:16]}",
                "processed": False,
                "is_duplicate": False,
                "created_at": event_time + timedelta(seconds=6),
                "processed_at": None,
                "raw_payload": {
                    "event": "payment.failed",
                    "payload": {
                        "payment": {
                            "entity": {
                                "id": pid,
                                "order_id": oid,
                                "amount": int(amount * 100),
                                "status": "failed",
                                "error_code": failure_type,
                                "error_description": failure_reason,
                            }
                        }
                    }
                }
            })

        # Inject realistic webhook edge cases:
        # 1. Duplicate webhooks
        for k in range(min(150, len(webhook_events))):
            orig = webhook_events[k]
            dup = dict(orig)
            dup["id"] = f"{orig['id']}_dup"
            dup["is_duplicate"] = True
            dup["processed"] = True
            webhook_events.append(dup)

        return {
            "customers": customers,
            "orders": orders,
            "payments": payments,
            "payment_attempts": payment_attempts,
            "subscriptions": subscriptions,
            "invoices": invoices,
            "recovery_cases": recovery_cases,
            "webhook_events": webhook_events,
            "ground_truth": ground_truth_records,
            "metrics": {
                "total_events": total_events,
                "num_success_events": num_success_events,
                "num_failure_events": num_failure_events,
                "num_cases": len(recovery_cases),
                "total_revenue_at_risk": sum(c["amount_at_risk"] for c in recovery_cases),
                "total_ground_truth_recoverable": sum(g["amount_at_risk"] for g in ground_truth_records if g["recoverable"] == 1),
            }
        }
