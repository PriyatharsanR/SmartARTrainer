import json
import os
from datetime import datetime

FILE = "last_activity.json"


def get_last_activity(trainee_id):
    if not os.path.exists(FILE):
        return None

    with open(FILE, "r") as f:
        data = json.load(f)

    return data.get(str(trainee_id))


def update_last_activity(trainee_id):
    data = {}

    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            data = json.load(f)

    data[str(trainee_id)] = datetime.today().strftime("%Y-%m-%d")

    with open(FILE, "w") as f:
        json.dump(data, f)


def is_inactive_30_days(trainee_id):
    last = get_last_activity(trainee_id)

    if not last:
        return False   # first time → no reset

    from datetime import datetime

    last_date = datetime.strptime(last, "%Y-%m-%d")
    today = datetime.today()

    return (today - last_date).days >= 30
