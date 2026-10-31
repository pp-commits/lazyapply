import unittest
from unittest.mock import Mock, patch

import requests

from utils.job_scraper.common import (
    fetch_greenhouse_jobs,
    fetch_workday_jobs,
    fetch_workday_job_description,
    filter_jobs,
    validate_cached_jobs,
)


def greenhouse_job(title="Software Engineer"):
    return {
        "title": title,
        "location": {"name": "Remote"},
        "content": "Build reliable software.",
        "absolute_url": "https://boards.greenhouse.io/example/jobs/1",
    }


class FetchGreenhouseJobsTests(unittest.TestCase):
    @patch("utils.job_scraper.common.requests.get")
    def test_success_returns_normalized_job_dictionaries(self, get):
        response = Mock()
        response.json.return_value = {"jobs": [greenhouse_job()]}
        get.return_value = response

        result = fetch_greenhouse_jobs("example", keyword="engineer")

        response.raise_for_status.assert_called_once_with()
        get.assert_called_once_with(
            "https://boards-api.greenhouse.io/v1/boards/example/jobs?content=true",
            timeout=10,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Software Engineer")
        self.assertEqual(result[0]["company"], "Example")

    @patch("utils.job_scraper.common.requests.get")
    def test_http_failure_returns_empty_list_and_reports_error(self, get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("503")
        get.return_value = response
        errors = []

        self.assertEqual(fetch_greenhouse_jobs("example", on_error=errors.append), [])
        self.assertTrue(any("API request failed" in message for message in errors))

    @patch("utils.job_scraper.common.requests.get", side_effect=requests.Timeout("slow"))
    def test_timeout_returns_empty_list_and_reports_error(self, _get):
        errors = []
        self.assertEqual(fetch_greenhouse_jobs("example", on_error=errors.append), [])
        self.assertTrue(any("timed out" in message for message in errors))

    @patch("utils.job_scraper.common.requests.get")
    def test_invalid_json_returns_empty_list_and_reports_error(self, get):
        response = Mock()
        response.json.side_effect = ValueError("invalid JSON")
        get.return_value = response
        errors = []

        self.assertEqual(fetch_greenhouse_jobs("example", on_error=errors.append), [])
        self.assertTrue(any("invalid JSON" in message for message in errors))

    @patch("utils.job_scraper.common.requests.get")
    def test_empty_jobs_list_is_valid(self, get):
        response = Mock()
        response.json.return_value = {"jobs": []}
        get.return_value = response
        self.assertEqual(fetch_greenhouse_jobs("example"), [])

    @patch("utils.job_scraper.common.requests.get")
    def test_malformed_records_are_skipped(self, get):
        response = Mock()
        response.json.return_value = {
            "jobs": [None, {"title": "Missing URL"}, greenhouse_job()]
        }
        get.return_value = response
        result = fetch_greenhouse_jobs("example")
        self.assertEqual([job["title"] for job in result], ["Software Engineer"])

    def test_unexpected_cache_types_and_bad_records_are_filtered(self):
        self.assertEqual(validate_cached_jobs("not a list"), [])
        self.assertEqual(validate_cached_jobs(None), [])
        result = validate_cached_jobs([
            "bad record",
            {"title": "Missing link"},
            {"title": "Valid", "link": "https://example.com/job"},
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Valid")
        self.assertEqual(result[0]["location"], "Remote")

    def test_filtering_ignores_bad_company_cache_and_matches_keyword(self):
        cache = {
            "GoodCo": [
                {"title": "Backend Engineer", "link": "https://example.com/1"},
                {"title": "Product Designer", "link": "https://example.com/2"},
            ],
            "BrokenCo": "cached error string",
        }
        result = filter_jobs(cache, ["GoodCo", "BrokenCo"], "engineer")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Backend Engineer")
        self.assertEqual(result[0]["company"], "GoodCo")

    @patch("utils.job_scraper.common.requests.get")
    def test_one_company_failure_does_not_discard_other_results(self, get):
        def response_for_url(url, timeout):
            response = Mock()
            if "/broken/" in url:
                response.raise_for_status.side_effect = requests.HTTPError("503")
            else:
                response.json.return_value = {"jobs": [greenhouse_job()]}
            return response

        get.side_effect = response_for_url
        results = {}
        errors = []
        for company in ("working", "broken", "also-working"):
            results[company] = fetch_greenhouse_jobs(company, on_error=errors.append)

        self.assertEqual(len(results["working"]), 1)
        self.assertEqual(results["broken"], [])
        self.assertEqual(len(results["also-working"]), 1)
        self.assertEqual(len(errors), 1)


class FetchWorkdayJobsTests(unittest.TestCase):
    @patch("utils.job_scraper.common.requests.post")
    def test_success_returns_normalized_workday_postings(self, post):
        response = Mock()
        response.json.return_value = {
            "jobPostings": [{
                "title": "Senior Software Engineer",
                "locationsText": "Bengaluru, India",
                "externalPath": "/job/Bengaluru/Senior-Software-Engineer_JR1000001",
            }]
        }
        post.return_value = response

        jobs = fetch_workday_jobs(
            "https://postman.wd108.myworkdayjobs.com",
            "postman",
            "careers",
            limit=3,
            keyword="engineering",
        )

        post.assert_called_once_with(
            "https://postman.wd108.myworkdayjobs.com/wday/cxs/postman/careers/jobs",
            json={"appliedFacets": {}, "limit": 3, "offset": 0, "searchText": "engineering"},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10,
        )
        self.assertEqual(jobs[0]["company"], "Postman")
        self.assertEqual(jobs[0]["location"], "Bengaluru, India")
        self.assertEqual(
            jobs[0]["link"],
            "https://postman.wd108.myworkdayjobs.com/careers/job/Bengaluru/Senior-Software-Engineer_JR1000001",
        )
        self.assertTrue(jobs[0]["description_url"].endswith("/wday/cxs/postman/careers/job/Bengaluru/Senior-Software-Engineer_JR1000001"))

    @patch("utils.job_scraper.common.requests.post")
    def test_malformed_workday_response_returns_empty_list_and_reports_error(self, post):
        response = Mock()
        response.json.return_value = {"jobs": []}
        post.return_value = response
        errors = []
        jobs = fetch_workday_jobs(
            "https://postman.wd108.myworkdayjobs.com",
            "postman",
            "careers",
            on_error=errors.append,
        )
        self.assertEqual(jobs, [])
        self.assertTrue(any("jobPostings list" in message for message in errors))

    @patch("utils.job_scraper.common.requests.get")
    def test_workday_description_html_is_extracted(self, get):
        response = Mock()
        response.json.return_value = {
            "jobPostingInfo": {"jobDescription": "<div><b>Build APIs</b><p>Ship reliable software.</p></div>"}
        }
        get.return_value = response
        self.assertEqual(
            fetch_workday_job_description("https://example.test/description"),
            "Build APIs\nShip reliable software.",
        )


if __name__ == "__main__":
    unittest.main()
