from datetime import time
import pytz

# ==========REMINDER STORAGE=========
medicine_reminders = {}

# =========ADD REMINDER============
def add_user_reminder(user_id, text):

    try:

        parts = text.split()

        if len(parts) < 3:

            return (
                "❌ Format:\n"
                "remind 08:30 dolo"
            )

        reminder_time = parts[1]

        medicine = " ".join(parts[2:]).lower()

    
        # ========== CREATE USER STORAGE===========
        if user_id not in medicine_reminders:

            medicine_reminders[user_id] = []

        # ======== DUPLICATE CHECK============
        for r in medicine_reminders[user_id]:

            if (
                r["medicine"] == medicine
                and
                r["time"] == reminder_time
            ):

                return (
                    "⚠️ Reminder already exists."
                )

    
        #  =============SAVE==========
        medicine_reminders[user_id].append({

            "medicine": medicine,
            "time": reminder_time

        })

        return (

            f"✅ Reminder Added\n\n"

            f"💊 Medicine: {medicine}\n"

            f"⏰ Time: {reminder_time}"

        )

    except Exception as e:

        print("❌ Add Reminder Error:", e)

        return (
            "❌ Invalid reminder format."
        )

# ========= REMOVE REMINDER =========
def remove_user_reminder(user_id, text):

    try:

        medicine = (
            text.replace("remove", "")
            .strip()
            .lower()
        )

        reminders = medicine_reminders.get(
            user_id,
            []
        )

        updated = [

            r for r in reminders

            if r["medicine"] != medicine

        ]

        medicine_reminders[user_id] = updated

        return (
            f"🗑️ Removed reminder for:\n"
            f"💊 {medicine}"
        )

    except Exception as e:

        print("❌ Remove Reminder Error:", e)

        return (
            "❌ Failed to remove reminder."
        )

# ========= LIST REMINDERS =========
def get_user_reminders(user_id):

    reminders = medicine_reminders.get(
        user_id,
        []
    )

    if not reminders:

        return "📭 No active reminders."

    msg = "📋 Active Reminders\n\n"

    for r in reminders:

        msg += (

            f"💊 {r['medicine']}\n"

            f"⏰ {r['time']}\n\n"

        )

    return msg

# ========= CLEAR REMINDERS =========
def clear_user_reminders(user_id):

    medicine_reminders[user_id] = []

    return "🧹 All reminders cleared."