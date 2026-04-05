#!/usr/bin/env python3
"""Career Page Job Scraper v3"""
import re, csv, sys, json, time, logging, requests, openpyxl
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

ATS_OVERRIDES = {
    "careers.snowflake.com":         ("greenhouse", "snowflakecomputing"),
    "stripe.com/jobs":               ("greenhouse", "stripe"),
    "careers.redfin.com":            ("greenhouse", "redfin"),
    "amplitude.com/careers":         ("greenhouse", "amplitude"),
    "careers.remitly.com":           ("greenhouse", "remitly"),
    "careers.avalara.com":           ("greenhouse", "avalara"),
    "www.axon.com/careers":          ("greenhouse", "axon"),
    "www.smartsheet.com":            ("greenhouse", "smartsheet"),
    "careers.expediagroup.com":      ("greenhouse", "expediagroup"),
    "www.alteryx.com":               ("greenhouse", "alteryx"),
    "careers.amd.com":               ("greenhouse", "amd"),
    "careers.adobe.com":             ("greenhouse", "adobe"),
    "www.zillow.com/careers":        ("greenhouse", "zillow"),
    "careers.mastercard.com":        ("greenhouse", "mastercard"),
    "careers.bms.com":               ("greenhouse", "bristolmyerssquibb"),
    "careers.invesco.com":           ("greenhouse", "invesco"),
    "www.eikontx.com":               ("greenhouse", "eikontx"),
    "careers.brillio.com":           ("lever", "brillio"),
    "www.icertis.com":               ("lever", "icertis"),
    "www.alpha-sense.com":           ("lever", "alphasense"),
    "antithesis.com":                ("lever", "antithesis"),
    "www.slalom.com":                ("lever", "slalom"),
    "www.virtusa.com":               ("lever", "virtusa"),
    "www.ssctech.com":               ("lever", "ssctech"),
}

