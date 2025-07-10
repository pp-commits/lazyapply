import requests

def fetch_greenhouse_jobs(company_slug, limit=10, keyword=None):
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        jobs = []
        for job in data.get("jobs", []):
            title = job["title"]
            if keyword and keyword.lower() not in title.lower():
                continue

            jobs.append({
                "title": title,
                "location": job["location"]["name"] if job.get("location") else "Remote",
                "company": company_slug.capitalize(),
                "summary": job.get("content", "")[:500],
                "link": job["absolute_url"]
            })

            if len(jobs) >= limit:
                break

        return jobs

    except Exception as e:
        return f"❌ Error fetching jobs for {company_slug}: {e}"
