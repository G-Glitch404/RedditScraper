# The Ultimate Reddit Scraper

[Open-source](https://github.com/G-Glitch404/RedditScraper) actor to scrape Reddit subreddits, posts, feeds, search results, and comment threads from Reddit JSON endpoints with flexible filtering, media extraction, and structured output.

## Current limitations and downsides of The Ultimate Reddit Scraper
* I'll do my best fixing all this in the next versions
* Will probably need an account cookies (loid, reddit_session)
* Doesn't return comments replies
* has a 100 requests per min rate-limit per account cookies 
  - to bypass the rate-limit use different accounts (cookies) in multiple runs
* The Logs tab for every run contains detailed information about the run, including errors, warnings, and debug information

## What does The Ultimate Reddit Scraper do?

**The Ultimate Reddit Scraper** is a **lite-wight** and **high-performance** Apify Actor for crawling Reddit content. It can extract subreddit feeds, post threads, user pages, custom feeds, and custom search URLs, while also collecting nested comments, media links, and detailed post metadata.

It is built for fast structured extraction and for building datasets you can use in analytics, monitoring, research, archiving, NLP, automation workflows, and content intelligence.

### The Ultimate Reddit Scraper can scrape

* Subreddit feeds and community posts
* Individual post threads
* User pages and profile-related content
* Custom feed URLs
* Custom search URLs
* Full comment section of a post (only top-level comments)
* Media links, preview images, gallery images, and video data (all if available)
* Post metadata such as score, awards, upvotes, and moderation flags, etc.

---

## Why scrape Reddit?

Reddit is one of the largest discussion platforms on the internet and a valuable source of real-world conversations, opinions, trends, and media. It is useful for tracking what people are saying, what content is gaining traction, and how topics evolve over time.

Here are just some of the ways you could use Reddit data:

* Sentiment analysis and brand monitoring
* Trend detection and topic research
* Market intelligence and competitive analysis
* Academic research on communities and behavior
* Archiving discussions and public conversations
* Training datasets for NLP and machine learning
* Monitoring public reaction to events, products, or campaigns

If you would like more inspiration on how scraping Reddit could help your business or organization, check out the [Apify industry pages](https://apify.com/industries).

---

## Supported URL types

You can start the Actor from different kinds of Reddit URLs. The table below explains what each one does.

| URL example                                                                                                | What the scraper does                              |
|------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| `https://www.reddit.com/r/technology/`                                                                     | Scrapes posts from the subreddit feed              || `https://www.reddit.com/r/technology/new/`                                                                      | Scrapes the “new” sorting view for the subreddit               |
| `https://www.reddit.com/r/technology/top/`                                                                 | Scrapes the “top” sorting view for the subreddit   |
| `https://www.reddit.com/r/mildlyinfuriating/comments/1txskkj/resurant_charges_extra_to_take_toppings_off/` | Scrapes a single post and its metadata             || `https://www.reddit.com/user/someusername/`                                                                     | Scrapes user-related content where supported by the source URL |
| `https://www.reddit.com/r/all/`                                                                            | Scrapes the global feed across Reddit              |
| `https://www.reddit.com/search/?q=bitcoin`                                                                 | Scrapes search-based results for the query         |
| `https://www.reddit.com/r/mildlyinfuriating/search/?q=hot+dog`                                             | Scrapes search results inside a specific subreddit |
| `https://www.reddit.com/r/funny/`                                                                          | Scrapes posts from the subreddit feed              |
| `https://www.reddit.com/r/funny/comments/.../`                                                             | Scrapes a single post and optionally its comments  |

---

## How to scrape Reddit

It is easy to use **The Ultimate Reddit Scraper**.

1. Click on **Try for free**
2. Enter the Reddit URLs you want to scrape
3. Configure optional filters like keywords, comment crawling, and field selection
4. Click on **Run**
5. Preview or download your data from the **Dataset** tab

---

## Input reference

| Input                |    Type | Required | Description                                                   |
|----------------------|--------:|---------:|---------------------------------------------------------------|
| `links`              |   array |      yes | Reddit URLs to crawl                                          |
| `maxPosts`           | integer |      yes | Maximum number of posts to collect per link                   |
| `cookies`            |  object |       no | Optional authenticated Reddit cookies (needed for deep crawl) |
| `deepCrawl`          | boolean |       no | Try to crawl deeper comment trees                             |
| `includeComments`    | boolean |       no | Include comments for post URLs                                |
| `keywords`           |   array |       no | Keep only posts matching keywords                             |
| `filterFields`       |   array |       no | Drop posts missing selected fields                            |
| `stopDate`           |  string |       no | Don't return posts older than this date                       |
| `includeCrossposts`  | boolean |       no | Keep or skip crossposts                                       |
| `proxyConfiguration` |  object |       no | Apify Proxy or custom proxy settings                          |

---

## Input options

## Links

**Type:** array
**Editor:** `requestListSources`
**Required:** yes
**Minimum items:** 1
**Maximum items:** 100

This is the main starting point for the Actor. Add one or more Reddit URLs here.

The Actor supports:

* subreddit URLs
* post URLs
* user URLs
* custom feed URLs
* custom search URLs

### How it behaves

* Each link is processed independently
* `maxPosts` applies per link
* If you provide multiple links, the Actor will crawl them one by one until the limit is reached for each source
* If a source is a post URL, the Actor can extract that post and its related data
* If a source is a feed or subreddit URL, the Actor crawls posts from that source

### Important notes

* Keep the number of links reasonable if you are scraping large sources
* Very large source lists with very high `maxPosts` values can hit Reddit rate limiting
* For large jobs, start with a small number of links first
* If you only need one post thread, provide a single post URL

### examples

* One subreddit URL for broad post discovery
* One post URL when you need comments and post metadata
* Multiple subreddit URLs when you need a topic-wide dataset
* A subreddit feed URL plus a search URL when you want both curated and query-based content
* A user URL when you want to scrape all posts by a specific user

---

## Maximum posts per link

**Type:** integer
**Required:** yes
**Minimum:** 10
**Maximum:** 10000

This sets the maximum number of posts to collect from each provided link.

### Important behavior

This value is applied **per link**, not globally.

Example:

* `maxPosts = 100`
* `links = 10 subreddit URLs`

The Actor will attempt to collect up to **100 posts from each subreddit**, which means up to **1000 posts total**.

### Recommended use

* Use a smaller value for testing
* Use a moderate value for large subreddit feeds
* Avoid very large values across many links unless you know the source is stable

### Why this matters

Reddit may start rate limiting aggressive crawling if you ask for too much data from many sources at once.
accounts are limited to 100 requests per minute if you exceed this the crawler will start failing and the actor will stop

### Practical guidance

* `10` to `50` for quick checks
* `100` to `1000` for normal scraping
* Higher values only when you need large archives

---

## Account cookies

**Type:** object
**Editor:** `json`
**Optional:** yes

This field lets you provide authenticated Reddit cookies.

### Expected usage

Use this if you want to run the scraper with a logged-in Reddit session

Required cookies keys:

* `loid`
* `reddit_session`

### When to use it

* when you want more stable access
* when you need account-bound access behavior
* when crawler is failing for too many requests limitations

### Important

* it's recommended to use your own account cookies with every run
* This is required when deep crawl is enabled otherwise the actor will return normal data
* Keep this value secret
* Do not expose it in logs or screenshots
* Invalid or expired cookies may cause blocked responses anyway
* If the cookie session is stale, refresh it before a run
* you can view a [YouTube Tutorial](https://www.youtube.com/watch?v=BY3KH4j2nhA) on how to extract your account cookies

### Format example

```json
{
  "loid": "your_loid_cookie_value",
  "reddit_session": "your_reddit_session_cookie_value"
}
```

---

## Deep crawl for comments

**Type:** boolean
**Default:** false

This enables deeper comment crawling for post URLs.

### What it does

When enabled, the Actor tries to collect the full comment section for post links.

### Important limitations

* Requires Reddit logged-in and valid Cookies (loid, reddit_session)
* This setting applies to **post URLs** only not for feeds
* Feed URLs usually do not return deep comments in the same way
* Very large threads can still be constrained by Reddit-side behavior and rate limits
* Comment expansion can be slower than post-only crawling

### Recommended use

Enable this when:

* you need full discussion context
* you are analyzing conversations
* you need comment trees for research or NLP tasks
* you want deeper thread reconstruction from post URLs

Disable this when:

* you only want posts
* you want faster runs
* you are doing broad feed scraping

### Practical meaning

* `false` means quicker post collection
* `true` means more detailed extraction and more processing per post link

---

## Include comments

**Type:** boolean
**Default:** true

This controls whether comments are included in the output for post URLs.

### Behavior

* `true` → the Actor returns max of first ~75 comments with each post link
* `false` → the Actor returns post data only without any comments

### Important note

Comments are not available for feed-style crawling in the same way as for post URLs. This is a content-source limitation rather than a UI limitation.

### Recommended use

* Enable it for single post scraping
* Disable it for feed-based bulk scraping when you only want post metadata from a large set of posts links
* Keep it enabled when comment analysis matters

### Practical meaning

* `includeComments = true` for post pages with max of 75 comments
* `includeComments = false` for lighter datasets and faster runs

---

## Keyword filters

**Type:** array
**Editor:** `stringList`
**Optional:** yes

This lets you filter posts by one or more keywords or phrases.

### Examples

* `bitcoin`
* `climate change`
* `data breach`
* `reddit`
* `hot dog`

### How it works

The Actor keeps only posts that match at least one keyword, depending on your implementation.

### Best practices

* Use short and specific keyword lists
* Use phrases when you need tighter matching
* Keep the keyword list focused to reduce noisy results
* Combine keywords with stop dates for better dataset relevance

### When to use it

* topic monitoring
* brand tracking
* niche content collection
* research around specific phrases or events
* reducing unnecessary output from broad sources

### Notes

* Case-Sensitive so take care when using it
* Empty keyword lists disable keyword filtering
* Phrase matching is often better than single generic terms

---

## Filter fields

**Type:** array
**Editor:** `select`
**Optional:** yes

This option removes posts that are missing selected fields.

### How it works

If you select a field, any post missing that field will be dropped.

Example:

* selecting `title` and `body` keeps only posts that have both fields populated

### Good use cases

* only keep complete posts
* remove sparse or partial records
* ensure data quality before export
* avoid empty or low-value results

### Examples

* `title`
* `body`
* `comments`
* `found_media`
* `score`
* `upvote_ratio`

### Important

This is a strict “must contain all selected fields” filter.

### Practical meaning

* Select nothing to keep all posts
* Select one field to require that field
* Select multiple fields to require all selected fields

---

## Stop date

**Type:** string
**Editor:** `datepicker`
**Optional:** yes

This stops the actor from returning older posts than the selected date

### How it behaves

* Only posts published on or after the selected date are collected
* Older posts are skipped
* Leave it empty to crawl without a date limit

### When to use it

* daily monitoring
* recent content collection
* archive reduction
* date-bounded research
* trend snapshots for a specific period

### Example

If you choose `2026-06-01`, the Actor will keep only posts from `2026-06-01` and newer.

### Notes

* Dates are UTC-based
* This is very useful when scraping active subreddits with large histories

---

## Include crossposts

**Type:** boolean
**Default:** true

This controls whether crossposted Reddit posts are included in the output.

### Behavior

* `true` → crossposts are included
* `false` → crossposts are skipped

### When to disable it

* when you want only original posts
* when crossposts add noise to your dataset
* when you want cleaner topic analysis
* when you want to remove repeated content

### When to enable it

* when you want broader coverage
* when reposted content matters
* when you want to track how content spreads across communities

---

## Proxy configuration

**Type:** object
**Editor:** `proxy`
**Optional:** yes

This controls whether the Actor uses Apify Proxy or a custom proxy setup.

### Recommended use

Use proxies when:

* Reddit blocks requests
* you see empty or partial results
* you are running larger jobs

### When not to use proxies

* very small test runs
* cases where direct access already works reliably
* if everything is working fine without them

### Notes

* Apify Proxy can help with stability
* Bad proxy settings can reduce reliability
* If requests fail or return blocks, proxies are one of the first things to try

---

## Example input

```json
{
  "links": [
    {
      "url": "https://www.reddit.com/r/mildlyinfuriating/"
    },
    {
      "url": "https://www.reddit.com/r/mildlyinfuriating/comments/1txskkj/resurant_charges_extra_to_take_toppings_off/"
    }
  ],
  "maxPosts": 100,
  "deepCrawl": false,
  "includeComments": true,
  "includeCrossposts": false,
  "keywords": ["Reddit", "news", "work"],
  "filterFields": ["title", "body", "comments"],
  "stopDate": null,
  "proxyConfiguration": {
    "useApifyProxy": false
  }
}
```

---

## Output fields

The Actor returns structured Reddit post objects. The table below explains each field.

## Top-level post fields

| Field                      | Type    | Description                                   |
|----------------------------|---------|-----------------------------------------------|
| `thumbnail`                | string  | Thumbnail URL for the post, if available      |
| `post_id`                  | string  | Reddit post ID, usually in `t3_...` format    |
| `crosspost_parent`         | string  | Parent post reference for crossposts          |
| `publisher_id`             | string  | Reddit author ID                              |
| `subreddit_id`             | string  | Subreddit ID                                  |
| `type`                     | string  | Post type such as image, video, link, or self |
| `subreddit_type`           | string  | Subreddit visibility type such as public      |
| `title`                    | string  | Post title                                    |
| `post_flair`               | string  | Post flair text                               |
| `publisher`                | string  | Username of the post author                   |
| `subreddit`                | string  | Subreddit name prefixed with `r/`             |
| `published_at`             | string  | UTC publication timestamp                     |
| `body`                     | string  | Post body text for self posts                 |
| `score`                    | integer | Post score                                    |
| `upvote_ratio`             | float   | Upvote ratio                                  |
| `upvotes`                  | integer | Upvotes                                       |
| `downvotes`                | integer | Downvotes                                     |
| `total_awards`             | integer | Number of awards received                     |
| `total_crossposts`         | integer | Crosspost count                               |
| `total_comments`           | integer | Comment count                                 |
| `total_subreddit_subs`     | integer | Subreddit subscriber count                    |
| `is_hidden`                | boolean | Whether the post is hidden                    |
| `is_crosspost`             | boolean | Whether the post is a crosspost               |
| `is_pinned`                | boolean | Whether the post is pinned                    |
| `is_author_premium`        | boolean | Whether the author has premium status         |
| `is_edited`                | boolean | Whether the post was edited                   |
| `can_gild`                 | boolean | Whether the post can be gilded                |
| `is_comments_still_active` | boolean | Whether comments are still open               |
| `is_score_hidden`          | boolean | Whether the score is hidden                   |
| `is_over_18`               | boolean | NSFW flag                                     |
| `is_locked`                | boolean | Whether the post is locked                    |
| `is_spoiler`               | boolean | Whether the post is marked as spoiler         |
| `is_gallery`               | boolean | Whether the post is a gallery post            |
| `is_video`                 | boolean | Whether the post contains video content       |
| `is_original_content`      | boolean | Whether the post is marked OC                 |
| `is_crosspostable`         | boolean | Whether the post can be crossposted           |
| `is_removed`               | object  | Removal or moderation metadata                |
| `link`                     | string  | Reddit permalink to the post                  |
| `found_media`              | array   | Extracted media URLs found in the post        |
| `comments`                 | array   | Extracted comment objects                     |

---

## Comment fields

| Field                | Type            | Description                                        |
|----------------------|-----------------|----------------------------------------------------|
| `author`             | string          | Comment author username                            |
| `author_id`          | string          | Comment author ID                                  |
| `parent_id`          | string          | Parent comment or post ID                          |
| `comment_id`         | string          | Reddit comment ID, usually in `t1_...` format      |
| `link_id`            | string          | Reddit post ID this comment belongs to             |
| `subreddit_id`       | string          | Subreddit ID                                       |
| `subreddit`          | string          | Subreddit name prefixed with `r/`                  |
| `score`              | integer         | Comment score                                      |
| `upvotes`            | integer         | Upvotes                                            |
| `downvotes`          | integer         | Downvotes                                          |
| `upvotes_ratio`      | integer or null | Upvote ratio when available                        |
| `type`               | string or null  | Comment type when available                        |
| `body`               | string          | Comment text                                       |
| `link`               | string          | Reddit permalink to the comment                    |
| `unrepliable_reason` | string or null  | Reason replies may be restricted                   |
| `can_send_replies`   | boolean         | Whether replies can be sent                        |
| `is_post_comment`    | boolean         | Whether this comment is a top-level post comment   |
| `is_reply`           | boolean         | Whether this comment is a reply to another comment |
| `is_score_hidden`    | boolean         | Whether score is hidden                            |
| `is_over_18`         | boolean or null | NSFW flag when present                             |
| `is_edited`          | boolean         | Whether the comment was edited                     |
| `is_author_blocked`  | boolean         | Whether the author is blocked                      |
| `published_at`       | string          | UTC timestamp for the comment                      |

---

## Example output

```json
{
  "thumbnail": "https://preview.redd.it/example.jpg",
  "post_id": "t3_1txskkj",
  "crosspost_parent": null,
  "publisher_id": "t2_ohi0a18u",
  "subreddit_id": "t5_2ubgg",
  "type": "image",
  "subreddit_type": "public",
  "title": "Restaurant charges extra to take toppings off",
  "post_flair": "I just wanted a hot dog",
  "publisher": "Own_Gear1920",
  "subreddit": "r/mildlyinfuriating",
  "published_at": "2026-06-05T18:04:26+00:00",
  "body": null,
  "score": 20487,
  "upvote_ratio": 0.95,
  "upvotes": 20487,
  "downvotes": 0,
  "total_awards": 0,
  "total_crossposts": 3,
  "total_comments": 1500,
  "total_subreddit_subs": 12173839,
  "is_hidden": false,
  "is_crosspost": false,
  "is_pinned": false,
  "is_author_premium": false,
  "is_edited": false,
  "can_gild": false,
  "is_comments_still_active": true,
  "is_score_hidden": false,
  "is_over_18": false,
  "is_locked": false,
  "is_spoiler": false,
  "is_gallery": false,
  "is_video": false,
  "is_original_content": false,
  "is_crosspostable": true,
  "is_removed": {
    "num_reports": null,
    "removed_by": null,
    "reason": null,
    "is_publisher_blocked": false,
    "mod_reason": null
  },
  "link": "https://www.reddit.com/r/mildlyinfuriating/comments/1txskkj/resurant_charges_extra_to_take_toppings_off/",
  "found_media": [
    "https://i.redd.it/1f6m15ps7i5h1.jpeg"
  ],
  "comments": [
    {
      "author": "FormalWare",
      "author_id": "t2_d2pa5",
      "parent_id": "t3_1txskkj",
      "comment_id": "t1_opy6amm",
      "link_id": "t3_1txskkj",
      "subreddit_id": "t5_2ubgg",
      "subreddit": "r/mildlyinfuriating",
      "score": 2735,
      "upvotes": 2735,
      "downvotes": 0,
      "upvotes_ratio": null,
      "type": null,
      "body": "\"None\"? That'll be nine cents, fancypants.",
      "link": "https://www.reddit.com/r/mildlyinfuriating/comments/1txskkj/resurant_charges_extra_to_take_toppings_off/opy6amm/",
      "unrepliable_reason": null,
      "can_send_replies": true,
      "is_post_comment": true,
      "is_reply": false,
      "is_score_hidden": false,
      "is_over_18": null,
      "is_edited": false,
      "is_author_blocked": false,
      "published_at": "2026-06-05T18:13:22+00:00"
    }
  ]
}
```

---

## Tips for scraping Reddit

* Use keyword filtering to focus on relevant posts
* Enable deep crawling only when you need full comment trees
* Start with a small `maxPosts` value first
* Use `filterFields` to reduce noisy or incomplete records
* Use cookies and proxies if you encounter rate limits or empty responses
* Use post URLs when you need comments, not only feed URLs
* Combine subreddit URLs with search URLs for broader coverage

---

## Cost considerations

Apify includes free usage credits on the Free plan, and the final cost depends on:

* number of posts scraped
* comment depth
* amount of media extracted
* proxy usage
* run duration

For lighter scraping tasks, this Actor can be used efficiently with small batches of URLs. For larger monitoring or archival jobs, a paid Apify plan is recommended.

---

## Is it legal to scrape Reddit?

Scraping publicly available data may be legal, but you should always review the website’s terms of service and applicable laws before collecting data at scale.

Personal data may be protected by GDPR and other privacy regulations. Do not scrape personal data unless you have a legitimate reason to do so.

If you are unsure, consult a lawyer.

We also recommend reading Apify’s article: [Is web scraping legal?](https://blog.apify.com/is-web-scraping-legal/)

---

## Contact

If you have suggestions, bug reports, or feature requests, feel free to open an issue or contact the author through [GitHub](https://github.com/G-Glitch404).

---

## More scrapers

* [The Ultimate News Scraper](https://apify.com/glitch_404/ultimate-news-scraper)
* [Investing.com Scraper](https://apify.com/glitch_404/investing-scraper)
