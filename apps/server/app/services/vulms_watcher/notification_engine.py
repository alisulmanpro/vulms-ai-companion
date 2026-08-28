from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from prisma import Prisma
from prisma.enums import NotificationStatus


def parse_lms_date(date_str: str) -> Optional[datetime]:
    """Parses VU LMS date strings into python datetime objects."""
    if not date_str:
        return None

    clean_str = date_str.strip()
    date_formats = (
        "%b %d, %Y",
        "%B %d, %Y",
        "%d-%b-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d"
    )

    for fmt in date_formats:
        try:
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            continue

    return None


class VULMSNotificationEngine:
    def __init__(self, db_client: Prisma):
        self.db: Prisma = db_client

    async def _has_alert_been_sent(self, phone_number: str, tag: str) -> bool:
        """
        Checks if a notification containing the unique item threshold tag 
        has already been created in the database.
        """
        existing = await self.db.notification.find_first(
            where={
                "phoneNumber": phone_number,
                "messageBody": {"contains": tag}
            }
        )
        return existing is not None

    async def _get_last_overdue_alert_time(self, phone_number: str, challan_no: str) -> Optional[datetime]:
        """
        Finds the latest notification timestamp for an overdue challan to enforce 5-day gaps.
        """
        record = await self.db.notification.find_first(
            where={
                "phoneNumber": phone_number,
                "messageBody": {"contains": f"OVERDUE:{challan_no}"}
            },
            order={"createdAt": "desc"}
        )
        return record.createdAt if record else None

    async def process_academic_items(
            self,
            phone_number: str,
            category_name: str,
            items_by_course: Dict[str, List[Any]],
            batch_collector: List[Dict[str, Any]]
    ) -> None:
        """Processes Quizzes, Assignments, and GDBs and appends to batch collector."""
        now = datetime.now()

        for course_code, items in items_by_course.items():
            for item in items:
                item_dict = item if isinstance(item, dict) else item.dict()

                item_id = item_dict.get("id", "")
                title = item_dict.get("title") or item_dict.get("question", "Activity")
                due_date_str = item_dict.get("dueDate") or item_dict.get("due_date", "")

                due_dt = parse_lms_date(due_date_str)
                if not due_dt:
                    continue

                if due_dt.hour == 0 and due_dt.minute == 0:
                    due_dt = due_dt.replace(hour=23, minute=59, second=59)

                hours_left = (due_dt - now).total_seconds() / 3600.0

                if hours_left <= 0:
                    continue

                threshold_tag = None
                label = ""

                if hours_left <= 1:
                    threshold_tag = f"[{item_id}:1H]"
                    label = "FINAL WARNING: 1 Hour Left!"
                elif hours_left <= 4:
                    threshold_tag = f"[{item_id}:4H]"
                    label = "URGENT: 4 Hours Left!"
                elif hours_left <= 10:
                    threshold_tag = f"[{item_id}:10H]"
                    label = "REMINDER: 10 Hours Left!"
                elif hours_left <= 30:
                    threshold_tag = f"[{item_id}:30H]"
                    label = "NOTICE: 30 Hours Left!"

                if threshold_tag:
                    already_sent = await self._has_alert_been_sent(phone_number, threshold_tag)
                    if not already_sent:
                        msg = (
                            f"VU LMS Alert - {category_name.upper()}\n"
                            f"Course: {course_code}\n"
                            f"Title: {title}\n"
                            f"Status: {label}\n"
                            f"Due Date: {due_date_str}\n"
                            f"Ref Tag: {threshold_tag}"
                        )
                        batch_collector.append({
                            "phoneNumber": phone_number,
                            "messageBody": msg,
                            "status": NotificationStatus.PENDING,
                            "retryCount": 0
                        })

    async def process_account_challans(
            self,
            phone_number: str,
            account_data: Dict[str, Any],
            batch_collector: List[Dict[str, Any]]
    ) -> None:
        """Processes Account Challans and appends to batch collector."""
        now = datetime.now()
        challans = account_data.get("challans_list") or account_data.get("challansList", [])

        for item in challans:
            item_dict = item if isinstance(item, dict) else item.dict()

            challan_no = item_dict.get("challan_no") or item_dict.get("challanNo", "")
            due_date_str = item_dict.get("due_date") or item_dict.get("dueDate", "")
            payable_fee = item_dict.get("payable_fee") or item_dict.get("payableFee", 0)

            due_dt = parse_lms_date(due_date_str)
            if not due_dt:
                continue

            if due_dt.hour == 0 and due_dt.minute == 0:
                due_dt = due_dt.replace(hour=23, minute=59, second=59)

            hours_left = (due_dt - now).total_seconds() / 3600.0

            # 1. Handle Overdue Rules (Every 5 Days)
            if hours_left < 0:
                last_sent = await self._get_last_overdue_alert_time(phone_number, challan_no)

                if not last_sent or (now - last_sent) >= timedelta(days=5):
                    tag = f"[OVERDUE:{challan_no}:{now.strftime('%Y%m%d')}]"
                    msg = (
                        f"⚠️ VU LMS Fee Overdue Alert\n"
                        f"Challan No: {challan_no}\n"
                        f"Payable Amount: Rs. {payable_fee}\n"
                        f"Status: Fee is OVERDUE! Late charges apply.\n"
                        f"Ref Tag: {tag}"
                    )
                    batch_collector.append({
                        "phoneNumber": phone_number,
                        "messageBody": msg,
                        "status": NotificationStatus.PENDING,
                        "retryCount": 0
                    })
                continue

            # 2. Handle Active Pre-Due Rules
            threshold_tag = None
            label = ""

            if hours_left <= 1:
                threshold_tag = f"[{challan_no}:1H]"
                label = "FINAL WARNING: 1 Hour Remaining!"
            elif hours_left <= 10:
                threshold_tag = f"[{challan_no}:10H]"
                label = "URGENT: 10 Hours Remaining!"
            elif hours_left <= 24:
                threshold_tag = f"[{challan_no}:24H]"
                label = "REMINDER: 24 Hours Remaining!"
            elif hours_left <= 48:
                threshold_tag = f"[{challan_no}:48H]"
                label = "NOTICE: 2 Days Remaining!"

            if threshold_tag:
                already_sent = await self._has_alert_been_sent(phone_number, threshold_tag)
                if not already_sent:
                    msg = (
                        f"💳 VU LMS Fee Reminder\n"
                        f"Challan No: {challan_no}\n"
                        f"Payable Amount: Rs. {payable_fee}\n"
                        f"Status: {label}\n"
                        f"Due Date: {due_date_str}\n"
                        f"Ref Tag: {threshold_tag}"
                    )
                    batch_collector.append({
                        "phoneNumber": phone_number,
                        "messageBody": msg,
                        "status": NotificationStatus.PENDING,
                        "retryCount": 0
                    })

    async def run(self, phone_number: str, parsed_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the notification evaluation and inserts queued messages in batch."""
        data = parsed_payload.get("data", {})
        if not data:
            return {"success": True, "queued_notifications": 0, "batch_payload": []}

        batch_notifications: List[Dict[str, Any]] = []

        # Process Assignments
        if "assignments" in data:
            await self.process_academic_items(
                phone_number, "Assignment", data["assignments"].get("items", {}), batch_notifications
            )

        # Process Quizzes
        if "quizzes" in data:
            await self.process_academic_items(
                phone_number, "Quiz", data["quizzes"].get("items", {}), batch_notifications
            )

        # Process GDBs
        if "gdbs" in data:
            await self.process_academic_items(
                phone_number, "GDB", data["gdbs"].get("items", {}), batch_notifications
            )

        # Process Account Challans
        if "account" in data:
            await self.process_account_challans(
                phone_number, data["account"], batch_notifications
            )

        # Execute Batch Insert into Database
        queued_count = len(batch_notifications)
        if queued_count > 0:
            await self.db.notification.create_many(data=batch_notifications)
            print(f"[Notification Engine] Inserted batch of {queued_count} notifications for {phone_number}")

        return {
            "success": True,
            "queued_notifications": queued_count,
            "batch_payload": batch_notifications
        }
