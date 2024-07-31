from curl_cffi.requests import Session


class CommentsExtractor:
    def __init__(self, session: Session, post_id: str, subreddit_name: str) -> None:
        self.session = session
        self.post_id = post_id
        self.subreddit_name = subreddit_name

        self.logger = Logger(logging.getLogger('CommentsExtractor'), {})
        self.extract_text = lambda text: re.sub(r'\n|\s{2,}', '', text).strip()

