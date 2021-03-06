from typing import List, Dict, Optional

from bs4 import BeautifulSoup

from time import sleep
from threading import Thread
from constants import Shop
from scraper.base.article_subscriber import ArticleSubscriber
from scraper.base.base_article import BaseArticle
import requests


class BaseShopScraper:
    SHOP: Shop

    def __init__(self):
        self.subscribers: List[ArticleSubscriber] = []
        self.article_states: Dict[str, bool] = dict()
        self.articles: List[BaseArticle] = list()
        runner_thread = Thread(target=self.run, daemon=True)
        runner_thread.start()

    def watch(self, article: BaseArticle):
        self.article_states[article.name] = False
        self.articles.append(article)

    def add_subscriber(self, subscriber: ArticleSubscriber):
        self.subscribers.append(subscriber)

    def remove_subscriber(self, subscriber: ArticleSubscriber):
        self.subscribers.remove(subscriber)

    def scrape_article(self, soup: BeautifulSoup, additional_data=None) -> bool:
        raise NotImplementedError()

    def prepare_scraping(self, article: BaseArticle) -> BeautifulSoup:
        url = article.article_entries.get(self.SHOP)
        request = requests.get(url, headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'})
        if request.status_code == 200:
            return BeautifulSoup(request.content, "html.parser")
        else:
            print(request)
            raise RuntimeError("Request failed")

    def notify_subscribers(self, article: BaseArticle):
        for subscriber in self.subscribers:
            subscriber.on_change(self.article_states[article.name], self.SHOP, article)

    def run(self):
        while True:
            for article in self.articles:
                try:
                    available = self.scrape_article(self.prepare_scraping(article), article.additional_data)
                    if available != self.article_states[article.name]:
                        self.article_states[article.name] = available
                        self.notify_subscribers(article)
                except Exception as err:
                    print(err)
                    pass
                sleep(30)

    def name(self) -> str:
        return str(self.SHOP.name).replace("_", " ")

    def get_status(self, article) -> Optional[str]:
        if article not in self.articles:
            return None
        return "*[{}]({})*    _{}_".format(str(self.name()), article.article_entries[self.SHOP],
                                           "Available" if self.article_states[article.name] else "Not available")
