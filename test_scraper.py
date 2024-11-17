from bs4 import BeautifulSoup
import requests

# list of websites to scrape
urls = [
    "https://www.gov.uk/browse/benefits",
    "https://www.gov.uk/browse/benefits/manage-your-benefit",
    "https://www.gov.uk/browse/benefits/manage-your-benefit",
    "https://www.gov.uk/browse/benefits/looking-for-work",
    "https://www.gov.uk/browse/benefits/unable-to-work",
       "https://www.gov.uk/browse/benefits/families",
         "https://www.gov.uk/browse/benefits/disability",
                "https://www.gov.uk/browse/benefits/help-for-carers",
                  "https://www.gov.uk/browse/benefits/low-income",
                   "https://www.gov.uk/browse/benefits/bereavement",
                   "https://www.gov.uk/sure-start-maternity-grant",
                   "https://www.gov.uk/paternity-pay-leave",
                   "https://www.gov.uk/child-tax-credit",
                   "https://www.gov.uk/child-benefit",
                   "https://www.gov.uk/child-trust-fund",
                   "https://www.gov.uk/free-school-meals",
                   "https://www.gov.uk/tax-credits",
                   "https://www.gov.uk/tax-credits-for-families",
                   "https://www.gov.uk/tax-credits-for-disabled-people",
                   "https://www.gov.uk/tax-credits-for-carers",
                   "https://www.gov.uk/tax-credits-for-low-income-families",
                   "https://www.gov.uk/tax-credits-for-bereaved-parents",
                   "https://www.gov.uk/tax-credits-for-disabled-people",
                   "https://www.gov.uk/tax-credits-for-carers",
                   "https://www.gov.uk/tax-credits-for-low-income-families",
                   "https://www.gov.uk/tax-credits-for-bereaved-parents",
                   "https://www.gov.uk/child-benefit-calculator"


]

with open('website_content.txt', 'w', encoding='utf-8') as file:
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.title.string if soup.title else "No title found"
            
            # Get the main content
            text = soup.get_text(strip=True)
            
            file.write(f"\n{'='*50}\n")
            file.write(f"URL: {url}\n")
            file.write(f"Title: {title}\n")
            file.write(f"Content:\n{text}\n")
            
            print(f"Successfully scraped {url}")
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")