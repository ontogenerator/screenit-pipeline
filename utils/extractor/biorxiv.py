import requests
from bs4 import BeautifulSoup
from datetime import date
import re


class Preprint:
    def __init__(self, doi, is_biorxiv):
        self.doi = doi
        self.html = None
        if is_biorxiv:
            self.url = 'https://biorxiv.org/cgi/content/' + doi
        elif is_biorxiv is None:
            self.url = 'https://medrxiv.org/cgi/content/' + doi
            r = requests.get(self.url)
            if r.status_code == 200:
                self.html = r.text
            else:
                self.url = 'https://biorxiv.org/cgi/content/' + doi
        else:
            self.url = 'https://medrxiv.org/cgi/content/' + doi

    def get_full_text_html(self):
        html = requests.get(self.url + '.full').text
        if 'data-panel-name="article_tab_full_text"' not in html:
            raise Exception('Full text not available for', self.url)
        paper = []
        soup = BeautifulSoup(html, 'html.parser')
        for header in soup.find_all('h2')[:-2]:
            if header.text.lower() in ['footnotes', 'abbreviations', 'references']:
                continue
            paper.append({'header': header.text, 'content': ''})
            for tag in header.parent:
                if tag.name == 'p':
                    paper[-1]['content'] += tag.text + ' '
                if tag.name == 'div' and ('subsection' in tag['class'] or 'section' in tag['class']):
                    for subtag in tag:
                        if subtag.name == 'h3':
                            paper[-1]['content'] += subtag.text + ': '
                        if subtag.name == 'p':
                            paper[-1]['content'] += subtag.text + ' '
            paper[-1]['content'] = paper[-1]['content'].strip()
        return paper

    def is_full_text_html(self):
        if not self.html:
            self.html = requests.get(self.url).text
        return 'data-panel-name="article_tab_full_text' in self.html

    def get_pdf(self, file):
        with open(file, 'wb') as f:
            f.write(requests.get(self.url + '.full.pdf').content)

    def get_data_code_statement(self):
        if 'medrxiv.org' not in self.url:
            return ''
        if not self.html:
            self.html = requests.get(self.url).text
        return ' '.join(re.split('<h2 class="">Data Availability</h2><p id="p-[0-9]+">', self.html)[1].split('</p></div>')[0].split()).strip()

    def get_metadata(self):
        if not self.html:
            self.html = requests.get(self.url).text
        soup = BeautifulSoup(self.html, 'html.parser')
        metadata = {'title': '', 'abstract': '', 'authors': [], 'date': None}
        for meta in soup.findAll('meta'):
            if meta.get('name') == 'DC.Title':
                metadata['title'] = BeautifulSoup(meta.get('content'), 'html.parser').get_text()
            if meta.get('name') == 'DC.Description':
                metadata['abstract'] = BeautifulSoup(meta.get('content'), 'html.parser').get_text().replace('\n', '')
            if meta.get('name') == 'DC.Date':
                metadata['date'] = date(*[int(num) for num in meta.get('content').split('-')])
            if meta.get('name') == 'DC.Contributor':
                metadata['authors'].append(BeautifulSoup(meta.get('content'), 'html.parser').get_text())
        return metadata
