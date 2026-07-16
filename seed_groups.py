"""
Seed all 17 groups with their BC, CT, TA, GC assignments.

Run once: python seed_groups.py
"""

import hashlib
from database import get_connection, initialize_database


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _username(name: str) -> str:
    return name.lower().replace(" ", ".").replace("shri.", "").replace("smt.", "").replace("ms.", "").replace("ku.", "").replace("dr.", "").replace("..", ".").strip(".")


ALL_USERS = [
    "Shri Bishnu Prasad Aryal Ji",
    "Smt Nara Maya Rijal",
    "Shri Manoj Thapa",
    "Ms Ganga Aryal",
    "Shri Bishnu Paudel",
    "Shri Keshav Raj Ghimire",
    "Shri Krishana Bhat",
    "Smt Bharati Dahal Paudel",
    "Shri Ram Chandra Adhikari",
    "Shri Dipakraj Pokhrel",
    "Smt Indu Dhungana Chalise",
    "Smt Sudha Khanal",
    "Shri Harish Pal",
    "Smt Samjhana Tripathi",
    "Smt Narayani Aryal",
    "Smt Shanti Lamichhane",
    "Shri Vishnu Prasad Kasaju",
    "Smt Leena Bista",
    "Shri Prava Pandey",
    "Smt Pushpa Pandey",
    "Smt Sita Baral",
    "Shri Bimal Subedi",
    "Smt Bhagirathi Ojha",
    "Shri Usha Upreti",
    "Shri Nuna Kattel",
    "Smt Madhaba Dahal",
    "Ms Dikshya Bhattarai",
    "Smt Kalpana Bhatta",
    "Smt Aapsara Dulal",
    "Shri Lok Nath Sharma",
    "Smt Sunita Maharjan",
    "Smt Jayshree Soni Ji",
    "Smt Teela Dhakal Khaaral",
    "Shri Ishor Thapa",
    "Ku Laxmi Kumari Panday",
    "Smt Namita Neupane",
    "Shri Dhrub Kummar Sapkota",
    "Ms Sanju Pandey",
    "Smt Kamal Chandra Bista",
    "Ms Trailokya Puri",
    "Shri Dr Rushikesh Shrik Ji",
    "Shri Dr Keshav Raj Bhatta",
    "Smt Goma Panday",
    "Smt Babita Upadhyaya",
    "Smt Sita Devi Dhakal",
    "Smt Anita Pathak Pant",
    "Shri Rajkumar Bhattarai",
]

