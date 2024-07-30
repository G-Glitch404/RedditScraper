import logging
import json
import re

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
        try: return self.get(timeout=10.0, impersonate="chrome110", *args, **kwargs)
        except Exception as e:
            self.logger.error(f'got an error while making a GET request: {e}')
            return requests.Response()

    def __get_posts(self, posts_count: int, selector: Selector) -> list[dict]:
        """ extract the post data from the selector """
        def scrape(select: Selector) -> list[dict]:
            return [
                {
                    "postId": post.css('::attr(id)').get('') or None,
                    "authorId": post.css('::attr(author-id)').get('') or None,
                    "subredditId": post.css('::attr(subreddit-id)').get('') or None,
                    "subreddit": post.css('::attr(subreddit-prefixed-name)').get(),
                    "author": author,
                    "title": post.css('::attr(post-title)').get(),
                    "postNsfw": not bool(post.css('::attr(is-post-nsfw)').get('0')),
                    "postType": post.css('::attr(post-type)').get(),
                    "postFlairs": self.extract_text(' '.join(post.css('shreddit-post-flair ::text').extract() or [])) or None,
                    "postIndex": int(post.css('::attr(feedindex)').get('0')),
                    "commentsCount": int(post.css('::attr(comment-count)').get('0')),
                    "upvotes": int(post.css('::attr(score)').get('0')),
                    "content": self.extract_text(''.join(post.css('div[data-post-click-location="text-body"] > div > p ::text').extract() or [])) or None,
                    "timestamp": post.css('::attr(created-timestamp)').get('').split('.')[0] or None,
                    "postLink": (self.api_address + post.css('::attr(permalink)').get('')) or None,
                    "postImageLink": post.css('::attr(content-href)').get(),
                    "authorAvatarLink": post.css('::attr(icon)').get(),
                } for post in select.css('article > shreddit-post[permalink]')
                if (author := post.css('::attr(author)').get('')) and 'automoderator' not in author.lower() or 'bot' not in author.lower()
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

        next_link = lambda: selector.css('faceplate-partial[src][method] ::attr(src)').get()
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
        profile = json.loads(selector.css('reddit-page-data ::attr(data)').get(
            json.dumps({'profile': {"empty": True}})
        ))['profile']

        return {
            "id": profile.get('id', None),
            "name": profile.get('name', None),
            "nsfw": profile.get('isNsfw', None),
            "description": self.extract_text(' '.join(selector.css('p[data-testid="profile-description"] ::text').extract())) or None,
            "post_karma": int(self.extract_text(selector.css('span[data-testid="karma-number"] ::text').get('0')).replace(',', '')),
            "comment_karma": int(self.extract_text(selector.css('span[data-testid="karma-number"]')[-1].css('::text').get('0')).replace(',', '')),
            "cake_day": self.extract_text(' '.join(selector.css('time[data-testid="cake-day"] ::text').extract())).lower() or None,
            "icon": profile.get('icon', None),
        }

    def get_community_info(self, community_name: str) -> dict:
        """ scraping a subreddit information """
        if '/' in community_name: community_name = community_name.replace('/', ' ').strip().split(' ')[-1]
        self.logger.debug(f'scraping all info from community: {community_name}')

        response = self.get(self.api_address + f'/r/{community_name.replace(" ", "")}/').text
        selector = Selector(text=response, type="html")
        subreddit = json.loads(selector.css('reddit-page-data ::attr(data)').get(
            json.dumps({'subreddit': {"empty": True}})
        ))['subreddit']

        return {
            "id": subreddit.get('id', None),
            "name": subreddit.get('name', None),
            "title": selector.css(f'shreddit-subreddit-header[name="{community_name}"] ::attr(display-name)').extract_first(None),
            "prefix": subreddit.get('prefixedName', None),
            "nsfw": subreddit.get('isNsfw', None),
            "quarantined": subreddit.get('isQuarantined', None),
            "description": selector.css(f'shreddit-subreddit-header[name="{community_name}"] ::attr(description)').get('') or None,
            "subscribers": int(selector.css(f'shreddit-subreddit-header[name="{community_name}"] ::attr(subscribers)').get('0')),
            "online": int(selector.css(f'shreddit-subreddit-header[name="{community_name}"] ::attr(active)').get('0')),
            "mods": [
                mod.replace('/', ' ').strip().split(' ')[-1]
                for mod in selector.css('faceplate-tracker[source="moderator_list"] > a ::attr(href)').extract() or ['']
                if mod
            ] or None,
            "rules": self.extract_text(' '.join(selector.css('faceplate-auto-height-animator.block ::text').extract())).split('.') or None,
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

    def get_home_feed(self, posts_count: int = 100) -> list[dict]:
        """ scraping an amount of posts from the homa page feed for browsing reddit normally """
        self.logger.debug(f'scraping {posts_count} from the home feed')

        response: str = self.get(self.api_address + '/?feed=home').text
        selector: Selector = Selector(text=response, type="html")

        yield from self.__get_posts(posts_count, selector)

    def get_post_comments(self, post_id: str, sub_name: str) -> list[dict]:
        """ scrape all the comments from a post """
        def scrape(select: Selector) -> dict[str, str]:
            comment_body = re.sub(
                r'\s{2,}',
                ' ',
                re.sub(r'\n{2,}', '\n',
                       ''.join(
                           select.css('div[slot="comment"] > div ::text').extract() or []
                       )).strip()
            )
            if comment_body != '':
                return {
                    "commentId": comment.css('::attr(thingid)').get(''),
                    "postId": comment.css('::attr(postid)').get(''),
                    "author": comment.css('::attr(author)').get(),
                    "body": comment_body,
                    "commentType": comment.css('::attr(content-type)').get(),
                    "upvotes": int(comment.css('::attr(score)').get('0')),
                    "created_at": select.css('faceplate-timeago ::attr(ts)').get('').split('.')[0] or None,
                    "commentLink": self.api_address + comment.css('::attr(permalink)').get(''),
                }

        threads: list = []

        self.logger.debug(f'scraping all comments from post_id: {post_id}')

        response = self.get(self.api_address + f'/svc/shreddit/comments/{sub_name}/{post_id}?render-mode=partial')
        comments_section = Selector(text=response.text, type="html").css('shreddit-comment[permalink]')
        for comment in comments_section:
            if (author := comment.css('::attr(author)').get('')) and 'automoderator' in author.lower() or 'bot' in author.lower(): continue
            if comment.css('::attr(depth)').get('') == '0':
                replies = []

                for reply in comments_section[comments_section.index(comment) + 1:]:
                    if comment == reply: continue
                    if reply.css('::attr(depth)').get('') == '0': break

                    comment_section = scrape(reply)
                    if comment_section:
                        replies.append(comment_section)

                threads.append({
                    "thread": scrape(comment),
                    "threadReplies": replies,
                })

        self.logger.debug(f'found: {len(comments_section)} comments on post_id: {post_id}')
        threads.append({"commentsCount": len(comments_section)})
        for comments in threads: yield comments
