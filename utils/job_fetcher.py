from utils.job_scraper import razorpay

company_map = {
    "razorpay": razorpay,
}

def get_jobs_from_company(company, limit=10):
    handler = company_map.get(company.lower())
    if not handler:
        return f"❌ No handler found for '{company}'"
    
    return handler.fetch_jobs(limit=limit)
