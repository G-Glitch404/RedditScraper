import logging
import json
import re
from selector import select as se

from logger import Logger
from decorators import retry

from curl_cffi.requests import Session
from curl_cffi import requests
from parsel import Selector


class RedditScraper(Session):
    api_address = 'https://www.reddit.com'

    def __init__(self, proxy: str = None) -> None:
        super(RedditScraper, self).__init__()
        self.headers.update({"user-agent": "Mozilla/5 (X11; Linux x86_64; rv:10) Gecko/20100101 Firefox/10"})

        self.logger = Logger(logging.getLogger('RedditScraper'), {})
        self.extract_text = lambda text: re.sub(r'\n|\s{2,}', '', text).strip()

        if proxy: self.proxies = {"http": proxy, "https": proxy}

    @retry
    def get(self, *args, **kwargs):
        """ GET request using Session """
        try: return super(RedditScraper, self).get(timeout=10.0, impersonate="chrome110", *args, **kwargs)
        except Exception as e:
            self.logger.error(f'got an error while making a GET request: {e}')
            return requests.Response()

    @retry
    def post(self, *args, **kwargs):
        """ GET request using Session """
        try: return super(RedditScraper, self).post(timeout=10.0, impersonate="chrome110", *args, **kwargs)
        except Exception as e:
            self.logger.error(f'got an error while making a POST request: {e}')
            return requests.Response()

    def __get_posts(self, posts_count: int, selector: Selector) -> list[dict]:
        """ extract the post data from the selector """
        def scrape(select: Selector) -> list[dict]:
            return [
                {
                    "postId": post.css(se['post_id']).get('') or None,
                    "authorId": post.css(se['author_id']).get('') or None,
                    "subredditId": post.css(se['subreddit_id']).get('') or None,
                    "subreddit": post.css(se['subreddit']).get(),
                    "author": author,
                    "title": post.css(se['post_title']).get(),
                    "postNsfw": not bool(post.css(se['post_nsfw']).get('0')),
                    "postType": post.css(se['post_type']).get(),
                    "postFlairs": self.extract_text(' '.join(post.css(se['post_flairs']).extract() or [])) or None,
                    "postIndex": int(post.css(se['post_index']).get('0')),
                    "commentsCount": int(post.css(se['comments_count']).get('0')),
                    "upvotes": int(post.css(se['post_upvotes']).get('0')),
                    "content": self.extract_text(''.join(post.css(se['content']).extract() or [])) or None,
                    "timestamp": post.css(se['timestamp']).get('').split('.')[0] or None,
                    "postLink": (self.api_address + post.css(se['post_link']).get('')) or None,
                    "postImageLink": post.css(se['post_image_link']).get(),
                    "authorAvatarLink": post.css(se['icon']).get(),
                } for post in select.css(se['post'])
                if (author := post.css(se['post_author']).get('')) and 'automoderator' not in author.lower() or 'bot' not in author.lower()
            ]

        posts: list = []

        if posts_count is None: posts_count: int = 10

        page = scrape(selector)
        if len(page) <= 0:
            self.logger.debug(f'no posts found for the selected subreddit')
            return page

        self.logger.debug(f'scraping {posts_count} posts from subreddit {page[0]["subreddit"]}')
        posts.extend(page)
        for post in page: yield post

        next_link = lambda: selector.css(se['posts_cursor']).get()
        last_pull_count: int = 0
        while next_link() and len(posts) < posts_count:
            response: str = self.get(self.api_address + next_link()).text
            selector: Selector = Selector(text=response, type="html")
            page = scrape(selector)
            posts.extend(page)

            if last_pull_count == len(posts): break
            last_pull_count = len(posts)

            for post in page: yield post

        self.logger.debug(f'scraped and found {len(posts)} posts from subreddit {page[0]["subreddit"]}')

    def get_user_info(self, user_name: str):
        """ scraping a user information """
        if '/' in user_name: user_name = user_name.replace('/', ' ').strip().split(' ')[-1]
        self.logger.debug(f'scraping all info from user: {user_name}')

        response = self.get(self.api_address + f'/user/{user_name.replace(" ", "")}/').text
        selector = Selector(text=response, type="html")
        profile = json.loads(selector.css(se['user_profile']).get(
            json.dumps({'profile': {"empty": True}})  # if user-profile is empty then default to this dict
        ))['profile']

        return {
            "id": profile.get('id', None),
            "name": profile.get('name', None),
            "nsfw": profile.get('isNsfw', None),
            "description": self.extract_text(' '.join(selector.css(se['user_description']).extract())) or None,
            "post_karma": int(self.extract_text(selector.css(se["posts_karma"]).get('0')).replace(',', '')),
            "comment_karma": int(self.extract_text(selector.css(se['comments_karma'])[-1].css('::text').get('0')).replace(',', '')),
            "cake_day": self.extract_text(' '.join(selector.css(se['cake_day']).extract())).lower() or None,
            "icon": profile.get('icon', None),
        }

    def get_community_info(self, community_name: str) -> dict:
        """ scraping a subreddit information """
        if '/' in community_name: community_name = community_name.replace('/', ' ').strip().split(' ')[-1]
        self.logger.debug(f'scraping all info from community: {community_name}')

        response = self.get(self.api_address + f'/r/{community_name.replace(" ", "")}/').text
        selector = Selector(text=response, type="html")
        subreddit = json.loads(selector.css(se['subreddit_homepage']).get(
            json.dumps({'subreddit': {"empty": True}})
        ))['subreddit']

        return {
            "id": subreddit.get('id', None),
            "name": subreddit.get('name', None),
            "title": selector.css(se['subreddit_title'].replace("{community_name}", community_name)).extract_first(None),
            "prefix": subreddit.get('prefixedName', None),
            "nsfw": subreddit.get('isNsfw', None),
            "quarantined": subreddit.get('isQuarantined', None),
            "description": selector.css(se['subreddit_description'].replace("{community_name}", community_name)).get('') or None,
            "subscribers": int(selector.css(se['subreddit_members_count'].replace("{community_name}", community_name)).get('0')),
            "online": int(selector.css(se['subreddit_online_members_count']).get('0')),
            "mods": [
                mod.replace('/', ' ').strip().split(' ')[-1]
                for mod in selector.css(se['subreddit_moderators']).extract() or ['']
                if mod
            ] or None,
            "rules": self.extract_text(' '.join(selector.css(se['subreddit_rules']).extract())).split('.') or None,
            'icon': subreddit.get('communityIcon', None)
        }

    def get_user_posts(self, user_name: str, posts_count: int = 100) -> list[dict]:
        """  scraping an amount of posts from a user """
        if '/' in user_name: user_name = user_name.split('/')[-1]
        self.logger.debug(f'scraping {posts_count} from user: {user_name}')

        response: str = self.get(self.api_address + f'/user/{user_name}/submitted').text
        selector: Selector = Selector(text=response, type="html")

        return self.__get_posts(posts_count, selector)

    def get_community_posts(self, community_name: str, posts_count: int = 100) -> list[dict]:
        """ scraping an amount of posts from a subreddit """
        if '/' in community_name: community_name = community_name.split('/')[-1]
        self.logger.debug(f'scraping {posts_count} from subreddit: {community_name}')

        response: str = self.get(self.api_address + f'/r/{community_name}').text
        selector: Selector = Selector(text=response, type="html")

        return self.__get_posts(posts_count, selector)

    def get_home_feed_posts(self, posts_count: int = 100) -> list[dict]:
        """ scraping an amount of posts from the homa page feed for browsing reddit normally """
        self.logger.debug(f'scraping {posts_count} from the home feed')

        response: str = self.get(self.api_address + '/?feed=home').text
        selector: Selector = Selector(text=response, type="html")

        yield from self.__get_posts(posts_count, selector)

    def get_post_comments(self, post_id: str, sub_name: str) -> list[dict]:
        """ scrape all the comments from a post """
        def get_comment_section(html: str) -> dict:
            comments_section: list[Selector] = Selector(html, type="html").css(se['comments_section'])
            for comment in comments_section:
                if (author := comment.css(se['comment_author']).get('')) and 'automoderator' in author.lower() or 'bot' in author.lower(): continue
                if comment.css(se['comment_depth']).get('') == '0':
                    replies = []

                    for reply in comments_section[comments_section.index(comment) + 1:]:
                        if comment == reply: continue
                        if reply.css(se['comment_depth']).get('') == '0': break

                        comment_section = scrape(reply)
                        if comment_section:
                            replies.append(comment_section)

                    yield {
                        "thread": scrape(comment),
                        "replies": replies,
                    }

        def scrape(select: Selector) -> dict[str, str]:
            comment_body = re.sub(
                r'\s{2,}', ' ',  # filtering multiple spaces to one space
                re.sub(r'\n{2,}', '\n',  # filtering multiple newlines "\n" to one newline
                       ''.join(
                           select.css(se['comment_body']).extract() or []
                       )).strip()
            )
            if comment_body != '':
                return {
                    "commentId": select.css(se['comment_id']).get(''),
                    "postId": select.css(se['comment_post_id']).get(''),
                    "author": select.css(se['comment_author']).get(),
                    "body": comment_body,
                    "commentType": select.css(se['comment_datatype']).get(),
                    "upvotes": int(select.css(se['comment_upvotes']).get('0')),
                    "created_at": select.css(se['comment_timestamp']).get('').split('.')[0] or None,
                    "commentLink": self.api_address + select.css(se['comment_link']).get(''),
                }

        if "t3_" not in post_id: post_id = f't3_{post_id}'
        self.logger.debug(f'scraping comments from post_id: {post_id}')

        response = self.get(self.api_address + f'/svc/shreddit/comments/{sub_name}/{post_id}?render-mode=partial').text  # this response will change after each request
        next_link = lambda html: (Selector(text=html, type="html").css(se['comments_cursor']).getall() or [False])[-1]
        while cursor := next_link(response):
            if not (link := Selector(text=response, type="html").css(se['next_comments_page']).get()): break
            yield from get_comment_section(response)
            print(response)
            response = self.post(
                self.api_address + link,
                data={
                    'cursor': cursor,
                    'csrf_token': self.cookies['csrf_token']
                }
            ).text

        self.logger.debug(f'finished scraping comments from post_id: {post_id}')


if __name__ == "__main__":
    api = RedditScraper()
    total_comments = 0
    for i in api.get_post_comments('t3_1efec9q', 'r/AITAH'):
        if len(i) > 1:
            print(i)
            total_comments += len(i.get('replies', []))
    print('total scraped comments:', total_comments)
    exit(0)

    for i in api.get_home_feed(): print(i)
    for i in api.get_community_info('r/AskReddit'): print(i)
    for i in api.get_community_posts('AskReddit'): print(i)
    for i in api.get_user_posts(''): print(i)
    for i in api.get_user_info(''): print(i)
