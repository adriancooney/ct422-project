import pycurl
import logging
from os.path import join, basename
from bs4 import BeautifulSoup
from urllib import urlencode
from StringIO import StringIO

class Scraper:
    @staticmethod
    def request_search_page(module):
        """Perform a request to mis.nuigalway.ie and return the HTML of the search page."""
        
        buffer = StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL, "https://www.mis.nuigalway.ie/regexam/paper_index_search_results.asp")
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.POSTFIELDS, urlencode({ "module": module }))
        c.perform()
        c.close()
        
        return buffer.getvalue()

    @staticmethod
    def get_papers(module):
        """Perform a request to the examination center and return array of papers"""
        
        html = Scraper.request_search_page(module)
        
        soup = BeautifulSoup(html, "html.parser")

        if soup.p != None and "maximum" in soup.p.get_text():
            raise ValueError("Too many results return from mis with module code %s, nuig is hurt." % module)

        if soup.b != None and "No matches" in soup.b.get_text():
            return []

        rows = soup.table.find_all("tr")
        papers = []
        
        # Skip the table header
        for i in range(1, len(rows)):
            row = rows[i]
            
            cells = row.find_all("td")
        
            # Extract the data
            paper = {
                "year": cells[0].text.strip(),
                "module": cells[1].text.strip(),
                "name": cells[2].text.strip(),
                "paper": cells[3].text.strip(),
                "sitting": cells[4].text.strip(),
                "period": cells[5].text.strip()
            }
            
            # Sometimes a paper is unavailable, we can check this if there is no "a" element
            # in the cell[6]. Sometimes you also get just Not Available
            if not (cells[6].a == None or cells[6].a.get("href") == None):
                paper["link"] = Scraper.generate_paper_link(paper)
            else:
                paper["link"] = None
            
            papers.append(paper)
        
        return papers

    period = {
        "Semester 1": 5,
        "Autumn": 3,
        "Summer": 2,
        "Summer Repeats/Resits": 13,
        "Spring": 0
    }
    
    sitting = {
        "First Sitting": 1,
        "Second Sitting": 2
    }

    @staticmethod
    def generate_paper_link(paper):
        """Dirty implementation of the NUIG paper storage naming scheme. This saves us following that 301 to get the link to the actual PDF."""
        
        return "https://www.mis.nuigalway.ie/papers_public/{year}/{module_alpha}/{year}_{module}_{sitting}_{period}.PDF".format(
            year = paper["year"].replace("/", "_"),
            module_alpha = paper["module"][:2],
            module = paper["module"].replace("-", "_"),
            period = Scraper.period[paper["period"]],
            sitting = Scraper.sitting[paper["sitting"]]
        )

    @staticmethod
    def download_paper(paper, path):
        """Download the PDF paper and put in directory `path`."""
        filename = join(path, basename(paper["link"]).lower())
        
        logging.info("Downloading \"%s %s\" to %s" % (paper["module"], paper["paper"], filename))
        with open(filename, "wb") as output:
            c = pycurl.Curl()
            c.setopt(c.URL, paper["link"])
            c.setopt(c.WRITEDATA, output)
            c.perform()
            c.close()

    @staticmethod
    def download_module(module, path):
        for paper in Scaper.get_papers(module):
            Scraper.download_paper(paper, path)