# Group data: (group_no, time, bc_name, ct_name, ta_name, gc_name, level, batch)
GROUPS = [
    ("1383", "5:00 AM",  "Shri Bishnu Prasad Aryal Ji",  "Smt Nara Maya Rijal",              "Shri Manoj Thapa",              "Ms Ganga Aryal",              "Level 1", "Regular"),
    ("1384", "6:00 AM",  "Shri Bishnu Prasad Aryal Ji",  "Shri Bishnu Paudel",               "Shri Keshav Raj Ghimire",       "Shri Krishana Bhat",          "Level 1", "Regular"),
    ("1385", "7:00 AM",  "Shri Bishnu Prasad Aryal Ji",  "Smt Bharati Dahal Paudel",         "Shri Ram Chandra Adhikari",     "Shri Dipakraj Pokhrel",       "Level 2", "Regular"),
    ("1386", "9:00 AM",  "Shri Bishnu Prasad Aryal Ji",  "Smt Indu Dhungana Chalise",        "Smt Sudha Khanal",              "Shri Harish Pal",             "Level 2", "Regular"),
    ("1387", "11:00 AM", "Shri Bishnu Prasad Aryal Ji",  "Smt Samjhana Tripathi",            "Smt Narayani Aryal",            "Smt Shanti Lamichhane",       "Level 3", "Regular"),
    ("1388", "1:00 PM",  "Shri Bishnu Prasad Aryal Ji",  "Shri Vishnu Prasad Kasaju",        "Smt Leena Bista",               "Shri Prava Pandey",           "Level 3", "Regular"),
    ("1389", "3:00 PM",  "Shri Bishnu Prasad Aryal Ji",  "Smt Pushpa Pandey",                "Smt Sita Baral",                "Shri Bimal Subedi",           "Level 4", "Regular"),
    ("1390", "4:00 PM",  "Shri Bishnu Prasad Aryal Ji",  "Smt Bhagirathi Ojha",              "Shri Usha Upreti",              "Shri Nuna Kattel",            "Level 4", "Regular"),
    ("1391", "6:00 PM",  "Shri Bishnu Prasad Aryal Ji",  "Smt Madhaba Dahal",                "Ms Dikshya Bhattarai",          "Smt Kalpana Bhatta",          "Level 1", "Kids"),
    ("1392", "7:00 PM",  "Shri Bishnu Prasad Aryal Ji",  "Smt Aapsara Dulal",                "Shri Lok Nath Sharma",          "Smt Sunita Maharjan",         "Level 2", "Kids"),
    ("1393", "9:00 PM",  "Smt Jayshree Soni Ji",         "Smt Teela Dhakal Khaaral",        "Shri Ishor Thapa",              "Ku Laxmi Kumari Panday",      "Level 3", "Kids"),
    ("1394", "9:00 PM",  "Smt Jayshree Soni Ji",         "Ms Dikshya Bhattarai",            "Smt Namita Neupane",            "Shri Dhrub Kummar Sapkota",   "Level 4", "Kids"),
    ("1395", "10:00 PM", "Smt Jayshree Soni Ji",         "Ms Sanju Pandey",                 "Smt Kamal Chandra Bista",       "Ms Trailokya Puri",           "Level 4", "Kids"),
    ("1569", "6:00 AM",  "Shri Dr Rushikesh Shrik Ji",   "Shri Dr Keshav Raj Bhatta",       "Smt Goma Panday",               "Ku Laxmi Kumari Panday",      "Level 1", "Regular"),
    ("1570", "6:00 PM",  "Shri Dr Rushikesh Shrik Ji",   "Smt Sudha Khanal",                "Smt Babita Upadhyaya",          "Smt Sita Devi Dhakal",        "Level 2", "Regular"),
    ("1571", "7:00 PM",  "Shri Dr Rushikesh Shrik Ji",   "Smt Anita Pathak Pant",           "Shri Rajkumar Bhattarai",       "Shri Dhrub Kummar Sapkota",   "Level 3", "Regular"),
]


def seed() -> None:
    initialize_database()
    conn = get_connection()

    # Create all users with default password 'change123'
    user_id_map = {}
    for full_name in ALL_USERS:
        uname = _username(full_name)
        existing = conn.execute(
            "SELECT id FROM users WHERE username=?", (uname,)
        ).fetchone()
        if existing:
            user_id_map[full_name] = existing[0]
        else:
            cur = conn.execute(
                "INSERT INTO users (full_name, username, password_hash, role, active) "
                "VALUES (?, ?, ?, 'TA', 1)",
                (full_name, uname, _hash("change123")),
            )
            user_id_map[full_name] = cur.lastrowid

    # Create / update each group
    for group_no, time, bc_name, ct_name, ta_name, gc_name, level, batch in GROUPS:
        group_label = f"{group_no} ({time})"
        existing = conn.execute(
            "SELECT id FROM groups WHERE name=?", (group_label,)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE groups SET bc_id=?, gc_id=?, ct_id=?, ta_id=?, "
                "bc_name=?, gc_name=?, ct_name=?, ta_name=?, "
                "level=?, batch=?, timing=? WHERE id=?",
                (
                    user_id_map[bc_name],
                    user_id_map[gc_name],
                    user_id_map[ct_name],
                    user_id_map[ta_name],
                    bc_name, gc_name, ct_name, ta_name,
                    level,
                    batch,
                    time,
                    existing[0],
                ),
            )
            print(f"Updated group {group_label} ({level}, {batch})")
        else:
            conn.execute(
                "INSERT INTO groups (name, bc_id, gc_id, ct_id, ta_id, "
                "bc_name, gc_name, ct_name, ta_name, level, batch, timing) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    group_label,
                    user_id_map[bc_name],
                    user_id_map[gc_name],
                    user_id_map[ct_name],
                    user_id_map[ta_name],
                    bc_name, gc_name, ct_name, ta_name,
                    level,
                    batch,
                    time,
                ),
            )
            print(f"Created group {group_label} ({level}, {batch})")

    conn.commit()
    conn.close()

    print("\nAll groups seeded successfully.")
    print("Default password for all users: change123")


if __name__ == "__main__":
    seed()