CAREER_URLS = [
    "https://www.amazon.jobs/en/","https://careers.microsoft.com/","https://careers.google.com/",
    "https://jobs.apple.com/","https://www.metacareers.com/","https://jobs.intel.com/",
    "https://www.nvidia.com/en-us/about-nvidia/careers/","https://careers.salesforce.com/",
    "https://careers.cognizant.com/us/en","https://www.tcs.com/careers","https://www.infosys.com/careers/",
    "https://www.accenture.com/us-en/careers","https://www.capgemini.com/us-en/careers/",
    "https://careers.hcltech.com/","https://careers.adobe.com/","https://apply.deloitte.com/careers/SearchJobs",
    "https://careers.jpmorgan.com/","https://www.goldmansachs.com/careers/","https://www.capitalonecareers.com/",
    "https://www.pwc.com/us/en/careers.html","https://careers.amd.com/","https://careers.qualcomm.com/",
    "https://www.kpmguscareers.com/","https://careers.snowflake.com/","https://stripe.com/jobs",
    "https://careers.expediagroup.com/","https://www.zillow.com/careers/","https://www.slalom.com/us/en/careers",
    "https://careers.redfin.com/","https://careers.mastercard.com/us/en/","https://careers.walmart.com/",
    "https://www.f5.com/company/careers","https://jobs.newyorklife.com/","https://hr.uw.edu/jobs/",
    "https://careers.bms.com/","https://www.oracle.com/careers/","https://www.nomura.com/careers/",
    "https://careers.statestreet.com/","https://jobs.citi.com/","https://amplitude.com/careers",
    "https://careers.hcahealthcare.com/","https://careers.fedex.com/fedex/","https://aecom.jobs/",
    "https://www.ltts.com/careers","https://careers.brillio.com/","https://www.americanexpress.com/en-us/careers/",
    "https://jobs.adp.com/","https://careers.invesco.com/","https://www.mizuhoamericas.com/careers/",
    "https://www.ssctech.com/careers","https://www.asml.com/en/careers","https://www.virtusa.com/careers",
    "https://careers.bankofamerica.com/","https://www.eikontx.com/careers/","https://careers.chubb.com/",
    "https://jobs.spectrum.com/","https://search.jobs.barclays/","https://antithesis.com/company/careers/",
    "https://www.alpha-sense.com/careers/","https://careers.avalara.com/","https://careers.remitly.com/",
    "https://www.icertis.com/company/careers/","https://www.smartsheet.com/careers","https://www.fitch.group/careers/",
    "https://www.alteryx.com/about-us/careers","https://broadcom.wd1.myworkdayjobs.com/External_Career",
    "https://careers.daiichisankyo.us/","https://www.axon.com/careers",
    "https://vhr-otsuka.wd1.myworkdayjobs.com/en-US/External","https://lseg.wd3.myworkdayjobs.com/en-US/Careers",
    "https://morganstanley.eightfold.ai/careers","https://careers.catalent.com/us/en/search-results",
    "https://careers.ey.com/ey/search/",
    "https://recruiting.ultipro.com/SPA1006SPCCU/JobBoard/a1ad5f09-7f9c-420c-9e77-4ace84ced6e0/",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def get_company_name(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    for prefix in ["www.", "careers.", "jobs.", "apply.", "hr.", "recruiting."]:
        if host.startswith(prefix):
            host = host[len(prefix):]
    return host.split(".")[0].upper()

def detect_ats(url):
    for fragment, (ats, slug) in ATS_OVERRIDES.items():
        if fragment in url:
            return ats, slug
    u = url.lower()
    for pattern in [r"boards(?:-api)?\.greenhouse\.io/([^/?#]+)", r"job-boards\.greenhouse\.io/([^/?#]+)"]:
        m = re.search(pattern, u)
        if m: return "greenhouse", m.group(1)
    m = re.search(r"jobs\.lever\.co/([^/?#]+)", u)
    if m: return "lever", m.group(1)
    m = re.search(r"(?:jobs|app)\.ashbyhq\.com/([^/?#]+)", u)
    if m: return "ashby", m.group(1)
    if "myworkdayjobs.com" in u: return "workday", url
    return "generic", url

def scrape_greenhouse(slug):
    for host in ["boards-api.greenhouse.io", "job-boards.greenhouse.io"]:
        try:
            r = SESSION.get(f"https://{host}/v1/boards/{slug}/jobs?content=true", timeout=15)
            if r.status_code == 200:
                jobs_raw = r.json().get("jobs", [])
                if jobs_raw:
                    return [{"title": j.get("title",""), "location": ", ".join(l.get("name","") for l in j.get("offices",[])) or j.get("location",{}).get("name",""), "department": ", ".join(d.get("name","") for d in j.get("departments",[])), "url": j.get("absolute_url",""), "posted_at": j.get("updated_at","")} for j in jobs_raw]
        except Exception as e:
            log.warning(f"    GH error ({host}/{slug}): {e}")
    return []

def scrape_lever(slug):
    try:
        r = SESSION.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", timeout=15)
        r.raise_for_status()
        return [{"title": j.get("text",""), "location": j.get("categories",{}).get("location",""), "department": j.get("categories",{}).get("department",""), "url": j.get("hostedUrl",""), "posted_at": datetime.fromtimestamp(j["createdAt"]/1000).isoformat() if j.get("createdAt") else ""} for j in r.json()]
    except Exception as e:
        log.warning(f"    Lever error ({slug}): {e}"); return []

def scrape_workday(url):
    try:
        parsed = urlparse(url); host = parsed.hostname; tenant = host.split(".")[0]; board = parsed.path.strip("/").split("/")[0]
        r = SESSION.post(f"https://{host}/wday/cxs/{tenant}/{board}/jobs", json={"appliedFacets":{},"limit":100,"offset":0,"searchText":""}, timeout=20)
        r.raise_for_status()
        return [{"title": j.get("title",""), "location": j.get("locationsText",""), "department": "", "url": urljoin(url, j.get("externalPath","")), "posted_at": j.get("postedOn","")} for j in r.json().get("jobPostings",[])]
    except Exception as e:
        log.warning(f"    Workday error: {e}"); return []

def parse_html_for_jobs(html, base_url):
    if not html: return []
    soup = BeautifulSoup(html, "html.parser")
    jobs, seen = [], set()
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else data.get("@graph", [data])
            for item in items:
                if item.get("@type") in ("JobPosting","jobPosting"):
                    title = item.get("title","")
                    if title and title not in seen:
                        seen.add(title)
                        loc = item.get("jobLocation",{})
                        loc = loc.get("address",{}).get("addressLocality","") if isinstance(loc,dict) else ""
                        jobs.append({"title":title,"location":loc,"department":item.get("occupationalCategory",""),"url":item.get("url",""),"posted_at":item.get("datePosted","")})
        except: pass
    if jobs: return jobs
    for tag, cls_re in [("a", re.compile(r"\bjob\b|\bposition\b|\brole\b",re.I)),("li",re.compile(r"\bjob\b|\bposition\b",re.I)),("div",re.compile(r"job[-_]?card|job[-_]?item|job[-_]?listing",re.I))]:
        for el in soup.find_all(tag, class_=cls_re):
            title_el = el.find(["h2","h3","h4","span"],class_=re.compile(r"title|name|role",re.I)) or (el if el.name=="a" else el.find("a"))
            title = (title_el.get_text(strip=True) if title_el else "")[:120]
            if not title or len(title)<4 or title in seen: continue
            seen.add(title)
            link_el = el if el.name=="a" else el.find("a")
            href = link_el.get("href","") if link_el else ""
            if href and not href.startswith("http"): href = urljoin(base_url, href)
            loc_el = el.find(class_=re.compile(r"location|city|place|office",re.I))
            dept_el = el.find(class_=re.compile(r"dept|department|team|category",re.I))
            jobs.append({"title":title,"location":loc_el.get_text(strip=True) if loc_el else "","department":dept_el.get_text(strip=True) if dept_el else "","url":href,"posted_at":""})
    return jobs

def scrape_with_playwright(url):
    if not PLAYWRIGHT_AVAILABLE: return []
    html = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(user_agent=HEADERS["User-Agent"]).new_page()
        try:
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            for sel in ["[class*='job']","[class*='position']","li"]:
                try: page.wait_for_selector(sel, timeout=8000); break
                except PWTimeout: continue
            time.sleep(2); html = page.content()
        except Exception as e: log.warning(f"    Playwright error: {e}")
        finally: browser.close()
    return parse_html_for_jobs(html, url)

def scrape_url(url):
    company, (ats, payload) = get_company_name(url), detect_ats(url)
    log.info(f"▶  {company:22s} [{ats:12s}]  {url}")
    jobs = []
    if ats == "greenhouse": jobs = scrape_greenhouse(payload)
    elif ats == "lever": jobs = scrape_lever(payload)
    elif ats == "workday":
        jobs = scrape_workday(payload)
        if not jobs: log.info("    Workday 0 → Playwright..."); jobs = scrape_with_playwright(url)
    else:
        try: r = SESSION.get(url, timeout=15); jobs = parse_html_for_jobs(r.text, url)
        except Exception as e: log.warning(f"    requests error: {e}")
        if not jobs: log.info("    HTML 0 → Playwright..."); jobs = scrape_with_playwright(url)
    log.info(f"   └─ {'✅' if jobs else '⚠️ '}  {len(jobs)} jobs")
    return company, jobs

def save_to_excel(results, filename="jobs_output.xlsx"):
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    s = wb.create_sheet("Summary",0); s.append(["Company","Careers Page","Jobs Found","Scraped At"])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    for url,(company,jobs) in zip(CAREER_URLS,results):
        s.append([company,url,len(jobs),ts])
        if not jobs: continue
        ws = wb.create_sheet(re.sub(r"[\\/*?\[\]:]","",company)[:31]); ws.append(["Title","Location","Department","Job URL","Posted At"])
        for j in jobs: ws.append([j.get("title",""),j.get("location",""),j.get("department",""),j.get("url",""),j.get("posted_at","")])
    wb.save(filename); log.info(f"📊  Excel → {filename}")

def save_to_csv(results, filename="jobs_output.csv"):
    ts, rows = datetime.now().strftime("%Y-%m-%d %H:%M"), 0
    with open(filename,"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["Company","Title","Location","Department","Job URL","Posted At","Careers Page","Scraped At"])
        for url,(company,jobs) in zip(CAREER_URLS,results):
            if not jobs: w.writerow([company,"No jobs found","","","","",url,ts]); continue
            for j in jobs: w.writerow([company,j.get("title",""),j.get("location",""),j.get("department",""),j.get("url",""),j.get("posted_at",""),url,ts]); rows+=1
    log.info(f"📄  CSV → {filename}  ({rows} rows)")

def main():
    args = sys.argv[1:]; want_csv = "--csv" in args or "--both" in args; want_excel = "--xlsx" in args or "--both" in args or not want_csv
    log.info(f"🚀  Starting — {len(CAREER_URLS)} companies\n")
    results, total = [], 0
    for url in CAREER_URLS:
        try: company, jobs = scrape_url(url)
        except Exception as e: log.error(f"Fatal: {url}: {e}"); company, jobs = get_company_name(url), []
        results.append((company,jobs)); total += len(jobs); time.sleep(1.0)
    log.info(f"\n✅  Done! {total} total jobs"); 
    if want_excel: save_to_excel(results)
    if want_csv: save_to_csv(results)
    log.info("Files saved in your job-scraper folder.")

if __name__ == "__main__":
    main()
