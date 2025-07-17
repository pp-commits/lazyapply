import requests
from bs4 import BeautifulSoup

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
                "summary": job.get("content", "")[:500],  # Short summary
                "link": job["absolute_url"]
            })

            if len(jobs) >= limit:
                break

        return jobs

    except Exception as e:
        return f"❌ Error fetching jobs for {company_slug}: {e}"


def fetch_full_job_description(url):
    """
    Fetches the full job description HTML and extracts visible text.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for job description in typical container
        job_section = soup.find("div", {"id": "content"})

        if not job_section:
            job_section = soup.find("section") or soup.find("article") or soup

        full_text = job_section.get_text(separator="\n").strip()
        return full_text if full_text else "Full job description could not be extracted."

    except Exception as e:
        return f"❌ Error fetching full job description: {e}"
