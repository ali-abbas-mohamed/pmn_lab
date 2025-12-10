import random
import datetime
import time
import argparse
import os

# Weighted severity distribution
severity_weights = {
    "INFO": 40,
    "DEBUG": 25,
    "MINOR": 15,
    "MAJOR": 10,
    "ERROR": 7,
    "CRITICAL": 3
}

# Users and roles
users_roles = {
    "Alice": "Manager",
    "John": "Standard",
    "Nathan": "Guest",
    "Joe": "Operator",
    "Sam": "Admin",
    "SYSTEM": "SYSTEM"
}

# User activity frequency weights (baseline)
user_weights = {
    "SYSTEM": 35,
    "Alice": 20,
    "John": 15,
    "Joe": 10,
    "Sam": 10,
    "Nathan": 5
}

# Time-of-day activity patterns (hour ranges)
user_active_hours = {
    "SYSTEM": (0, 23),   # always
    "Alice": (8, 18),    # business hours
    "John": (7, 22),     # daytime/evening
    "Nathan": (17, 23),  # evenings
    "Joe": (4, 12),      # morning shifts
    "Sam": (9, 17)       # daytime
}

# Role-based message pools
role_messages = {
    "Manager": [
        "Application launch: SecureMessenger",
        "Application launch: VideoCall",
        "Configuration change: Wi-Fi disabled",
        "Configuration change: Bluetooth enabled",
        "File upload initiated (File: report_Q4.pdf)",
        "File upload completed (Status: Success)",
        "Login successful",
        "Logout"
    ],
    "Standard": [
        "Login successful",
        "Logout",
        "Downloaded update package",
        "Attempted access to restricted admin panel",
        "Security alert: Failed attempt to access restricted settings",
        "File upload initiated (File: report_Q4.pdf)",
        "File upload completed (Status: Success)"
    ],
    "Guest": [
        "Login successful",
        "Application launch: SecureMessenger",
        "Application launch: VideoCall",
        "Logout",
        "File upload initiated (File: guest_upload.txt)"
    ],
    "Operator": [
        "Installed security patch",
        "Password change successful",
        "Login successful",
        "Application launch: VideoCall",
        "Security alert: Failed attempt to access restricted settings",
        "Downloaded update package"
    ],
    "Admin": [
        "Password change successful",
        "Two-factor authentication enabled",
        "Unauthorized app installation blocked",
        "Malware scan completed (No threats found)",
        "Login successful",
        "Logout"
    ],
    "SYSTEM": [
        "UE shutdown initiated",
        "UE OS loaded successfully",
        "UE attached to network (PLMN: 310-150, Cell: 12345)",
        "Critical fault detected: Radio module overheating (Temp: 85°C)",
        "Fault correlation: BTS power off at Site Dallas-01 caused UE detach",
        "Wi-Fi connected (SSID: OfficeNet)",
        "Wi-Fi disconnected",
        "Battery low (5%)",
        "Device rebooted"
    ]
}

def weighted_choice(weight_dict):
    items = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(items, weights=weights, k=1)[0]

def generate_random_interval(min_seconds=1, max_seconds=30):
    return random.randint(min_seconds, max_seconds)

def pick_user_for_time(current_time):
    """Pick a user based on time-of-day activity patterns."""
    hour = current_time.hour
    active_users = [u for u, hrs in user_active_hours.items() if hrs[0] <= hour <= hrs[1]]
    if not active_users:
        active_users = list(users_roles.keys())  # fallback
    weights = [user_weights[u] for u in active_users]
    return random.choices(active_users, weights=weights, k=1)[0]

def write_log_entry(f, timestamp, user, role, severity, message):
    log_entry = f"{timestamp} [{severity}] [{user}] {message} (Role: {role})\n"
    f.write(log_entry)
    f.flush()
    print(log_entry.strip())

def prepopulate_logs(base_filename, days_back=3, entries_per_day=50):
    now = datetime.datetime.now()
    for d in range(days_back, 0, -1):
        day = (now - datetime.timedelta(days=d)).date()
        log_filename = f"{os.path.splitext(base_filename)[0]}_{day}.log"
        with open(log_filename, "a") as f:
            current_time = datetime.datetime.combine(day, datetime.time(0, 0, 0))
            for _ in range(entries_per_day):
                timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
                user = pick_user_for_time(current_time)
                role = users_roles[user]
                severity = weighted_choice(severity_weights)
                message = random.choice(role_messages[role])
                write_log_entry(f, timestamp, user, role, severity, message)
                current_time += datetime.timedelta(seconds=generate_random_interval(60, 600))

def generate_live_logs(base_filename="ue_audit.log", start_date=None,
                       rotation="day", max_size=1024*1024):
    if start_date is None:
        current_time = datetime.datetime.now()
    else:
        current_time = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    current_day = current_time.date()
    file_index = 1

    while True:
        if rotation == "day":
            log_filename = f"{os.path.splitext(base_filename)[0]}_{current_day}.log"
        else:
            log_filename = f"{os.path.splitext(base_filename)[0]}_{file_index}.log"

        with open(log_filename, "a") as f:
            try:
                while True:
                    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    user = pick_user_for_time(current_time)
                    role = users_roles[user]
                    severity = weighted_choice(severity_weights)
                    message = random.choice(role_messages[role])
                    write_log_entry(f, timestamp, user, role, severity, message)

                    interval = generate_random_interval(1, 30)
                    current_time += datetime.timedelta(seconds=interval)

                    if rotation == "day":
                        if current_time.date() != current_day:
                            current_day = current_time.date()
                            break
                    else:
                        if os.path.getsize(log_filename) >= max_size:
                            file_index += 1
                            break

                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\nStopped log generation.")
                return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mobile Audit Log Generator with Role-Based Patterns, User Frequency, Time-of-Day Activity, Prepopulation, and Rotation")
    parser.add_argument("--file", type=str, default="ue_audit.log", help="Base filename for logs")
    parser.add_argument("--start", type=str, help="Start date in YYYY-MM-DD format (default: now)")
    parser.add_argument("--rotation", type=str, choices=["day", "size"], default="day",
                        help="Rotation type: 'day' or 'size'")
    parser.add_argument("--maxsize", type=int, default=1024*1024,
                        help="Max file size in bytes before rotation (only for size rotation)")
    parser.add_argument("--prepopulate", type=int, default=3,
                        help="Number of past days to prepopulate logs")
    parser.add_argument("--entries", type=int, default=50,
                        help="Number of entries per prepopulated day")
    args = parser.parse_args()

    prepopulate_logs(args.file, days_back=args.prepopulate, entries_per_day=args.entries)
    generate_live_logs(base_filename=args.file,
                       start_date=args.start,
                       rotation=args.rotation,
                       max_size=args.maxsize)