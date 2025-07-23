#Wikipedia Geoprovenance Analysis 

import requests
import pandas as pd
from urllib.parse import urlparse
import tldextract
import re
from typing import Dict, List, Optional
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WikipediaGeoProvenanceAnalyzer:

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikipediaGeoProvenance'
        })

    def extract_citations_from_article(self, article_title: str, lang: str) -> List[Dict]:
        """
        Extract citations from a Wikipedia article using the MediaWiki API.

        Args:
            article_title: Title of the Wikipedia article
            lang: Language code ('en', 'fr', or 'de') Need to manually change the language

        Returns:
            List of citation dictionaries with URLs and metadata
        """
        api_url = f"https://{lang}.wikipedia.org/w/api.php"

        params = {
            'action': 'parse',
            'page': article_title,
            'format': 'json',
            'prop': 'wikitext'
        }

        try:
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'parse' not in data:
                logger.error(f"Article '{article_title}' not found or inaccessible")
                return []

            wikitext = data['parse']['wikitext']['*']
            citations = self._parse_citations_from_wikitext(wikitext)

            logger.info(f"Extracted {len(citations)} citations from '{article_title}'")
            return citations

        except Exception as e:
            logger.error(f"Error fetching article '{article_title}': {e}")
            return []

    def _parse_citations_from_wikitext(self, wikitext: str) -> List[Dict]:
        """
        Parse citations from Wikipedia wikitext markup.
        Extracts URLs from various citation templates and ref tags.
        """
        citations = []

        # Pattern to match URLs in ref tags and citation templates
        url_patterns = [
            r'url\s*=\s*([^|}\n]+)',  # url= parameter
            r'https?://[^\s|}]+',      # Direct HTTP URLs
        ]

        for pattern in url_patterns:
            matches = re.finditer(pattern, wikitext, re.IGNORECASE)
            for match in matches:
                url = match.group(1) if pattern.startswith('url') else match.group(0)
                url = url.strip().rstrip('|}')

                if self._is_valid_url(url):
                    citations.append({
                        'url': url,
                        'domain': urlparse(url).netloc,
                    })

        return list({c['url']: c for c in citations}.values())  # Remove duplicates

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and external (not Wikipedia internal)."""
        try:
            parsed = urlparse(url)
            return (parsed.scheme in ['http', 'https'] and 
                   parsed.netloc and 
                   'wikipedia.org' not in parsed.netloc.lower())
        except:
            return False

    def analyze_url_geoprovenance(self, urls: List[str]) -> pd.DataFrame:
        """
        Analyze geoprovenance of URLs using multiple signals.
        Implements the methodology from Sen et al. 2015 (https://github.com/shilad/geo-provenance).

        Args:
            urls: List of URLs to analyze

        Returns:
            DataFrame with geoprovenance analysis results
        """
        results = []

        for url in urls:
            try:
                extracted = tldextract.extract(url)
                domain_info = {
                    'url': url,
                    'domain': extracted.domain + '.' + extracted.suffix,
                    'subdomain': extracted.subdomain,
                    'tld': extracted.suffix,
                    'country_from_tld': self._get_country_from_tld(extracted.suffix)
                }

                # Add WHOIS and other analysis here in full implementation
                results.append(domain_info)

            except Exception as e:
                logger.warning(f"Error analyzing URL {url}: {e}")
                continue

        return pd.DataFrame(results)

    def _get_country_from_tld(self, tld: str) -> Optional[str]:
        """Map domain to country"""
        # Need to maybe add more mappings
        country_tlds = {
            'uk': 'United Kingdom', 'us': 'United States', 'de': 'Germany',
            'fr': 'France', 'jp': 'Japan', 'ca': 'Canada', 'au': 'Australia',
            'ch': 'Switzerland', 'cn': 'China', 'es': 'Spain', 'it': 'Italy',
            'nl': 'Netherlands', 'se': 'Sweden', 'no': 'Norway', 'ru': 'Russia',
            'br': 'Brazil', 'in': 'India', 'kr': 'South Korea', 'pl': 'Poland'
        }
        return country_tlds.get(tld.lower())

    def generate_geoprovenance_report(self, article_title: str, lang: str) -> Dict:
        """
        Generate a complete geoprovenance report for an article.

        Args:
            article_title: Wikipedia article to analyze
            lang: Language code ('en', 'fr', or 'de')

        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting geoprovenance analysis for '{article_title}' ({lang})")

        # Extract citations
        citations = self.extract_citations_from_article(article_title, lang)

        if not citations:
            return {'error': 'No citations found or article inaccessible'}

        # Analyze source geoprovenance
        urls = [c['url'] for c in citations]
        source_analysis = self.analyze_url_geoprovenance(urls)

        # Compile report
        report = {
            'article_title': article_title,
            'total_citations': len(citations),
            'unique_domains': source_analysis['domain'].nunique(),
            'country_distribution': source_analysis['country_from_tld'].value_counts().to_dict(),
            'tld_distribution': source_analysis['tld'].value_counts().to_dict(),
            'citations_with_country_tld': source_analysis['country_from_tld'].notna().sum(),
            'citations': citations,
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }

        logger.info(f"Analysis complete. Found {report['total_citations']} citations from {report['unique_domains']} unique domains")

        return report

# Example usage
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = WikipediaGeoProvenanceAnalyzer()

    # Analyze a sample article
    # Manually comment or uncomment articles to test depending on language
    # Uncomment the articles that needs to be analyzed
    # Comment all the articles that are not needed
    sample_articles = [
        # "Norwegian Sea",
        # "Salzburg",
        # "Egyptian–Hittite peace treaty",
        # "Abraham Lincoln",
        # "The Legend of Zelda: Ocarina of Time",
        # "Blomberg–Fritsch affair",
        # "Babylon",
        # "Calisto (moon)",
        # "Panama Canal",
        # "Kitty Clive",
        # "Roman temple of Bziza",
        # "Rochester Castle",
        # "Statue of Liberty", 
        # "El Greco",
        # "History of evolutionary thought",
        # "raccoon",
        # "Elisabeth Dmitrieff",
        # "Kardashev Scale",
        # "Ganymede (moon)",
        # "Martin Luther King",
        # "Dromaeosauridae",
        # "Aristotle",
        # "Roswell incident"
        # "Mer de Norvège",
        # "Salzbourg",
        # "Traité de paix égypto-hittite",
        # "Abraham Lincoln",
        # "The Legend of Zelda: Ocarina of Time",
        # "Affaire Blomberg-Fritsch",
        # "Babylone",
        # "Callisto (lune)",
        # "Canal de Panama",
        # "Catherine Clive",
        # "Temple romain de Bziza",
        # "Château de Rochester",
        # "Statue de la Liberté",
        # "Le Greco",
        # "Histoire de la pensée évolutionniste",
        # "Raton laveur",
        # "Élisabeth Dmitrieff",
        # "Échelle de Kardachev",
        # "Ganymède (lune)",
        # "Martin Luther King",
        # "Dromaeosauridae",
        # "Aristote",
        # "Affaire de Roswell"
        "Europäisches Nordmeer",
        "Salzburg",
        "Ägyptisch-Hethitischer Friedensvertrag",
        "Abraham Lincoln",
        "The Legend of Zelda: Ocarina of Time",
        "Blomberg-Fritsch-Krise",
        "Babylon",
        "Kallisto (Mond)",
        "Panamakanal",
        "Kitty Clive",
        "Tempel von Bziza",
        "Rochester Castle",
        "Freiheitsstatue",
        "El Greco",
        "Geschichte der Evolutionstheorie",
        "Waschbär",
        "Elisabeth Dmitrieff",
        "Kardaschow-Skala",
        "Ganymed (Mond)",
        "Martin Luther King",
        "Dromaeosauridae",
        "Aristoteles",
        "Roswell-Zwischenfall"
    ]

    results = {}

    for article in sample_articles:
        try:
            report = analyzer.generate_geoprovenance_report(article, lang='de')  # Change 'de' to 'fr' for French or 'en' for English
            results[article] = report

            # Print summary
            if 'error' not in report:
                print(f"\n{article}:")
                print(f"  Citations: {report['total_citations']}")
                print(f"  Unique domains: {report['unique_domains']}")
                print(f"  Top countries: {dict(list(report['country_distribution'].items())[:3])}")

        except Exception as e:
            print(f"Error analyzing '{article}': {e}")
            continue

    # Save results
    with open('geoprovenance_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nAnalysis complete! Results saved to 'geoprovenance_results.json'")
