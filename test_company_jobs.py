from utils.job_scraper.razorpay import fetch_jobs

jobs = fetch_jobs(limit=5, keyword="engineering")

if isinstance(jobs, str):
    print("❌ Error:", jobs)
elif not jobs:
    print("⚠️ No jobs found matching keyword.")
else:
    for i, job in enumerate(jobs, start=1):
        print(f"\n--- Job #{i} ---")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Summary: {job['summary']}")
        print(f"Link: {job['link']}")
