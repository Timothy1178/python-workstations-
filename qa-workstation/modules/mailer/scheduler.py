"""Runs scheduled Mailer jobs while the workstation is up.

A daemon thread wakes every 30 s; a job is due when its schedule is
enabled, today is one of its days, the wall clock has passed its time,
and it has not already run today. Sends go through run_job() so the
manual "Run now" and the schedule behave identically.
"""
import threading
import time

from . import store, outlook

_started = False


def run_job(job, review=False):
    template = store.get_item("templates", job.get("template_id", "")) or {}
    try:
        table = store.resolve_table(job)
        subject, body = store.render(template, job, table)
        to, cc, bcc = store.recipients_for(job)
        result = outlook.send(store.settings(), to, cc, bcc, subject, body, review=review)
        status = {"ok": True, "message": result, "rows": len(table.get("rows") or []),
                  "to": to, "subject": subject}
    except Exception as exc:  # anything: file missing, transport down…
        status = {"ok": False, "message": str(exc)}
    job["last_run"] = store.now()
    job["last_status"] = status
    store.upsert("jobs", job)
    store.log({"job": job.get("name"), "job_id": job.get("id"), **status})
    return status


def _due(job, now_struct):
    sched = job.get("schedule") or {}
    if not sched.get("enabled"):
        return False
    days = sched.get("days") or [0, 1, 2, 3, 4]
    if now_struct.tm_wday not in days:
        return False
    hhmm = sched.get("time") or "09:00"
    if time.strftime("%H:%M", now_struct) < hhmm:
        return False
    last = (job.get("last_run") or "")[:10]
    return last != time.strftime("%Y-%m-%d", now_struct)


def tick():
    now_struct = time.localtime()
    for job in store.list_items("jobs"):
        if _due(job, now_struct):
            run_job(job)


def _loop():
    while True:
        try:
            tick()
        except Exception:
            pass
        time.sleep(30)


def start():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, name="mailer-scheduler", daemon=True).start()
