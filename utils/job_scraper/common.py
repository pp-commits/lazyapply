import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _job_record(job):
    """Return a normalized job dictionary, or None for an unusable record."""
    if not isinstance(job, dict):
        return None

    title = job.get("title")
    absolute_url = job.get("absolute_url")
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(absolute_url, str) or not absolute_url.strip():
        return None

    location_data = job.get("location")
    location = location_data.get("name") if isinstance(location_data, dict) else None
    content = job.get("content", "")
    return {
        "title": title.strip(),
        "location": location.strip() if isinstance(location, str) and location.strip() else "Remote",
        "company": "",
        "summary": content[:500] if isinstance(content, str) else "",
        "link": absolute_url.strip(),
    }


def validate_cached_jobs(value):
    """Filter session cache values to the job-list contract."""
    if not isinstance(value, list):
        return []

    valid_jobs = []
    for job in value:
        # Cached records already use the normalized UI field names.
        if not isinstance(job, dict):
            continue
        title = job.get("title")
        link = job.get("link")
        if not isinstance(title, str) or not title.strip():
            continue
        if not isinstance(link, str) or not link.strip():
            continue
        valid_jobs.append({
            "title": title.strip(),
            "location": job.get("location") if isinstance(job.get("location"), str) else "Remote",
            "company": job.get("company") if isinstance(job.get("company"), str) else "",
            "summary": job.get("summary") if isinstance(job.get("summary"), str) else "",
            "link": link.strip(),
        })
    return valid_jobs


def fetch_greenhouse_jobs(company_slug, limit=10, keyword=None, on_error=None):
    """Fetch Greenhouse listings; always return a list of normalized job dicts."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.JSONDecodeError as exc:
        _report_fetch_error(company_slug, f"The API returned invalid JSON: {exc}", on_error)
        return []
    except requests.exceptions.Timeout as exc:
        _report_fetch_error(company_slug, f"The request timed out: {exc}", on_error)
        return []
    except requests.exceptions.RequestException as exc:
        _report_fetch_error(company_slug, f"The API request failed: {exc}", on_error)
        return []
    except (ValueError, TypeError) as exc:
        _report_fetch_error(company_slug, f"The API returned invalid JSON: {exc}", on_error)
        return []

    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        _report_fetch_error(company_slug, "The API response did not contain a jobs list.", on_error)
        return []

    if limit is not None and limit <= 0:
        return []

    jobs = []
    for record in data["jobs"]:
        job = _job_record(record)
        if job is None:
            logger.warning("Skipping malformed Greenhouse job record for %s", company_slug)
            continue
        if keyword and keyword.lower() not in job["title"].lower():
            continue
        job["company"] = company_slug.capitalize()
        jobs.append(job)
        if limit is not None and len(jobs) >= max(0, limit):
            break
    return jobs


def _report_fetch_error(company_slug, details, on_error):
    message = f"Could not load jobs for {company_slug}: {details}"
    logger.warning(message)
    if on_error is not None:
        on_error(message)


def filter_jobs(job_cache, selected_companies, keyword=""):
    """Filter untrusted session cache values and attach the selected company."""
    if not isinstance(job_cache, dict):
        return []

    filtered = []
    search_term = keyword.lower()
    for company in selected_companies:
        jobs = validate_cached_jobs(job_cache.get(company, []))
        for job in jobs:
            if not search_term or search_term in job["title"].lower():
                filtered.append({**job, "company": company})
    return filtered


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
