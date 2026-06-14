# The Ultimate Reddit Scraper

Scrape Reddit subreddits, posts, feeds, and full comment trees with flexible filters, media extraction, and structured output.

## What does The Ultimate Reddit Scraper do?

**The Ultimate Reddit Scraper** is a high-performance Apify Actor for crawling Reddit content from public JSON endpoints. It can extract subreddit feeds, individual post threads, user activity pages, and custom Reddit feeds, while also collecting nested comments, media links, and rich post metadata.

It is designed for fast structured extraction and for building datasets you can use in analytics, monitoring, research, archiving, NLP, or automation workflows.

### The Ultimate Reddit Scraper can scrape:

- Subreddit feeds and community posts
- Individual post threads
- User pages and profile-related content
- Custom feed URLs
- Full comment trees with nested replies
- Media links, preview images, and gallery images
- Post metadata such as score, awards, upvotes, and flags

---

## Why scrape Reddit?

Reddit is one of the largest discussion platforms on the internet and a valuable source of real-world conversations, opinions, trends, and media. It is useful for tracking what people are saying, what content is gaining traction, and how topics evolve over time.

Here are just some of the ways you could use Reddit data:

- Sentiment analysis and brand monitoring
- Trend detection and topic research
- Market intelligence and competitive analysis
- Academic research on communities and behavior
- Archiving discussions and public conversations
- Training datasets for NLP and machine learning
- Monitoring public reaction to events or products

If you would like more inspiration on how scraping Reddit could help your business or organization, check out the [Apify industry pages](https://apify.com/industries).

---

## Features

### Start from multiple Reddit sources
You can provide different kinds of Reddit URLs as input:

- subreddit URLs
- post URLs
- user URLs
- custom feed URLs

### Deep comment crawling
Enable deep comment crawling to extract complete comment trees, including nested replies and hidden batches loaded from Reddit JSON endpoints.

### Keyword filtering
Filter posts by one or more keywords or phrases.

Examples:

- `bitcoin`
- `climate change`
- `"data breach"`

### Crosspost handling
Choose whether crossposts should be included in the output or filtered out.

### Field-based filtering
Return only posts that contain the fields you care about.

### Media extraction
Collect image URLs, gallery images, preview links, and video-related URLs when available.

### Structured output
The Actor returns clean structured Reddit items that can be used directly in:

- datasets
- spreadsheets
- databases
- APIs
- downstream analysis pipelines

---

## How to scrape Reddit

It is easy to use **The Ultimate Reddit Scraper**.

1. Click on **Try for free**
2. Enter the Reddit URLs you want to scrape
3. Configure optional filters like keywords, comments, and field selection
4. Click on **Run**
5. Preview or download your data from the **Dataset** tab

---

## Input options

### Start URLs
Add one or more Reddit URLs to crawl.

Supported examples:

- `https://www.reddit.com/r/technology/`
- `https://www.reddit.com/r/technology/.json`
- `https://www.reddit.com/r/mildlyinfuriating/comments/1txskkj/resurant_charges_extra_to_take_toppings_off/`
- `https://www.reddit.com/user/someusername/`
- `https://www.reddit.com/r/all/`

### Maximum posts
Set the maximum number of Reddit posts the Actor should collect.

- Minimum: `10`
- Default: `10`
- Recommended for testing: small values first

### Cookies
Optional authenticated Reddit cookies can be provided if you want to crawl as a logged-in account.

Use this when you need:

- session-based access
- account-specific content
- more stable access in some cases

### Deep crawl for comments
Enable this to crawl full comment trees, including nested replies and hidden comment batches.

### Include comments
When enabled, comments are included for post URLs.

### Include crossposts
When enabled, crossposted posts are included in the output.

### Keyword filters
Add keywords or phrases to limit posts to relevant content.

### Filter fields
Drop posts missing selected fields.

### Stop date
Stop crawling once posts become older than the selected date.

### Proxy configuration
Choose whether to use Apify Proxy or a custom proxy setup.

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
  "deepCrawl": true,
  "includeComments": true,
  "includeCrossposts": true,
  "keywords": ["reddit", "news"],
  "filterFields": ["title", "body", "comments"],
  "stopDate": "2026-06-01",
  "proxyConfiguration": {
    "useApifyProxy": false
  }
}