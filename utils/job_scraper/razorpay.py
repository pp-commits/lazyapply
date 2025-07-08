import requests
import html2text

def fetch_jobs(limit=10, keyword="engineering"):
    url = "https://boards-api.greenhouse.io/v1/boards/razorpaysoftwareprivatelimited/jobs?content=true"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"❌ API error: {str(e)}"

    data = response.json()
    job_list = data.get("jobs", [])

    jobs = []
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.body_width = 0 

    for job in job_list:
        title = job.get("title", "").lower()
        department = job.get("departments", [])
        dept_names = [d.get("name", "").lower() for d in department]

        # Filter by keyword in title or department
        if keyword.lower() not in title and not any(keyword.lower() in d for d in dept_names):
            continue

        raw_summary = job.get("content", "")
        summary = h.handle(raw_summary).strip().replace('\n', ' ').replace('  ', ' ')
        summary = summary[:300] + "..." if len(summary) > 300 else summary

        jobs.append({
            "title": job.get("title", "N/A"),
            "company": "Razorpay",
            "location": job.get("location", {}).get("name", "N/A"),
            "summary": summary[:300] + "..." if len(summary) > 300 else summary,
            "link": job.get("absolute_url", "#")
        })

        if len(jobs) >= limit:
            break

    return jobs
